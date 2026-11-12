import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { performance } from 'node:perf_hooks';
import { normalize, prepareEntries, findEntries } from '../search.mjs';

const data = JSON.parse(readFileSync(new URL('../data/index.json', import.meta.url)));
const entries = prepareEntries(data.entries);
assert.equal(findEntries(entries, '').length, entries.length);
assert.equal(findEntries(entries, '  !!!  ').length, entries.length);
assert.equal(normalize('  CUBES—Café  '), 'cubes cafe');
assert.equal(findEntries(entries, 'offering potion')[0].name, 'Offering Potion');
assert.equal(findEntries(entries, 'POTION offering')[0].name, 'Offering Potion');
assert.ok(findEntries(entries, 'first five runes').length > 0);
assert.ok(findEntries(entries, 'quark shop').length > 0);
assert.ok(findEntries(entries, 'hepteract').length > 0);
assert.ok(findEntries(entries, 'crystal upgrades').length > 0);
assert.equal(findEntries(entries, 'zzzznoresult987654').length, 0);
assert.doesNotThrow(() => findEntries(entries, '[.*+?^${}()|\\]'));
for (const phrase of ['golden quarks', 'platonic', 'rune', 'ambrosia', 'purple reactor', 'challenge', 'research']) {
  assert.ok(findEntries(entries, phrase).length > 0, phrase);
}
const custom = prepareEntries([{id:'test',name:'<img src=x onerror=alert(1)>',category:'Unusual',text:'Rarely normalized café',sources:[{key:'hiddenSourceIdentifier'}]}]);
assert.equal(findEntries(custom, 'cafe').length, 1);
assert.equal(findEntries(custom, 'hiddenSourceIdentifier').length, 1);
const start = performance.now();
for (let i = 0; i < 100; i++) findEntries(entries, ['quark', 'ambrosia', 'rune offering', 'cube upgrade'][i % 4]);
console.log(`Search assertions passed: ${entries.length} records; average query ${((performance.now() - start) / 100).toFixed(2)}ms`);
