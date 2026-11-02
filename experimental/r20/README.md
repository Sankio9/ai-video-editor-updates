# R2.0 — Experimental graphics safety gate

**Status:** LOCAL candidate only. These files are not present in any stable GitHub Release, CEP extension, or automated updater payload. Do not install as production.

- `cep/jsx/r20_graphics_guard.jsx`: ES3-friendly preflight-only helper, validating independent script preview plans, track mapping (V3/V4/V5), timing, per-block separators, existing clip inventory and overlap. It **never writes** to the timeline.
- `tests/guard.test.js`: deterministic mock tests, run with `node experimental/r20/tests/guard.test.js`.
- DO NOT call the guard on arbitrary project files without parsing and validating their origin.
- Current gate intentionally rejects V5 whenever ANY existing item is present, even when outside the planned insertion range. It reports exactly two choices, but does NOT implement destructive overwrite. Requires explicit opt-in + safe backup/restore implementation and Premiere validation.
- `sequenceId` and `clips` in the snapshot must be supplied by the actual CEP ExtendScript integration; a mock is not authoritative.
- `checkPlan` does not parse DOCX and cannot verify exact script fidelity. Unicode tests cover safe preservation of JS strings only; real MOGRT parameter readback remains necessary.
- Not yet implemented: real CEP toggle wiring, per-module DOCX extract, MOGRT import/set/readback, transaction-safe insertion+rollback, ownership ledger, timeline frame-rate quantization, SHA-256 compatibility with installed baseline, API integration tests.

**Blocker:** R2.0 lab files (`r20_independent_plans.py` and CEP JSX clone) were generated in a previous chat container and are not accessible here; the public updates repo does not contain the stable CEP application source. Avoid reconstructing approved modules from speculative assumptions.

**Test and release policy:** stable remains v1.9.13 until P0 live Premiere tests pass. Do NOT edit `release/next.json` or merge this branch. VO module 05 stays HOLD.
