# Searchergism

An unofficial English Synergism text reference. Dependency-free static HTML, CSS, and JavaScript for GitHub Pages. No game execution, runtime scraping, API keys, package installation, or save upload. **All stages are visible: expect spoilers.**

## Preview

From the repository root:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open <http://localhost:8000>. Stop with Ctrl+C. Opening `index.html` directly via `file://` will not load the JSON/module files in most browsers. Searches update as you type; all words match in any order across names, descriptions, categories, and source keys. Exact name matches rank first. `/` focuses search and Escape clears it. `?q=offering+potion` links to a search. Results render in a single full-width column, 60 at a time; matching searches all records in the selected categories. Expand/collapse **Categories** and toggle any of the 19 categories, or use Select all / Select none. Selected categories are combined (OR), then narrowed by the text query (AND). Clear/Escape clears only the query; Reset all filters restores every category too. Category selections are included in shareable URLs using repeated `category` parameters. Source details remain in the JSON and audit log, but are no longer displayed on result cards.

## Publish to GitHub Pages

Publish the repository root using Pages (Deploy from a branch, `/ (root)`). No build step is needed. URLs are relative and work under a project subpath. `.nojekyll` keeps this a plain static site. Do not publish the local `source-reference/` directory; it is gitignored. No push or Pages configuration has been performed by this implementation.

## Maintain the data

`data/index.json` is the checked-in, editable source of truth. Each record has a stable `id`, `category`, `name`, plain `text`, a `dynamic` flag, and `sources` containing source file/key and original `raw` text. Update records directly when correcting wording or adding information. Original provenance makes the seed auditable. When manually adding/removing entries, update `meta.entries` and `meta.categories`; `meta` source hash/version and translation counts describe the original seed. The page derives visible totals from the current entries.

The seed uses local **Synergism 4.1.1** `translations/en.json` and untranslated visible text/tooltips from `index.html`. Names, descriptions, effects, challenge rules, and named modern registries are grouped where possible; other gameplay translation leaves remain individual records. Counts are **search records, not purchasable upgrade counts**. Coverage includes achievements, ants, resets, buildings, runes/talismans/blessings/spirits, research, challenges, corruptions, campaigns, cubes/platonic upgrades/hepteract forge, shop/quarks/golden quarks, octeracts, ambrosia variants, purple reactor, statistics, automation and gameplay help.

### Optional regeneration (Python 3.10+, standard library only)

The copied game repository is a **read-only reference** at `source-reference/SynergismOfficial`. Never edit it as part of site maintenance. The script reads it but does not execute game code or write to it.

```sh
# Print coverage without changing the editable index:
python3 scripts/extract.py

# Create a candidate for review rather than overwriting manual edits:
python3 scripts/extract.py --output data/candidate.json

# Explicitly replace the editable seed (overwrites hand edits):
python3 scripts/extract.py --write

# An alternative local copy can be provided with --source PATH.
```

Delete a candidate after comparing it. Keep new manual curation rather than blindly regenerating. Extraction is deterministic for the same reference; metadata includes the English file SHA-256 and version from `package.json`. The source copy need not be present to preview or publish the site.

### Upgrade-only curation — 2026-11-12

The live index now contains **1,184** upgrade/modifier records across **19** categories; **3,659** of the original 4,843 records were removed. It retains 2,653 original translation strings. The Static Game Help category and its three records were removed in a follow-up at user request; the complete session log reflects these decisions. **673** retained records contain dynamic parameters.

See [the complete session log](docs/index-curation-2026-11-12.md) for **every kept and removed record**, its original indexed text, category, source references and decision reason. The machine-readable decisions are in `data/curation-decisions.json`, with a hash of each reviewed text.

Kept: actual stat/yield/multiplier/exponent/cap/cost/free-level changes, challenge bonuses, and upgrades changing starting resources or preserving accumulated values. Variable magnitudes count. Removed: standalone labels, balances, current levels, output/progress reports, costs, instructions, flavor-only text, statistics-factor names, and unlock/automation-only records. A grouped description is retained unchanged if it contains a real modifying effect; accompanying flavor or unlock text may remain inside that record.

