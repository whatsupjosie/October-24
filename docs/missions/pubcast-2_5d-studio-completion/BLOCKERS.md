# Blockers and deferred work

- Browser runtime verification: no browser execution has yet been performed against this branch. **Not a claim that browser execution is impossible**; next action is to attempt it with available runtime or have owner verify. Do not mark passed.
- Full legacy Control Room integration: mapping and connections remain unverified. Next action: inspect existing station interfaces and backend routes, identify common command contract.
- Owner photographs and final set artwork: intentionally deferred; placeholder layers and configuration must remain replaceable.

Two-minute stall rule: record actual attempts/errors here; avoid repeated unchanged retries. Resolve entries when evidence changes.

## Current known limitations of shared switching
- Shared switcher controls 2.5D source selection through backend, but the browser renderer's pixels are not transported back into the server switcher's network video output. Must design and verify media ingest before calling remote multi-client broadcast complete.
- Registration of per-genre sources currently persists in CameraManager after a 2.5D production ends; cleanup must be safe for other active operators. Do not blindly reset global Program/Preview when stopping.
- Audio master and bus state now share the backend; media output from a DIFFERENT BROWSER PAGE is not automatically captured by the 2.5D local recorder. Cross-client audio ingest remains to be engineered and tested.
- Live browser and FastAPI verification remain unperformed. Local clone attempt blocked by DNS earlier; no executed pytest or Node test suite yet. Isolated source/module mock checks are documented separately.
