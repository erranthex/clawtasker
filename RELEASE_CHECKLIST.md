# Release Checklist — ClawTasker CEO Console v1.5.0

## Pre-release

- [x] All source changes committed to `ui/src/modules/`
- [x] `ui/src/build-manifest.json` version updated to 1.5.0
- [x] `VERSION` file updated to 1.5.0
- [x] Build: `python3 scripts/build_ui.py 1.5.0`
- [x] Verify: `python3 scripts/verify_build.py` — 130/130 pass
- [x] CHANGELOG.md updated with v1.5.0 entry
- [x] README.md updated for v1.5.0
- [x] BILL_OF_MATERIALS.md updated
- [x] docs/AGENT_PROMPTS.md updated
- [x] Requirements audit: 10 REQs with full test case traceability

## Build verification

- [x] 109 functions in built output
- [x] 11 view containers present
- [x] 13 key constants declared before use
- [x] 18 key functions present
- [x] 14/14 portraits, 14/14 sprites, 23 textures, 56 vendor files
- [x] CSS sprite-avatar-frame + --sprite-url present
- [x] server.py WEB_DIR → ui/dist/
- [x] main.js bootstrap with DOMContentLoaded

## Package

- [x] `zip -r clawtasker_v1_5_0.zip .`
- [x] Standalone HTML: `ui/dist/index.html` testable in browser
- [x] Test report: `docs/TEST_REPORT_v1_5_0.md`

## GitHub release

- [ ] Create tag `v1.5.0`
- [ ] Upload `clawtasker_v1_5_0.zip` as release asset
- [ ] Copy CHANGELOG v1.5.0 section as release notes
