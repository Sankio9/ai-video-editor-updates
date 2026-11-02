# R2.0.2 — Beta channel integration (development checkpoint)

**Decision (2026-10-27):** Do not use one-off .cmd launchers for every R2 update. The existing installed updater checks `/releases/latest` (stable only); GitHub excludes the experimental R2.0.x prereleases from that endpoint. R2.0 is **functional in tests but not stable for production**.

### Tested isolated implementation
A source-only local prototype was created with:
- `updater/beta.py`: opt-in GitHub prerelease discovery (only official `Sankio9/ai-video-editor-updates` repository and `v2.x.y` releases), next incremental version, canonical release URL, size and SHA-256.
- `cep/aive_updater_beta.js`: visible Stable/Beta selector within updater section, Stable by default. Beta verifies/downloads from Premiere using the same stable `runner.prepare()`, leaving the stable client untouched.
- `cep/index.html`: one additional script tag.
- `tests/test_beta.py`: six local tests PASS including chronological beta checks, stable isolation and malformed digests/URLs.
- JavaScript syntax and Python syntax PASS. Draft SHA-256: beta.py `1724ebad22568dd0ad018a3a226ea4360ac2e403ef6c6352169c84bac84a5a8d`; beta JS `dc2ec23af66dd3195755a70f0c9b14a54dbf14b1b881848c2526a4dcbbb33eb1`; candidate index `81a976fd8393294dd7f2d57ab69ea04ab2d675a936ddfefa6c50fafd3ec05f82`.

**NOT RELEASED.** Before deployment, review actual code and complete deterministic SHA-pinned packaging, real updater preflight in both CEP roots, rollback tests, Windows startup and Premiere UI tests. Keep stable v1.9.13 as latest; never relabel R2 as stable merely to make the updater offer it.

**Migration:** the installed R2.0 updater cannot fetch a beta until beta support is first bootstrapped. One final controlled bridge is technically required; subsequent R2 updates must run in-app, with no manual ZIP or CMD.
