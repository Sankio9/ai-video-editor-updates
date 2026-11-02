"""R2.0.6 — strict offline Project Panel inventory resolver for selective-ASR audio.

Consumes a recursive *local* Project Panel snapshot and creates a memory-only map
of original media file paths for requested four-digit source codes.  Deliberately
fail-closed on offline, duplicate or contradictory media codes. No Premiere writes.
Never resolves source identity from parent-folder numbers / reporter timecodes.
"""
from __future__ import annotations

import re
from pathlib import Path

CODE_RE = re.compile(r"(?<![0-9])([0-9]{4})(?![0-9])")
MAX_ITEMS = 50000
MAX_DEPTH = 50
SUPPORTED_MEDIA = frozenset((
    ".mp4", ".mov", ".mxf", ".avi", ".mkv", ".mts", ".m2ts",
    ".wav", ".mp3", ".m4a", ".aac", ".flac", ".wma",
))
BIN_TYPES = frozenset(("bin", "folder", "root"))
MEDIA_TYPES = frozenset(("media", "file", "clip", "footage", "source"))


def name_codes(value: str) -> set[str]:
    """Use only the leaf name. E.g. 2026_folder/CAM_9981_x.MOV -> 9981."""
    if not isinstance(value, str):
        return set()
    basename = re.split(r"[\\/]", value)[-1]
    return set(CODE_RE.findall(basename))


def _children(node):
    for key in ("children", "items"):
        value = node.get(key)
        if value is not None:
            if not isinstance(value, list):
                raise ValueError("Invalid Project Panel bin child list")
            return value
    return None


def resolve_project_panel(inventory, required_codes):
    """Return {four-digit code: local original media pathname} or raise.

    Expected schema:
      {"schema":"aive-r206-project-panel-v1","items":[
        {"type":"bin","name":"Interviews","children":[
          {"type":"media","name":"CAM_9981_a.mov",
           "mediaPath":"D:\\media\\CAM_9981_a.mov","offline":false}
        ]}
      ]}
    Project Panel exporter must use a *real Premiere media path*, not a path
    inferred from the Premiere display name. No paths are ever uploaded.
    """
    if not isinstance(inventory, dict) or inventory.get("schema") != "aive-r206-project-panel-v1":
        raise ValueError("Unknown Project Panel inventory format")
    roots = inventory.get("items")
    if not isinstance(roots, list):
        raise ValueError("Project Panel inventory must provide items")
    if not isinstance(required_codes, (list, set, tuple)) or not required_codes:
        raise ValueError("No required source codes")
    required = set(required_codes)
    if len(required) != len(required_codes):
        raise ValueError("Duplicate required source code")
    if any(not isinstance(code, str) or not re.fullmatch(r"[0-9]{4}", code) for code in required):
        raise ValueError("Invalid required source code")

    matches = {code: [] for code in required}
    issues = []
    scanned = 0
    seen_nodes = set()
    stack = [(r, 0, ()) for r in reversed(roots)]

    while stack:
        node, depth, bins = stack.pop()
        scanned += 1
        if scanned > MAX_ITEMS or depth > MAX_DEPTH:
            raise ValueError("Project Panel inventory depth/item limit")
        if not isinstance(node, dict):
            raise ValueError("Invalid Project Panel item")
        node_type = str(node.get("type", "")).lower().strip()
        name = node.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("Unnamed Project Panel item")
        node_id = node.get("nodeId")
        if node_id is not None:
            if not isinstance(node_id, str) or not node_id:
                raise ValueError("Invalid Project Panel nodeId")
            if node_id in seen_nodes:
                raise ValueError("Duplicate Project Panel nodeId")
            seen_nodes.add(node_id)
        children = _children(node)
        if children is not None or node_type in BIN_TYPES:
            if children is None:
                raise ValueError("Bin has no child list: " + name)
            for child in reversed(children):
                stack.append((child, depth + 1, bins + (name,)))
            continue
        if node_type not in MEDIA_TYPES:
            # Sequences, markers, nested sequences and graphics are not media.
            continue

        display_codes = name_codes(name)
        media_path = node.get("mediaPath")
        disk_codes = name_codes(media_path or "")
        touched = (display_codes | disk_codes) & required
        if not touched:
            continue
        if node.get("offline") is not False:
            issues.append(("OFFLINE_OR_UNKNOWN", sorted(touched), name))
            continue
        if not isinstance(media_path, str) or not media_path.strip():
            issues.append(("NO_REAL_MEDIA_PATH", sorted(touched), name))
            continue
        if len(display_codes) > 1 or len(disk_codes) > 1:
            issues.append(("AMBIGUOUS_MEDIA_FILENAME", sorted(touched), name))
            continue
        if display_codes and disk_codes and display_codes != disk_codes:
            issues.append(("CONTRADICTORY_SOURCE_CODES", sorted(touched), name))
            continue
        code = next(iter(touched))
        if code not in required:
            continue
        p = Path(media_path)
        if p.suffix.lower() not in SUPPORTED_MEDIA:
            issues.append(("UNSUPPORTED_MEDIA_TYPE", [code], name))
            continue
        if not p.is_file() or p.is_symlink():
            issues.append(("MEDIA_MISSING_OR_LINKED", [code], name))
            continue
        if p.stat().st_size < 1:
            issues.append(("EMPTY_SOURCE", [code], name))
            continue
        matches[code].append({"name": name, "path": str(p), "bins": bins})

    missing = sorted(code for code, files in matches.items() if not files)
    duplicates = sorted(code for code, files in matches.items() if len(files) > 1)
    if issues or missing or duplicates:
        # No confidential paths in exception messages; UI may colorize by codes.
        messages = []
        if missing:
            messages.append("MISSING_RED: " + ",".join(missing))
        if duplicates:
            messages.append("DUPLICATE_RED: " + ",".join(duplicates))
        if issues:
            messages.append("MEDIA_ISSUE_RED: " + ";".join(
                kind + ":" + ",".join(codes) for kind, codes, _ in issues[:20]))
        raise ValueError("Project Panel source integrity STOP — " + " | ".join(messages))
    return {code: files[0]["path"] for code, files in sorted(matches.items())}


def sources_for_rescan(request, inventory):
    if not isinstance(request, dict) or not isinstance(request.get("rescans"), list):
        raise ValueError("Invalid R206 rescan request")
    codes = [item.get("sourceCode") for item in request["rescans"] if isinstance(item, dict)]
    if not codes:
        raise ValueError("No R206 rescans")
    return resolve_project_panel(inventory, codes)
