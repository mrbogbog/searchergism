"""Verify extraction, explicit curation, complete session log and regeneration."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from curation import apply_curation
spec = importlib.util.spec_from_file_location('extract', ROOT / 'scripts/extract.py')
extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract)


class ExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/index.json').read_text())
        cls.review = json.loads((ROOT / 'data/curation-decisions.json').read_text())
        cls.decisions = {d['id']: d for d in cls.review['decisions']}
        cls.source_root = ROOT / 'source-reference/SynergismOfficial'
        cls.seed = extract.extract(cls.source_root) if cls.source_root.exists() else None

    def test_unique_ids_and_counts(self):
        entries = self.data['entries']
        self.assertEqual(len(entries), len({e['id'] for e in entries}))
        self.assertEqual(dict(Counter(e['category'] for e in entries)), self.data['meta']['categories'])
        self.assertEqual(len(entries), self.data['meta']['entries'])
        self.assertTrue(all(e['name'] and e['text'] and e['sources'] for e in entries))
        self.assertEqual(self.data['meta']['dynamicEntries'], sum(e['dynamic'] for e in entries))

    def test_complete_raw_extraction_and_curated_provenance(self):
        if self.seed is None:
            self.skipTest('Local reference needed for extraction provenance verification')
        source = json.loads((self.source_root / 'translations/en.json').read_text())
        expected = {k: v for root in extract.CATEGORIES for k, v in extract.flatten(source[root], [root])}
        found = {}
        for entry in self.seed['entries']:
            self.assertNotIn('<<', entry['text'])
            for original in entry['sources']:
                if original['file'] == 'translations/en.json':
                    self.assertNotIn(original['key'], found)
                    found[original['key']] = original['raw']
        self.assertEqual(expected, found)
        original_by_id = {e['id']: e for e in self.seed['entries']}
        for entry in self.data['entries']:
            self.assertEqual(original_by_id[entry['id']], entry)

    def test_cleaning(self):
        source = {'word': 'Cubes', 'loop': '$t(loop)'}
        self.assertEqual(extract.clean('<<gold|{{amount}}>> <b>$t(word)</b><br>num:((1e12))', source), '⟨amount⟩ Cubes\n1e12')
        self.assertIn('[translation: loop]', extract.clean('$t(loop)', source))
        self.assertEqual(extract.clean('&lt;img&gt;', source), '<img>')
        self.assertEqual(extract.clean('< LOCKED >', source), '< LOCKED >')

    def test_deterministic_curated_seed(self):
        if self.seed is None:
            self.skipTest('Local reference needed for regeneration verification')
        self.assertEqual(apply_curation(self.seed), self.data)

    def test_every_input_has_one_decision_and_log_entry(self):
        self.assertEqual(len(self.decisions), self.review['inputEntries'])
        self.assertEqual(len(self.review['decisions']), len(self.decisions))
        kept = {d['id'] for d in self.decisions.values() if d['keep']}
        self.assertEqual(kept, {e['id'] for e in self.data['entries']})
        log = (ROOT / 'docs/index-curation-2026-11-12.md').read_text()
        self.assertEqual(log.count('### `'), len(self.decisions))
        removed_section, kept_section = log.split('## Removed\n', 1)[1].split('## Kept\n', 1)
        for decision in self.decisions.values():
            section = kept_section if decision['keep'] else removed_section
            self.assertEqual(section.count('### `' + decision['id'] + '`\n'), 1)
        if self.seed:
            self.assertEqual(set(self.decisions), {e['id'] for e in self.seed['entries']})
            for entry in self.seed['entries']:
                self.assertIn(entry['text'].replace('\r\n', '\n').replace('\r', '\n'), log)
                self.assertEqual(hashlib.sha256(entry['text'].encode()).hexdigest(), self.decisions[entry['id']]['textSHA256'])

    def test_user_examples(self):
        for identifier in ['achievements.achievementLevelMobile', 'achievements.achievementRewards.137.experientiaAutobuy']:
            self.assertFalse(self.decisions[identifier]['keep'])
        for identifier in ['achievements.achievementRewards.13.multipliers', 'achievements.achievementRewards.160.multipliers']:
            self.assertTrue(self.decisions[identifier]['keep'])

    def test_obvious_ui_unlocks_removed_and_modifiers_preserved(self):
        kept = {e['id'] for e in self.data['entries']}
        for identifier in ['statistics.gameStage', 'statistics.ambrosiaGenerationStats.ShopUpgrade1', 'shop.upgradeDescriptions.shopTalisman', 'upgrades.descriptions.81', 'researches.descriptions.47', 'runes.EXPNeeded', 'ambrosia.edit.level', 'cubes.cubeMetadata.cost']:
            self.assertNotIn(identifier, kept)
        for identifier in ['upgrades.descriptions.107','researches.descriptions.108','octeract.data.octeractAmbrosiaLuck','purpleAmbrosia.data.taurus','hepteracts.orbEffect','singularityChallenge.data.noQuarkUpgrades']:
            self.assertIn(identifier, kept)

    def test_changed_and_new_text_require_review(self):
        entry = self.data['entries'][0].copy()
        for change in [{'text': entry['text'] + ' changed'}, {'id': 'brand.new.upgrade'}]:
            with self.assertRaisesRegex(ValueError, 'Review required'):
                apply_curation({'entries': [{**entry, **change}]})


if __name__ == '__main__':
    unittest.main()
