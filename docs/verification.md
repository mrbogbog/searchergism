# Local verification — 2026-11-12

- `node --test tests/search.test.mjs`: passed; 4,843 records, average query approximately 1 ms on this machine (100-query sample, not a performance guarantee).
- `python3 -m unittest discover -s tests -p '*_test.py' -v`: 4 tests passed. Verified unique IDs, totals, exact original text/provenance for all 6,453 selected translation strings, normalization and deterministic regeneration.
- HTTP preview: root HTML, static JSON, modules, CSS, font and license resources served locally.
- Chrome headless rendered direct `?q=offering+potion`: 4 matches; Offering Potion ranked first, with visible highlights.
- A temporary same-origin browser harness passed: input search, direct URL, name ranking, highlights, source disclosure, no-match/reset, 60-record initial rendering and 120 after Show more, example search buttons, Escape and `/`, injection-shaped query, 390px layout without horizontal overflow, single-column narrow / two-column desktop layouts, local font availability, simulated fetch failure and retry.
- Corporate Chrome policy disallows remote debugging. Verification used ordinary headless DOM rendering instead, without modifying browser policy. Test harnesses, browser profiles and screenshots were temporary and removed.
- The reference copy's files were fingerprinted during verification and compared again at completion. No writes to the reference copy were made.

See README.md for the exact coverage boundaries. This is a static text index, not a live calculator or an exhaustive capture of every generated runtime message.
