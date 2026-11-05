const BASE = 'https://soliddigitalpolska-create.github.io/solid-digital-probki250-13/';
export const CATEGORY_LABELS = Object.freeze({ WWW: 'Strony internetowe', SKLEP: 'Sklepy i e-commerce', AUTOMATYZACJA: 'Automatyzacje', IT: 'Aplikacje i integracje', GRAFIKA: 'Grafika i identyfikacja', UX: 'UX i audyty', DTP: 'Dokumenty i skład', VIDEO: 'Wideo i animacja', MARKETING: 'Marketing', BIUROWE: 'Procesy i organizacja', '3D': 'Projekty 3D', COPY: 'Treści', TLUMACZENIA: 'Wersje językowe' });

export function normalizeText(value) {
  return String(value ?? '').toLocaleLowerCase('pl').replaceAll('ł', 'l').normalize('NFD')
    .replace(/[\u0300-\u036f]/gu, '').replace(/[^a-z0-9]+/gu, ' ').trim();
}

export function prepareCatalog(rows) {
  if (!Array.isArray(rows) || rows.length > 1000) throw new Error('Nieprawidłowy katalog.');
  const seen = new Set();
  return rows.flatMap(row => {
    if (!row || typeof row.id !== 'string' || !/^[a-z0-9][a-z0-9-]*(?:\/[a-z0-9][a-z0-9-]*){0,4}$/u.test(row.id)
      || seen.has(row.id) || row.url !== `${BASE}${row.id}/` || typeof row.title !== 'string'
      || !row.title.trim() || !Array.isArray(row.categories)) return [];
    const categories = [...new Set(row.categories.filter(c => Object.hasOwn(CATEGORY_LABELS, c)))];
    if (!categories.length) return [];
    seen.add(row.id);
    return [{ id: row.id, url: row.url, title: row.title.trim().slice(0, 240), summary: typeof row.summary === 'string' ? row.summary.trim().slice(0, 360) : '', categories,
      tags: Array.isArray(row.tags) ? row.tags.filter(t => typeof t === 'string').slice(0, 32).map(t => t.slice(0, 80)) : [] }];
  });
}

export function findSamples(items, query, category) {
  const words = [...new Set(normalizeText(query).split(' ').filter(Boolean))];
  return items.filter(item => {
    if (category && !item.categories.includes(category)) return false;
    const searchable = normalizeText([item.title, item.summary, ...item.tags,
      ...item.categories.map(c => CATEGORY_LABELS[c] || c)].join(' '));
    return words.every(word => searchable.includes(word));
  });
}

export function readFilters(search) {
  const params = new URLSearchParams(search), category = params.get('kategoria') || '';
  return { query: (params.get('q') || '').slice(0, 160), category: Object.hasOwn(CATEGORY_LABELS, category) ? category : '' };
}

async function mountCatalog() {
  const input = document.querySelector('#search');
  if (!input) return;
  const select = document.querySelector('#category'), grid = document.querySelector('#results');
  const status = document.querySelector('#result-count'), more = document.querySelector('#load-more');
  const empty = document.querySelector('#empty'), clear = document.querySelector('#clear');
  document.querySelector('.search-panel').hidden = false;
  status.textContent = 'Wczytywanie katalogu…';
  const initial = readFilters(location.search);
  input.value = initial.query;
  let items = [], visible = 24;
  const text = (tag, className, value) => {
    const node = document.createElement(tag); node.className = className; node.textContent = value; return node;
  };
  const render = () => {
    const found = findSamples(items, input.value, select.value), fragment = document.createDocumentFragment();
    for (const item of found.slice(0, visible)) {
      const card = document.createElement('article'); card.className = 'sample';
      card.append(text('p', 'sample-type', CATEGORY_LABELS[item.categories[0]]));
      const heading = document.createElement('h3'), link = document.createElement('a');
      link.href = item.url; link.textContent = item.title.replace(/ — makieta$/u, ''); heading.append(link); card.append(heading);
      if (item.summary) card.append(text('p', 'sample-summary', item.summary));
      card.append(text('span', 'sample-cta', 'Otwórz demonstrację ↗')); fragment.append(card);
    }
    grid.replaceChildren(fragment);
    status.textContent = `${found.length} z ${items.length} przykładów · pokazano ${Math.min(visible, found.length)}`;
    empty.hidden = found.length > 0; more.hidden = found.length <= visible;
    more.textContent = `Pokaż kolejne ${Math.min(24, Math.max(0, found.length - visible))}`;
    clear.hidden = !input.value && !select.value;
    const url = new URL(location.href);
    input.value ? url.searchParams.set('q', input.value) : url.searchParams.delete('q');
    select.value ? url.searchParams.set('kategoria', select.value) : url.searchParams.delete('kategoria');
    history.replaceState(null, '', url);
  };
  try {
    const response = await fetch(new URL('./assets/portfolio-catalog.json', document.baseURI), { signal: AbortSignal.timeout(15000) });
    if (!response.ok) throw new Error('Katalog niedostępny.');
    const data = await response.json(); items = prepareCatalog(data.samples);
    if (!items.length) throw new Error('Katalog jest pusty.');
    const available = new Set(items.flatMap(item => item.categories));
    for (const [value, label] of Object.entries(CATEGORY_LABELS)) {
      if (!available.has(value)) continue;
      const option = document.createElement('option'); option.value = value; option.textContent = label; select.append(option);
    }
    select.value = available.has(initial.category) ? initial.category : '';
    input.disabled = false; select.disabled = false;
    input.addEventListener('input', () => { visible = 24; render(); });
    select.addEventListener('change', () => { visible = 24; render(); });
    more.addEventListener('click', () => { visible += 24; render(); });
    clear.addEventListener('click', () => { input.value = ''; select.value = ''; visible = 24; render(); input.focus(); });
    document.querySelectorAll('[data-query]').forEach(button => button.addEventListener('click', () => { input.value = button.dataset.query; select.value = ''; visible = 24; render(); input.focus(); }));
    document.querySelector('#catalog-total').textContent = String(items.length);
    document.querySelector('#quick-queries').hidden = false;
    render();
  } catch {
    status.textContent = 'Nie udało się wczytać katalogu. Poniżej nadal możesz otworzyć cztery wybrane przykłady.';
    document.querySelector('#catalog-total').textContent = '—'; document.querySelector('#quick-queries').hidden = true;
  }
}

if (typeof document !== 'undefined') mountCatalog();
