import { prepareEntries, findEntries } from './search.mjs';

const $ = (id) => document.getElementById(id);
const PAGE_SIZE = 60;
let entries = [];
let matches = [];
let shown = 0;
let searchFrame = 0;
let urlTimer = 0;
let categories = [];
let selectedCategories = new Set();

function readCategorySelection() {
  const params = new URL(location.href).searchParams;
  selectedCategories = new Set(params.has('category')
    ? params.getAll('category').filter((category) => categories.includes(category))
    : categories);
}

function syncCategoryControls() {
  document.querySelectorAll('#category-options input').forEach((input) => {
    input.checked = selectedCategories.has(input.value);
  });
  $('category-summary').textContent = `${selectedCategories.size} / ${categories.length} selected`;
  $('select-all').disabled = selectedCategories.size === categories.length;
  $('select-none').disabled = selectedCategories.size === 0;
}

function buildCategoryControls() {
  const counts = new Map();
  for (const entry of entries) counts.set(entry.category, (counts.get(entry.category) || 0) + 1);
  categories = [...counts.keys()].sort((a, b) => a.localeCompare(b));
  readCategorySelection();
  $('category-options').replaceChildren();
  for (const category of categories) {
    const label = node('label', undefined, 'category-toggle');
    const input = node('input');
    input.type = 'checkbox';
    input.value = category;
    input.addEventListener('change', () => {
      if (input.checked) selectedCategories.add(category);
      else selectedCategories.delete(category);
      syncCategoryControls();
      search();
    });
    label.append(input, node('span', category), node('span', formatter.format(counts.get(category)), 'category-count'));
    $('category-options').append(label);
  }
  syncCategoryControls();
}
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
  url.searchParams.delete('category');
  if (selectedCategories.size !== categories.length) {
    if (selectedCategories.size === 0) url.searchParams.append('category', '');
    else categories.filter((category) => selectedCategories.has(category)).forEach((category) => url.searchParams.append('category', category));
  }
  try { history.replaceState(null, '', url); } catch { /* Search remains usable if history is restricted. */ }
}

function search() {
  $('results').setAttribute('aria-busy', 'true');
  matches = findEntries(entries, $('search').value, selectedCategories);
  $('empty-hint').textContent = selectedCategories.size === 0
    ? 'No categories are selected. Select a category or reset all filters.'
    : 'Try fewer words, select more categories, or reset all filters.';
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
    $('version').textContent = data.meta.sourceVersion || '';
    $('search').disabled = false;
    buildCategoryControls();
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
$('reset').addEventListener('click', () => {
  selectedCategories = new Set(categories);
  syncCategoryControls();
  clearSearch();
});
$('more').addEventListener('click', renderNextPage);
$('retry').addEventListener('click', load);
$('select-all').addEventListener('click', () => {
  selectedCategories = new Set(categories);
  syncCategoryControls();
  search();
});
$('select-none').addEventListener('click', () => {
  selectedCategories.clear();
  syncCategoryControls();
  search();
});
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
  if (entries.length) {
    readCategorySelection();
    syncCategoryControls();
    search();
  }
});
load();
