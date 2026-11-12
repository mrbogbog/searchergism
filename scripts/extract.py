#!/usr/bin/env python3
"""Seed the editable English index using only Python's standard library."""
import argparse
from collections import Counter
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    'ambrosia': 'Ambrosia', 'redAmbrosia': 'Red Ambrosia',
    'purpleAmbrosia': 'Purple Ambrosia', 'purpleReactor': 'Purple Reactor',
    'achievements': 'Achievements', 'reset': 'Resets', 'ants': 'Ants',
    'challenges': 'Challenges', 'cubes': 'Cube Upgrades', 'researches': 'Research',
    'shop': 'Quark Shop', 'singularity': 'Singularity & Golden Quarks',
    'upgrades': 'Upgrades', 'campaigns': 'Campaigns', 'corruptions': 'Corruptions',
    'footnotes': 'Gameplay Help', 'buildings': 'Buildings', 'octeract': 'Octeracts',
    'runes': 'Runes & Talismans', 'singularityChallenge': 'Singularity Challenges',
    'statistics': 'Statistics & Formulas', 'wowCubes': 'Cubes & Higher Dimensions',
    'dynamicUpgrades': 'Upgrade Help', 'hepteracts': 'Hepteracts',
    'offlineProgress': 'Offline Progress', 'fastForward': 'Offline Progress',
    'history': 'Reset History', 'toggles': 'Automation Help',
    'hotkeys': 'Gameplay Help', 'pseudoCoins': 'PseudoCoins', 'general': 'General Help'
}
PARALLEL = [
    ('descriptions', 'names', 'effects'),
    ('upgradeDescriptions', 'upgradeNames', 'upgradeEffects'),
    ('crystalUpgrades', None, 'crystalEffects'),
    ('constantUpgrades', None, 'constantEffects')
]


def humanize(value):
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', str(value)).replace('_', ' ').strip().capitalize()


def flatten(value, path):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flatten(child, path + [key])
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from flatten(child, path + [str(index)])
    elif isinstance(value, str) and value.strip():
        yield '.'.join(path), value


def lookup(data, key):
    value = data
    try:
        for part in key.split('.'):
            value = value[int(part)] if isinstance(value, list) else value[part]
        return value if isinstance(value, str) else None
    except (KeyError, IndexError, ValueError, TypeError):
        return None


def clean(text, translations, trail=()):
    def expand(match):
        key = match.group(1).strip()
        value = lookup(translations, key)
        if value is None or key in trail:
            return '[translation: ' + key + ']'
        return clean(value, translations, trail + (key,))
    text = re.sub(r'\$t\(([^()]+)\)', expand, text)
    for _ in range(8):
        new = re.sub(r'<<[^|<>]*\|([\s\S]*?)>>', r'\1', text)
        if new == text:
            break
        text = new
    text = re.sub(r'num:\(\((.*?)\)\)', r'\1', text)
    text = re.sub(r'<br\s*/?>|</(?:p|div|li)>', '\n', text, flags=re.I)
    text = re.sub(r'</?[A-Za-z][A-Za-z0-9]*(?:\s+[^<>]*?)?\s*/?>', '', text)
    text = re.sub(r'\{\{\s*-?\s*([^{}]+?)\s*\}\}', lambda m: '⟨' + m.group(1) + '⟩', text)
    return re.sub(r'[ \t]+', ' ', unescape(text)).strip()


