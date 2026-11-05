import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { normalizeText, findSamples, prepareCatalog, readFilters } from '../assets/catalog-search.mjs';

const base = 'https://soliddigitalpolska-create.github.io/solid-digital-probki250-13/';
const row = (id, title, categories, summary = '') => ({ id, title, categories, summary, tags: [], url: `${base}${id}/` });
const samples = [row('sklep', 'Sklep Łódź', ['SKLEP'], 'API Shoper'), row('api', 'Łódź API', ['IT']), row('grafika', 'Grafika', ['GRAFIKA'])];

test('Polish accents, ł, case and numbers do not prevent a match', () => {
  assert.equal(normalizeText('ŁÓDŹ, Żółć i n8n!'), 'lodz zolc i n8n');
});

test('all query words must occur in the searchable metadata', () => {
  assert.deepEqual(findSamples(samples, 'lodz shoper', '').map(x => x.id), ['sklep']);
  assert.deepEqual(findSamples(samples, 'API LODZ', '').map(x => x.id), ['sklep', 'api']);
  assert.deepEqual(findSamples(samples, 'nieistniejący wynik', ''), []);
});

test('category combines with search and an empty query lists that category', () => {
  assert.deepEqual(findSamples(samples, 'lodz', 'IT').map(x => x.id), ['api']);
  assert.deepEqual(findSamples(samples, '', 'GRAFIKA').map(x => x.id), ['grafika']);
  assert.equal(findSamples(samples, '', '').length, 3);
});

test('catalogue rejects external links, traversal paths and duplicate ids', () => {
  const good = row('bezpieczny', 'Przykład', ['WWW']);
  const actual = prepareCatalog([good, good, { ...row('inny', 'Inny', ['WWW']), url: 'https://example.com/' }, row('../sekret', 'Błędny', ['IT']), row('brak-typu', 'Błędny', ['NIEZNANA'])]);
  assert.deepEqual(actual.map(x => x.id), ['bezpieczny']);
});

test('shared filters decode Polish text, bound query length and reject unknown categories', () => {
  assert.deepEqual(readFilters('?q=%C5%BC%C3%B3%C5%82%C4%87&kategoria=SKLEP'), { query: 'żółć', category: 'SKLEP' });
  assert.equal(readFilters('?q=' + 'a'.repeat(300)).query.length, 160);
  assert.equal(readFilters('?kategoria=javascript%3Aalert(1)').category, '');
});

test('the initial document remains usable when its script cannot load', () => {
  const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  assert.match(html, /class="search-panel"[^>]*hidden/u);
  assert.match(html, /id="quick-queries"[^>]*hidden/u);
  const status = html.match(/<p id="result-count"[^>]*>([\s\S]*?)<\/p>/u)[1];
  assert.doesNotMatch(status, /Wczytywanie/u);
  assert.match(status, /href="#featured"/u);
});
