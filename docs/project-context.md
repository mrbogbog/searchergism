# Searchergism — project context

## Goal
A simple website that indexes Synergism upgrade/helper text and makes it searchable, for people playing the idle game Synergism.

## Repos (local)
- Game source: `/Users/agallien/git/SynergismOfficial`
- Site repo: `/Users/agallien/git/searchergism`

## Product decisions (v1)
- **Content scope:** All helper text found in the game (upgrades, challenges, research, cubes/hepteracts, runes, quarks, shop, and similar).
- **Data model:** Scrape from SynergismOfficial to seed; ship an easily maintainable list in searchergism source (not live scrape at runtime).
- **Search UX:** Instant filter-as-you-type. Category / era / unlock-stage quick filters are future work.
- **Visual style:** Dark Synergism UI — gold accents, font feel close to the game.
- **Hosting:** GitHub Pages (root of the Pages site for this repo).
- **Stack:** Static HTML + JavaScript only.

## Out of scope for v1 (potential later)
- Formulas and cost calculators
- Spoiler / unlock gating
- Offline save sync
- Era/stage and category quick filters (called out as interesting next)

## Status
Local build attempted; blocked by PreToolUse hooks on the self-hosted worker (`post_to_aloc.sh`, `aicodemetricsd` returning invalid JSON). Alex paused to try another approach. Restart prompt: [docs/resume-v1.md](resume-v1.md).