class StaticHTML(HTMLParser):
    """Collect untranslated visible text and tooltip attributes, with provenance."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        blocked = tag in ('script', 'style', 'head', 'noscript') or any(x[1] for x in self.stack) or 'i18n' in attrs
        element = attrs.get('id') or (self.stack[-1][2] if self.stack else tag)
        if not blocked:
            for attr in ('title', 'aria-label'):
                if attrs.get(attr) and 'i18n-' + attr not in attrs:
                    self.items.append((self.getpos()[0], element, attrs[attr]))
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
            self.stack.append((tag, blocked, element))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        text = data.strip()
        if self.stack and not self.stack[-1][1] and len(text) >= 16 and re.search(r'[A-Za-z]{3}', text):
            self.items.append((self.getpos()[0], self.stack[-1][2], text))


def extract(source):
    raw = (source / 'translations/en.json').read_bytes()
    data = json.loads(raw)
    entries, consumed = [], set()

    def add(identifier, category, name, fields, file='translations/en.json'):
        fields = [(key, value) for key, value in fields if isinstance(value, str) and value.strip()]
        if not fields:
            return
        texts = []
        for key, value in fields:
            normalized = clean(value, data)
            if normalized and normalized not in texts:
                texts.append(normalized)
        entries.append({
            'id': identifier, 'category': category, 'name': clean(name, data),
            'text': '\n\n'.join(texts),
            'dynamic': any('{{' in value or '$t(' in value and '⟨' in clean(value, data) for _, value in fields),
            'sources': [{'file': file, 'key': key, 'raw': value} for key, value in fields]
        })
        if file == 'translations/en.json':
            consumed.update(key for key, _ in fields)

    def visit(node, path, category):
        if not isinstance(node, dict):
            return
        # Parallel maps are the older game's name/description/effect registries.
        for desc_key, name_key, effect_key in PARALLEL:
            descriptions = node.get(desc_key)
            if not isinstance(descriptions, dict):
                continue
            names = node.get(name_key, {}) if name_key else {}
            if desc_key == 'upgradeDescriptions' and not names:
                names = node.get('names', {})
            effects = node.get(effect_key, {})
            for key, description in descriptions.items():
                if not isinstance(description, str):
                    continue
                fields = [('.'.join(path + [desc_key, key]), description)]
                for field_key, mapping in [(name_key if node.get(name_key or '') else 'names', names), (effect_key, effects)]:
                    if isinstance(mapping, dict) and isinstance(mapping.get(key), str):
                        fields.append(('.'.join(path + [field_key, key]), mapping[key]))
                name = names.get(key) if isinstance(names, dict) else None
                fallback = humanize(key) if not key.isdigit() else humanize(path[0]) + ' #' + key
                if desc_key in ('crystalUpgrades', 'constantUpgrades'):
                    fallback = ('Crystal' if desc_key == 'crystalUpgrades' else 'Constant') + ' upgrade #' + key
                add('.'.join(path + [desc_key, key]), category, name or fallback, fields)
        # Modern registries hold a named object with related prose fields.
        if isinstance(node.get('name'), str) and any(k in node for k in ('description', 'effect', 'flavor', 'default', 'effects', 'reward', 'rewards')):
            fields = [(key, value) for key, value in flatten(node, path) if key not in consumed]
            add('.'.join(path), category, node.get('progressName', node['name']), fields)
        for key, value in node.items():
            visit(value, path + [key], category)

    for root, category in CATEGORIES.items():
        visit(data.get(root), [root], category)
        for key, value in flatten(data.get(root), [root]):
            if key not in consumed:
                add(key, category, ' · '.join(humanize(x) for x in key.split('.')[1:]), [(key, value)])

    parser = StaticHTML()
    parser.feed((source / 'index.html').read_text())
    seen = {entry['text'] for entry in entries}
    for ordinal, (line, element, value) in enumerate(parser.items):
        text = clean(value, data)
        if text in seen or len(text) < 16:
            continue
        seen.add(text)
        add('html.' + str(line) + '.' + element + '.' + str(ordinal), 'Static Game Help', humanize(element), [(f'line {line} #{element}', value)], 'index.html')

    entries.sort(key=lambda e: (e['category'], e['id']))
    counts = dict(sorted(Counter(e['category'] for e in entries).items()))
    all_leaves = dict(flatten(data, []))
    excluded = dict(sorted(Counter(k.split('.')[0] for k in all_leaves if k not in consumed).items()))
    report = {
        'translationSHA256': hashlib.sha256(raw).hexdigest(),
        'sourceVersion': json.loads((source / 'package.json').read_text()).get('version'),
        'entries': len(entries), 'categories': counts,
        'translationStringsIncluded': len(consumed),
        'translationStringsTotal': len(all_leaves),
        'excludedTranslationRoots': excluded,
        'dynamicEntries': sum(e['dynamic'] for e in entries),
        'notes': [
            'Counts are search records, not a count of purchasable upgrades.',
            'Named registries and parallel name/description/effect maps are grouped; other gameplay strings remain separate.',
            'All nonempty strings in the selected gameplay translation roots are included, including labels and validation help.',
            'Untranslated visible index.html text and tooltips supplement the translations.',
            'Runtime TypeScript expressions, player-state values, computed costs, generated DOM and platform-specific text are not evaluated.',
            'Angle brackets ⟨value⟩ mark unresolved game interpolation parameters; no game save is loaded.',
            'UI-only translation roots (account, save/import, settings, layout, platform, feedback and announcements) are excluded explicitly.'
        ]
    }
    return {'schemaVersion': 1, 'meta': report, 'entries': entries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'source-reference/SynergismOfficial')
    parser.add_argument('--write', action='store_true', help='Explicitly replace the editable data/index.json seed')
    parser.add_argument('--output', type=Path, help='Write a candidate elsewhere for comparison; does not overwrite the canonical index')
    parser.add_argument('--raw', action='store_true', help='Generate the uncurated extraction for review; requires --output')
    args = parser.parse_args()
    if args.write and args.output:
        parser.error('Choose --write or --output, not both')
    if args.raw and (args.write or not args.output):
        parser.error('--raw requires --output and cannot overwrite the curated index with --write')
    if args.raw and args.output.resolve() == (ROOT / 'data/index.json').resolve():
        parser.error('--raw cannot overwrite data/index.json')
    result = extract(args.source)
    if not args.raw:
        from curation import apply_curation
        result = apply_curation(result)
    print(json.dumps(result['meta'], ensure_ascii=False, indent=2))
    target = ROOT / 'data/index.json' if args.write else args.output
    if target:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    else:
        print('Dry run only. Use --write to replace the seed or --output PATH to compare a candidate.')


if __name__ == '__main__':
    main()
