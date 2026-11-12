"""Apply explicit reviewed decisions; never infer upgrade semantics from keywords."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / 'data/curation-decisions.json'


def apply_curation(seed):
    review = json.loads(DECISIONS.read_text())
    decisions = {row['id']: row for row in review['decisions']}
    if len(decisions) != len(review['decisions']):
        raise ValueError('Duplicate curation decisions')
    result = deepcopy(seed)
    kept = []
    for entry in seed['entries']:
        decision = decisions.get(entry['id'])
        digest = hashlib.sha256(entry['text'].encode()).hexdigest()
        if decision is None or decision['textSHA256'] != digest:
            raise ValueError(f"Review required for new/changed text: {entry['id']}. Generate --raw --output candidate.json first.")
        if decision['keep']:
            kept.append(entry)
    meta = result['meta']
    meta['seedEntries'] = len(seed['entries'])
    meta['seedTranslationStringsIncluded'] = meta['translationStringsIncluded']
    meta['seedCategories'] = meta['categories']
    meta['seedDynamicEntries'] = meta['dynamicEntries']
    meta['entries'] = len(kept)
    meta['categories'] = dict(sorted(Counter(e['category'] for e in kept).items()))
    meta['translationStringsIncluded'] = sum(s['file'] == 'translations/en.json' for e in kept for s in e['sources'])
    meta['dynamicEntries'] = sum(e['dynamic'] for e in kept)
    meta['curation'] = {
        'date': review['date'], 'policy': 'Explicit value-modifying upgrades and rewards; no standalone labels, status, instructions, costs, or unlock-only text.',
        'kept': len(kept), 'removed': len(seed['entries']) - len(kept),
        'decisionsFile': 'data/curation-decisions.json',
        'sessionLog': 'docs/index-curation-2026-11-12.md'
    }
    meta['notes'] = [
        'Curated upgrade/modifier records, not a count of purchasable upgrades.',
        'Grouped descriptions are retained if at least one effect modifies a gameplay value; original grouped text is preserved.',
        'Raw extraction coverage is recorded under seedEntries, seedCategories and seedTranslationStringsIncluded.',
        'excludedTranslationRoots describes pre-curation extraction exclusions, not the curation removals.',
        'Standalone UI/status/instructions/costs and unlock-only records were removed through explicit reviewed decisions.',
        'Save-dependent values are not evaluated; angle brackets ⟨value⟩ mark unresolved interpolation parameters.'
    ]
    result['entries'] = kept
    return result


def write_session_log(seed, curated, path):
    """One-time audit: preserve every original record's text, name and provenance."""
    review = json.loads(DECISIONS.read_text())
    decisions = {row['id']: row for row in review['decisions']}
    lines = [
        '# Index curation session — 2026-11-12', '',
        f"Reviewed **{len(seed['entries']):,}** original records. **Kept {len(curated['entries']):,}; removed {len(seed['entries']) - len(curated['entries']):,}.**", '',
        '## Criteria', '',
        '- Keep an explicit upgrade/reward that modifies production, gains, costs, exponents, caps, effective/free levels, starting resources, or retention of accumulated progress.',
        '- Variable amounts count. A literal number is not required. A number by itself is not sufficient.',
        '- Remove standalone labels, balances, current levels, costs, output/progress reports, purchase prompts, instructions, lore, prerequisites, statistic-factor names, and unlock/automation-only messages.',
        '- Keep a grouped record if it contains a real modifier; do not rewrite or split its original text. This can preserve accompanying lore, unlocks, conditions and costs inside a real upgrade description.',
        '- Keep explicit numeric automation speed/cost improvements; remove merely enabling an autobuyer.',
        '- Keep positive challenge rewards; remove standalone challenge penalties and generic calculation explanations.',
        '- Decisions apply to this session’s input, not an automatic keyword policy for future text.', '',
        'The complete original normalized text is logged below for **every** kept and removed record. Source file/key references retain provenance; raw markup is recoverable from the read-only reference or raw extraction. `data/curation-decisions.json` stores each decision, reason and text SHA-256 for safe regeneration.', '',
        '## Category summary', '', '| Category | Kept | Removed |', '|---|---:|---:|'
    ]
    counts = Counter(e['category'] for e in curated['entries'])
    original = Counter(e['category'] for e in seed['entries'])
    for category, total in sorted(original.items()):
        lines.append(f'| {category} | {counts[category]} | {total-counts[category]} |')
    for keep, title in [(False, 'Removed'), (True, 'Kept')]:
        lines += ['', '## ' + title, '']
        for entry in seed['entries']:
            decision = decisions[entry['id']]
            if decision['keep'] != keep:
                continue
            lines += [f"### `{entry['id']}`", '', f"**Name:** {entry['name']}", '', f"**Category:** {entry['category']}", '', '**Decision:** ' + decision['reason'], '', '**Original indexed text:**', '', '````text', entry['text'], '````', '', '**Sources:**']
            for source in entry['sources']:
                lines.append(f"- `{source['file']}` → `{source['key']}`")
            lines += ['', '**Text SHA-256:** `' + decision['textSHA256'] + '`', '']
    path.write_text('\n'.join(lines) + '\n')
