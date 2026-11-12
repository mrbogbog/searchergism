"""Verify every selected translation is preserved once with original provenance."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('extract', ROOT / 'scripts/extract.py')
extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract)


class ExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/index.json').read_text())
        cls.source = json.loads((ROOT / 'source-reference/SynergismOfficial/translations/en.json').read_text())

    def test_unique_ids_and_counts(self):
        entries = self.data['entries']
        self.assertEqual(len(entries), len({e['id'] for e in entries}))
        self.assertEqual(dict(Counter(e['category'] for e in entries)), self.data['meta']['categories'])
        self.assertEqual(len(entries), self.data['meta']['entries'])
        self.assertTrue(all(e['name'] and e['text'] and e['sources'] for e in entries))

    def test_complete_selected_roots_and_exact_raw_text(self):
        expected = {k: v for root in extract.CATEGORIES for k, v in extract.flatten(self.source[root], [root])}
        found = {}
        for entry in self.data['entries']:
            self.assertNotIn('<<', entry['text'])
            self.assertNotIn('num:((', entry['text'])
            for source in entry['sources']:
                if source['file'] == 'translations/en.json':
                    self.assertNotIn(source['key'], found)
                    found[source['key']] = source['raw']
        self.assertEqual(expected, found)

    def test_cleaning(self):
        source = {'word': 'Cubes', 'loop': '$t(loop)'}
        self.assertEqual(extract.clean('<<gold|{{amount}}>> <b>$t(word)</b><br>num:((1e12))', source), '⟨amount⟩ Cubes\n1e12')
        self.assertIn('[translation: loop]', extract.clean('$t(loop)', source))
        self.assertEqual(extract.clean('&lt;img&gt;', source), '<img>')
        self.assertEqual(extract.clean('< LOCKED >', source), '< LOCKED >')

    def test_deterministic_seed(self):
        self.assertEqual(extract.extract(ROOT / 'source-reference/SynergismOfficial'), self.data)


if __name__ == '__main__':
    unittest.main()
