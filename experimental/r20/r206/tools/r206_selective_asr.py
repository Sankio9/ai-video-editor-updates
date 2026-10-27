"""R2.0.6 candidate: fail-closed, read-only selective-ASR recovery planner.

Consumes R1.9.13 last_match_diagnostic.json locally. Emits *requests*, never
cut timestamps, never an ASR match, and never audio/transcript/private text.
Exact source codes and CUT ids are only written to a local output JSON.
No whisper/GPU side effects: executor integration requires separate validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

SCHEMA_IN = "aive-match-diagnostic-v1"
SCHEMA_OUT = "aive-r206-asr-rescan-request-v1"
RESCAN_STATUSES = frozenset((
    "REVIEW_WEAK_BOUNDARY", "REVIEW_WEAK_TRANSCRIPT",
    "REVIEW_NO_MATCH", "REVIEW_INVALID_BOUNDS",
    "REVIEW_ALTERNATIVE_OCCURRENCE", "REVIEW_OUTSIDE_SEARCH_RADIUS",
))
WHOLE_SOURCE_STATUSES = frozenset((
    "REVIEW_WEAK_TRANSCRIPT", "REVIEW_NO_MATCH",
    "REVIEW_ALTERNATIVE_OCCURRENCE",
))
MAX_FULL_SOURCE_SECONDS = 480.0
WINDOW_PAD_SECONDS = 20.0
MAX_SOURCE_DURATION_SECONDS = 86400.0
MAX_DIAGNOSTIC_BYTES = 8 * 1024 * 1024


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def clamp_seconds(a, b, length):
    if not finite(a) or not finite(b):
        raise ValueError("Invalid source time")
    start = max(0.0, min(length, float(a)))
    end = max(0.0, min(length, float(b)))
    if end - start < 0.25:
        raise ValueError("Empty ASR window")
    return round(start, 3), round(end, 3)


def candidate(event, duration):
    """One conservative ASR region per event; not a montage IN/OUT."""
    asr = event["asr"]
    status = asr["matchStatus"]
    have_tc = finite(event.get("scriptIn")) or finite(event.get("scriptOut"))
    if status in WHOLE_SOURCE_STATUSES or not have_tc:
        if duration <= MAX_FULL_SOURCE_SECONDS:
            return (0.0, round(duration, 3), "FULL_SOURCE", "LOW_CONFIDENCE_ASR")
        return None

    start = asr.get("rawMatchedIn")
    end = asr.get("rawMatchedOut")
    if finite(start) and finite(end) and 0 <= start < end <= duration:
        return (*clamp_seconds(start - WINDOW_PAD_SECONDS, end + WINDOW_PAD_SECONDS, duration),
                "AROUND_ASR_CANDIDATE", "BOUNDARY_AUDIT")

    # Reporter TC may guide *search* only; never a final montage decision.
    tc_a, tc_b = event.get("scriptIn"), event.get("scriptOut")
    if finite(tc_a) and finite(tc_b) and 0 <= tc_a < tc_b:
        return (*clamp_seconds(tc_a - 90, tc_b + 90, duration),
                "REPORTER_TC_SEARCH_HINT", "NO_SAFE_ASR_ANCHOR")
    if duration <= MAX_FULL_SOURCE_SECONDS:
        return (0.0, round(duration, 3), "FULL_SOURCE", "NO_SAFE_ASR_ANCHOR")
    return None


def merge(windows, max_gap=3.0):
    """Merge overlapping/neighbouring recovery windows of ONE source."""
    if not windows:
        return []
    ordered = sorted(windows, key=lambda x: (x["startSeconds"], x["endSeconds"]))
    merged = []
    for window in ordered:
        if (merged and window["startSeconds"] <= merged[-1]["endSeconds"] + max_gap):
            prev = merged[-1]
            prev["endSeconds"] = max(prev["endSeconds"], window["endSeconds"])
            prev["cutIds"] = sorted(set(prev["cutIds"] + window["cutIds"]))
            prev["reasons"] = sorted(set(prev["reasons"] + window["reasons"]))
            prev["methods"] = sorted(set(prev["methods"] + window["methods"]))
        else:
            merged.append({
                "startSeconds": window["startSeconds"],
                "endSeconds": window["endSeconds"],
                "cutIds": sorted(set(window["cutIds"])),
                "reasons": sorted(set(window["reasons"])),
                "methods": sorted(set(window["methods"])),
            })
    return merged


def build(diagnostic):
    if not isinstance(diagnostic, dict) or diagnostic.get("schema") != SCHEMA_IN:
        raise ValueError("Unsupported diagnostic schema")
    events = diagnostic.get("events")
    if not isinstance(events, list) or not 0 < len(events) <= 2000:
        raise ValueError("Invalid event count")
    per_source = defaultdict(list)
    known_ids, lengths, observed = set(), {}, defaultdict(list)
    for e in events:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise ValueError("Invalid event")
        if e["id"] in known_ids:
            raise ValueError("Duplicate CUT id")
        known_ids.add(e["id"])
        code = e.get("sourceCode")
        if not isinstance(code, str) or not code.isdigit() or len(code) != 4:
            raise ValueError("Invalid source code")
        a = e.get("asr")
        if not isinstance(a, dict):
            raise ValueError("ASR diagnostic missing")
        duration = a.get("sourceDuration")
        if not finite(duration) or not .25 <= duration <= MAX_SOURCE_DURATION_SECONDS:
            raise ValueError("Untrusted source duration: " + code)
        if code in lengths and abs(lengths[code] - duration) > .25:
            raise ValueError("Conflicting durations for source " + code)
        lengths[code] = float(duration)
        status = a.get("matchStatus") or "UNKNOWN"
        if not isinstance(status, str):
            raise ValueError("Invalid match status")
        observed[status].append(e["id"])
        if status not in RESCAN_STATUSES:
            continue
        per_source[code].append(e)

    sources,blocked = [],[]
    for code, affected in sorted(per_source.items()):
        duration = lengths[code]
        windows, rejected = [], []
        for e in affected:
            suggested = candidate(e, duration)
            if suggested is None:
                rejected.append(e["id"])
                continue
            start, end, method, reason = suggested
            windows.append({"startSeconds": start, "endSeconds": end,
                            "cutIds": [e["id"]], "reasons": [reason],
                            "methods": [method]})
        if rejected:
            blocked.append({"sourceCode": code, "cutIds": sorted(rejected),
                            "reason": "SOURCE_TOO_LONG_OR_NO_TRUSTWORTHY_ANCHOR",
                            "requiredAction": "EDITORIAL_SOURCE_REVIEW"})
        if windows:
            combined=merge(windows)
            sources.append({
                "sourceCode": code, "sourceDurationSeconds": round(duration, 3),
                "priority": "HIGH" if any(e["asr"]["matchStatus"] in
                    ("REVIEW_NO_MATCH", "REVIEW_WEAK_TRANSCRIPT") for e in affected)
                    else "NORMAL",
                "windows": combined,
                "windowSecondsTotal": round(sum(x["endSeconds"]-x["startSeconds"]
                                                for x in combined), 3),
            })
    return {
        "schema": SCHEMA_OUT, "action": "REQUEST_SELECTIVE_RETRANSCRIPTION_ONLY",
        "safeToModifyPremiereTimeline": False, "automaticCuttingAllowed": False,
        "reporterTimecodeUsedForCutting": False,
        "requiresNewASRAndEditorialValidation": True,
        "maxFullSourceSeconds": MAX_FULL_SOURCE_SECONDS,
        "rescans": sources, "blocked": blocked,
        "summary": {
            "totalEvents": len(events), "flaggedEvents": sum(len(v) for v in per_source.values()),
            "skippedSuggestedForAudit": len(events)-sum(len(v) for v in per_source.values()),
            "rescanSources": len(sources), "blockedSources": len(blocked),
            "statusCounts": {k:len(v) for k,v in sorted(observed.items())},
        },
    }


def run(input_path, output_path):
    input_path, output_path = Path(input_path), Path(output_path)
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Output cannot overwrite original diagnostic")
    if not input_path.is_file() or input_path.stat().st_size > MAX_DIAGNOSTIC_BYTES:
        raise ValueError("Missing or oversized diagnostic")
    raw = input_path.read_bytes()
    result = build(json.loads(raw.decode("utf-8-sig")))
    result["sourceDiagnosticSHA256"] = hashlib.sha256(raw).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_name(output_path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(output_path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return result


def main():
    cli = argparse.ArgumentParser(description="READ-ONLY R2.0.6 ASR rescue planning")
    cli.add_argument("--diagnostic", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    a=cli.parse_args()
    result=run(a.diagnostic,a.output)
    print(json.dumps({"ok":True, "flagged":result["summary"]["flaggedEvents"],
                      "sources":result["summary"]["rescanSources"],
                      "blocked":result["summary"]["blockedSources"],
                      "autoCut":False}, ensure_ascii=False))

if __name__ == "__main__":
    main()
