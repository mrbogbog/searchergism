Resume building v1 of Searchergism on Alex’s machine.

Prerequisite: First verify Shell, ReadFile, and file-editing tools work. Previous attempts were blocked by invalid-JSON hooks (`post_to_aloc.sh` and `aicodemetricsd`). If still blocked, stop and report the exact error.

Paths:
- Site repo: /Users/agallien/git/searchergism
- Game source (read-only): /Users/agallien/git/SynergismOfficial
- Project context: /cursor/stores/self/docs/project-context.md
- Preferences: /cursor/stores/self/preferences.md

Instructions:
1. Inspect existing Searchergism work and preserve unrelated/uncommitted changes.
2. Scrape all available helper/upgrade-related text from SynergismOfficial, including upgrades, challenges, research, cubes/hepteracts, runes, quarks, shop, and similar systems.
3. Store the extracted content in an easily maintained static data file. Runtime scraping is not allowed; optionally include a regeneration script.
4. Build a dependency-free static HTML/CSS/JavaScript site suitable for GitHub Pages.
5. Add instant filter-as-you-type search across names, descriptions/helper text, and categories.
6. Style it like Synergism: dark UI, gold accents, and game-inspired typography based on inspected CSS/assets.
7. Add a brief README covering local preview and future ideas: formulas/cost calculations, spoiler gating, save sync, and era/stage filters.
8. Verify the site locally and check the extracted data/counts.
9. Do not push, open a PR, or modify SynergismOfficial. Leave the Searchergism working tree ready to preview.

Report:
- Counts by category
- Files created or changed
- How to preview locally
- Scrape gaps or dynamically generated text that could not be extracted
