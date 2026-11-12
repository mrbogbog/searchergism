export function normalize(value) {
  return value.normalize('NFKD').replace(/\p{M}/gu, '').toLocaleLowerCase('en').replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
}

export function prepareEntries(entries) {
  return entries.map((entry) => ({
    ...entry,
    searchName: normalize(entry.name),
    searchText: normalize([entry.name, entry.text, entry.category, entry.id, ...entry.sources.map((s) => s.key)].join(' '))
  }));
}

export function findEntries(entries, query, categories = null) {
  if (categories !== null) entries = entries.filter((entry) => categories.has(entry.category));
  const normalized = normalize(query);
  const words = [...new Set(normalized.split(' ').filter(Boolean))];
  if (!words.length) return entries;
  return entries.filter((entry) => words.every((word) => entry.searchText.includes(word)))
    .map((entry) => ({ entry, rank: (entry.searchName === normalized ? 100 : 0) + (entry.searchName.includes(normalized) ? 20 : 0) + words.filter((word) => entry.searchName.includes(word)).length }))
    .sort((a, b) => b.rank - a.rank || a.entry.category.localeCompare(b.entry.category) || a.entry.name.localeCompare(b.entry.name))
    .map(({ entry }) => entry);
}