Regeneration now applies the explicit decisions by default, **not keyword heuristics**. New or changed text stops regeneration and requires review; existing removals cannot silently reappear. To inspect a fresh uncurated extraction, use `python3 scripts/extract.py --raw --output data/candidate.json`; raw output cannot overwrite the live index. `scripts/curation.py` applies the decisions and can generate the session audit. The original extraction coverage below describes the **pre-curation seed**, not the current searchable scope.

### Original extraction coverage and known gaps

- All **6,453** nonempty translation strings in 31 selected gameplay roots are preserved verbatim in provenance. These become **4,776** grouped translation records plus **67** static HTML records: **4,843** total across **30** categories. The page’s “What’s in this index?” panel and JSON metadata provide category counts.
- **1,379** records contain interpolation parameters. `⟨value⟩` means an unresolved in-game value, not zero or an estimated number. Current/next effects, costs, progress, conditional rewards, computed formulas and save-dependent unlocks are **not evaluated**. Both conditional text variants may appear together.
- Color markup and HTML tags are removed for reading; nested translation references are expanded, and `num:((…))` is kept as its literal number (without the game's locale/scientific formatting). Original markup is preserved under `sources[].raw`. Optional in-game stat-symbol decoration is not reproduced. Source text is rendered with DOM text nodes, not injected as HTML.
- The other **415** translation strings are deliberately excluded: account, save/import/export, settings, layout, tabs, mobile/platform messages, testing/calculation debug prompts, event messages, main boot notices, feedback and announcements. Excluded roots and counts are recorded in `meta.excludedTranslationRoots`.
- TypeScript is inspected for coverage but **not executed or parsed as a general-purpose text source**. Any prose assembled only in TypeScript, runtime-generated DOM, server-supplied events/store content, and platform-specific help can be absent. For example `src/UpdateVisuals.ts` constructs the “You have … Wow! …” cube-balance status in code; live balances are intentionally absent. The index is a broad static reference, not an exact simulation or claim to every possible runtime string.
- Broad coverage intentionally includes some UI labels and validation messages. Some fallback titles are humanized translation keys or numeric upgrade IDs rather than official names (the older upgrade/research registries do not always define names). Statistics and related help may overlap across systems. Only English is indexed.

## Verify

```sh
node --test tests/search.test.mjs
python3 -m unittest discover -s tests -p '*_test.py' -v
```

Node 18+ is sufficient for search unit tests. The eight Python tests check curated counts, every keep/remove decision and log entry, user examples, removed UI/unlocks, preserved real modifiers, and rejection of unreviewed new/changed text. With the local reference present they also verify complete raw extraction, unchanged retained provenance and deterministic curated regeneration; source-dependent checks skip when it is absent. If manually editing indexed text, review the matching decision/hash rather than bypassing the curation guard. Browser checks should cover initial load, multiword search, no matches, clear, load more, source disclosure, keyboard shortcuts, direct query URLs, failure/retry, and narrow screens.

## Files and styling

- `index.html`, `styles.css`, `app.js`: responsive, keyboard-accessible interface and safe text rendering.
- `search.mjs`: shared normalization, matching and name ranking.
- `data/index.json`: maintainable content and extraction report.
- `scripts/extract.py`, `tests/`: optional maintenance and regression checks.
- `assets/fonts/`: locally served Inconsolata Latin font and SIL Open Font License.
- `licenses/Synergism-MIT.txt`: upstream MIT notice for reproduced game content.

Styling is inspired by inspected `Synergism.css`: `#111` background, `#171717` panels, gold borders/accents, square controls and the game’s bundled Inconsolata. No third-party CDN or framework is used.

## Future ideas

- Formula and cost calculations, with explicit game-version compatibility.
- Spoiler gating by unlock state.
- Optional local-only save sync, without uploading saves.
- Era/stage and category quick filters.
- Further curation of fallback titles, cross-system duplicate grouping, and more languages.

## Attribution

Independent fan project; not an official Synergism site. Game content is © 2019–2025 Platonic and Khafra, under MIT. Inconsolata is © 2006 The Inconsolata Project Authors, under SIL OFL 1.1. Both license notices are included with the redistributed material.
