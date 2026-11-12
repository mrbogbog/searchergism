import { prepareEntries, findEntries } from './search.mjs';

const $ = (id) => document.getElementById(id);
const PAGE_SIZE = 60;
let entries = [];
let matches = [];
let shown = 0;
let searchFrame = 0;
let urlTimer = 0;
const formatter = new Intl.NumberFormat('en');

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function highlighted(text, query) {
  const fragment = document.createDocumentFragment();
  const words = [...new Set(query.split(/[^\p{L}\p{N}]+/u).filter(Boolean))].sort((a, b) => b.length - a.length);
  if (!words.length) {
    fragment.append(document.createTextNode(text));
    return fragment;
  }
  const escaped = words.map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const pattern = new RegExp(escaped.join('|'), 'giu');
  let offset = 0;
  for (const match of text.matchAll(pattern)) {
    fragment.append(document.createTextNode(text.slice(offset, match.index)), node('mark', match[0]));
    offset = match.index + match[0].length;
  }
  fragment.append(document.createTextNode(text.slice(offset)));
  return fragment;
}

function card(entry) {
  const article = node('article', undefined, 'card');
  article.dataset.entryId = entry.id;
  const category = node('p', entry.category, 'category');
  const title = node('h3');
  title.append(highlighted(entry.name, $('search').value));
  const description = node('p', undefined, 'description');
  description.append(highlighted(entry.text, $('search').value));
  article.append(category, title);
  if (entry.dynamic) article.append(node('span', 'Contains game-calculated values', 'dynamic'));
  article.append(description);
  const source = node('details', undefined, 'source');
  source.append(node('summary', 'Source · ' + entry.id));
  const list = node('ul');
  for (const item of entry.sources) {
    const line = node('li');
    line.append(node('code', item.file + ' → ' + item.key), node('span', item.raw));
    list.append(line);
  }
  source.append(list);
  article.append(source);
  return article;
}

function renderNextPage() {
  const fragment = document.createDocumentFragment();
  const end = Math.min(shown + PAGE_SIZE, matches.length);
  for (let index = shown; index < end; index++) fragment.append(card(matches[index]));
  $('results').append(fragment);
  shown = end;
  $('more').hidden = shown >= matches.length;
  $('more').textContent = `Show ${formatter.format(Math.min(PAGE_SIZE, matches.length - shown))} more results`;
  const count = formatter.format(matches.length);
  $('status').textContent = `${count} ${matches.length === 1 ? 'match' : 'matches'}${shown < matches.length ? ` · showing ${formatter.format(shown)}` : ''} / ${formatter.format(entries.length)} records`;
  $('results').setAttribute('aria-busy', 'false');
}

function updateURL() {
  const url = new URL(location.href);
  const query = $('search').value.trim();
  if (query) url.searchParams.set('q', query);
  else url.searchParams.delete('q');
  try { history.replaceState(null, '', url); } catch { /* Search remains usable if history is restricted. */ }
}

function search() {
  $('results').setAttribute('aria-busy', 'true');
  matches = findEntries(entries, $('search').value);
  $('results').replaceChildren();
  shown = 0;
  $('empty').hidden = matches.length !== 0;
  $('clear').disabled = !$('search').value;
  renderNextPage();
  clearTimeout(urlTimer);
  urlTimer = setTimeout(updateURL, 150);
}

function queueSearch() {
  clearTimeout(searchFrame);
  searchFrame = setTimeout(search, 0);
}

function clearSearch() {
  $('search').value = '';
  search();
  $('search').focus();
}

function coverage(meta) {
  $('version').textContent = meta.sourceVersion || '';
  $('coverage-description').textContent = `${formatter.format(meta.translationStringsIncluded)} English translation strings plus static HTML help, organized into ${formatter.format(entries.length)} records across ${Object.keys(meta.categories).length} categories. Seeded from the local Synergism ${meta.sourceVersion} reference. ${formatter.format(meta.dynamicEntries)} seed records contain game-calculated parameters.`;
  $('category-counts').replaceChildren();
  const counts = new Map();
  for (const entry of entries) counts.set(entry.category, (counts.get(entry.category) || 0) + 1);
  for (const [category, count] of [...counts].sort(([a], [b]) => a.localeCompare(b))) {
    const row = node('div');
    row.append(node('dt', category), node('dd', formatter.format(count)));
    $('category-counts').append(row);
  }
}

async function load() {
  $('error').hidden = true;
  $('retry').disabled = true;
  $('status').textContent = 'Loading the static index…';
  $('results').setAttribute('aria-busy', 'true');
  try {
    const response = await fetch(new URL('./data/index.json', import.meta.url));
    if (!response.ok) throw new Error(`Index request failed (${response.status})`);
    const data = await response.json();
    if (data.schemaVersion !== 1 || !Array.isArray(data.entries) || !data.entries.length) throw new Error('Invalid index schema');
    entries = prepareEntries(data.entries);
    coverage(data.meta);
    $('search').disabled = false;
    document.querySelectorAll('[data-query]').forEach((button) => { button.disabled = false; });
    search();
  } catch (error) {
    $('error').hidden = false;
    $('status').textContent = 'Index unavailable';
    $('results').setAttribute('aria-busy', 'false');
    console.error('Searchergism:', error);
  } finally {
    $('retry').disabled = false;
  }
}

$('search').value = new URL(location.href).searchParams.get('q') || '';
$('search-form').addEventListener('submit', (event) => { event.preventDefault(); search(); updateURL(); });
$('search').addEventListener('input', queueSearch);
$('clear').addEventListener('click', clearSearch);
$('reset').addEventListener('click', clearSearch);
$('more').addEventListener('click', renderNextPage);
$('retry').addEventListener('click', load);
document.querySelectorAll('[data-query]').forEach((button) => button.addEventListener('click', () => {
  $('search').value = button.dataset.query;
  search();
  $('search').focus();
}));
document.addEventListener('keydown', (event) => {
  if (event.ctrlKey || event.altKey || event.metaKey || event.isComposing) return;
  const editing = event.target instanceof Element && (event.target.matches('input, textarea, select') || event.target.isContentEditable);
  if (event.key === '/' && !editing) {
    event.preventDefault();
    $('search').focus();
  }
  if (event.key === 'Escape' && event.target === $('search')) {
    event.preventDefault();
    clearSearch();
  }
});
window.addEventListener('popstate', () => {
  $('search').value = new URL(location.href).searchParams.get('q') || '';
  if (entries.length) search();
});
load();
