import { LIMITS, parseCSV, detectDelimiter, decodeUTF8, profileColumns, inferMapping, validateMapping, auditTable, tidyTable, buildCSVExport, buildJSONReport } from './logic.js';

const $ = id => document.getElementById(id);
const fields = ['sku','name','price','gtin','url'];
const source = $('csv-source');
const separators = {comma:',',semicolon:';',tab:'\t'};
const separatorLabels = {',':'przecinek',';':'średnik','\t':'tabulator'};
let parsed = null, current = null, revision = 0;

function status(message, tone = '') {
  $('csv-status').textContent = message;
  $('csv-status').dataset.tone = tone;
}

function invalidateAudit() {
  current = null;
  $('csv-download').disabled = true;
  $('json-download').disabled = true;
  $('csv-result-panel').hidden = true;
}

function invalidateSource(message = 'Dane zmienione. Wczytaj je ponownie, aby uzyskać aktualny wynik.') {
  revision++;
  parsed = null;
  invalidateAudit();
  $('csv-parse').disabled = false;
  $('csv-mapping-panel').hidden = true;
  status(message);
}

function readMapping() { return Object.fromEntries(fields.map(field => [field, Number($(`map-${field}`).value)])); }

function updateMappingStatus() {
  if (!parsed) return;
  const errors = validateMapping(readMapping(), parsed.headers.length);
  if (!parsed.records.length) errors.push('Plik zawiera tylko nagłówek. Dodaj co najmniej jeden rekord danych.');
  $('mapping-status').textContent = errors.length ? errors.join(' ') : 'Mapowanie jest kompletne. Możesz uruchomić audyt.';
  $('mapping-status').dataset.tone = errors.length ? 'error' : 'success';
  $('csv-audit').disabled = errors.length > 0;
}

function element(tag, text) { const node = document.createElement(tag); if (text !== undefined) node.textContent = String(text); return node; }
function short(value, length = 180) { const text = String(value); return text.length > length ? text.slice(0,length) + '…' : text; }

function renderTable(target, headers, rows, caption) {
  const container = $(target);
  container.replaceChildren();
  if (!rows.length) { container.append(element('p', 'Brak pozycji.')); return; }
  const table = element('table');
  if (caption) table.append(element('caption', caption));
  const head = element('thead'), headerRow = element('tr');
  headers.forEach(label => { const th = element('th',short(label)); th.scope = 'col'; headerRow.append(th); });
  head.append(headerRow); table.append(head);
  const body = element('tbody');
  rows.forEach(values => {
    const row = element('tr');
    values.forEach(value => row.append(element('td', value)));
    body.append(row);
  });
  table.append(body); container.append(table);
}

source.addEventListener('input', () => { $('csv-file').value = ''; invalidateSource(); });
$('csv-delimiter').addEventListener('change', () => invalidateSource('Separator zmieniony. Wczytaj dane ponownie.'));
fields.forEach(field => $(`map-${field}`).addEventListener('change', () => { invalidateAudit(); updateMappingStatus(); status('Mapowanie zmienione. Uruchom audyt ponownie.'); }));

$('csv-file').addEventListener('change', async event => {
  const file = event.target.files[0];
  invalidateSource('Wczytywanie pliku lokalnie…');
  source.value = '';
  if (!file) { status('Wybierz plik lub wklej dane.'); return; }
  const token = revision;
  $('csv-parse').disabled = true;
  try {
    if (file.size > LIMITS.bytes) throw new Error('Przekroczono limit 2 MiB pliku.');
    const bytes = new Uint8Array(await file.arrayBuffer());
    if (token !== revision) return;
    source.value = decodeUTF8(bytes);
    status(`Wczytano lokalnie: ${short(file.name,100)}. Kliknij „Wczytaj i zobacz kolumny”.`);
  } catch (error) { if (token === revision) status(error.message, 'error'); }
  finally { if (token === revision) $('csv-parse').disabled = false; }
});

$('csv-demo').addEventListener('click', () => {
  invalidateSource();
  $('csv-file').value = '';
  $('csv-delimiter').value = 'auto';
  source.value = 'SKU;Nazwa;Cena;GTIN;URL\n KUB-01 ; Kubek demonstracyjny ;29,90;00012345600012;https://example.invalid/kubek\nKUB-01;"Kubek z opisem\nw dwóch liniach";1,234;4006381333932;brak-adresu\nTOR-02;Torba demonstracyjna;49,00;;https://example.invalid/torba';
  status('Wstawiono fikcyjne dane z celowymi błędami. Kody GTIN służą wyłącznie demonstracji; nie potwierdzają przypisania do produktów.');
});

$('csv-parse').addEventListener('click', () => {
  invalidateAudit();
  parsed = null;
  $('csv-mapping-panel').hidden = true;
  try {
    let delimiter = separators[$('csv-delimiter').value];
    if (!delimiter) {
      const detected = detectDelimiter(source.value);
      if (!detected.delimiter) throw new Error('Nie można jednoznacznie rozpoznać separatora. Wybierz go ręcznie; jeśli plik jest uszkodzony, otrzymasz numer problematycznego rekordu.');
      delimiter = detected.delimiter;
    }
    parsed = parseCSV(source.value, delimiter);
    const suggestion = inferMapping(parsed.headers);
    fields.forEach(field => {
      const select = $(`map-${field}`);
      select.replaceChildren();
      const empty = element('option', ['gtin','url'].includes(field) ? 'Pomiń kontrolę tego pola' : 'Wybierz kolumnę');
      empty.value = '-1'; select.append(empty);
      parsed.headers.forEach((header,index) => { const option = element('option', `${index + 1}. ${short(header || '(pusty nagłówek)',80)}`); option.value = String(index); select.append(option); });
      select.value = String(suggestion[field]);
    });
    $('csv-loaded').textContent = `${parsed.records.length} rekordów danych · ${parsed.headers.length} kolumn · separator: ${separatorLabels[delimiter]}.`;
    renderTable('csv-preview',['Rekord','Linia',...parsed.headers],parsed.records.slice(0,20).map(row=>[row.number,row.line,...row.values.map(value=>short(value))]),'Dane źródłowe — bez zmian');
    renderTable('csv-profiles',['Kolumna','Nagłówek','Puste','Unikalne niepuste','Próbki'],profileColumns(parsed).map(profile=>[profile.column,short(profile.name),profile.empty,profile.distinct,profile.samples.map(sample=>short(sample,70)).join(' | ')]),'Profil wszystkich kolumn');
    $('csv-mapping-panel').hidden = false;
    updateMappingStatus();
    status('Dane wczytane. Sprawdź mapowanie pól i uruchom audyt.', 'success');
  } catch (error) { status(error.message, 'error'); }
});

$('csv-audit').addEventListener('click', () => {
  invalidateAudit();
  if (!parsed) return;
  try {
    const mapping = readMapping();
    const audit = auditTable(parsed, mapping);
    const tidy = tidyTable(parsed);
    const exported = buildCSVExport(tidy.table, parsed);
    current = { table:parsed, mapping, audit, tidy, exported };
    const unchecked = ['gtin','url'].filter(field=>mapping[field]===-1).map(field=>field.toUpperCase());
    $('csv-summary').textContent = `${audit.records} rekordów danych · ${audit.issues.length} problemów · ${audit.affectedRecords} rekordów wymagających uwagi. ${unchecked.length ? 'Pominięte kontrole: '+unchecked.join(', ')+'.' : 'GTIN i URL: kontrole włączone dla niepustych wartości.'}`;
    $('issue-count').textContent = audit.issues.length ? `Pokazano ${Math.min(audit.issues.length,200)} z ${audit.issues.length} problemów. Pełna lista jest w JSON.` : 'Nie wykryto problemów w wybranych kontrolach. To nie gwarantuje poprawności wszystkich danych ani przyjęcia importu.';
    renderTable('csv-issues',['Rekord','Linia','Kolumna / pole','Problem'],audit.issues.slice(0,200).map(issue=>[issue.record,issue.line,`${issue.column} / ${issue.field.toUpperCase()}`,issue.message]));
    $('trim-count').textContent = `${tidy.changes.length} proponowanych zmian. Pokazano ${Math.min(tidy.changes.length,100)}; pełna lista jest w JSON.`;
    renderTable('csv-changes',['Rekord','Kolumna','Przed','Po'],tidy.changes.slice(0,100).map(change=>[change.record,change.column,short(JSON.stringify(change.before),240),short(JSON.stringify(change.after),240)]));
    $('csv-export-status').textContent = exported.blocked ? `Eksport CSV zablokowany: ${exported.unsafe.length} komórek z ryzykownym początkiem. Popraw dane u źródła i uruchom audyt ponownie. Nie usuwamy tych znaków ani nie dopisujemy apostrofu. Raport JSON jest dostępny.` : 'Eksport CSV jest dostępny. Zawiera tylko przycięcie brzegów; wykryte błędy biznesowe pozostają do poprawy. Importuj identyfikatory jako tekst, aby arkusz nie usunął zer początkowych.';
    $('csv-export-status').dataset.tone = exported.blocked ? 'error' : '';
    renderTable('csv-unsafe',['Rekord','Kolumna','Powód blokady'],exported.unsafe.slice(0,100).map(cell=>[cell.record,cell.column,cell.reason]),exported.blocked ? `Pokazano ${Math.min(exported.unsafe.length,100)} z ${exported.unsafe.length} komórek blokujących eksport.` : '');
    if (!exported.blocked) $('csv-unsafe').replaceChildren();
    $('csv-download').disabled = exported.blocked;
    $('json-download').disabled = false;
    $('csv-result-panel').hidden = false;
    status(`Audyt zakończony: ${audit.issues.length} problemów. ${exported.blocked ? 'Eksport CSV zablokowany; JSON dostępny.' : 'Sprawdź wynik i podgląd zmian przed pobraniem.'}`,audit.issues.length || exported.blocked ? '' : 'success');
  } catch (error) { status(error.message,'error'); }
});

function download(contents, mime, filename) {
  const url = URL.createObjectURL(new Blob([contents],{type:mime}));
  const anchor = element('a'); anchor.href = url; anchor.download = filename;
  document.body.append(anchor); anchor.click(); anchor.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}

$('csv-download').addEventListener('click', () => {
  if (!current || current.exported.blocked) return;
  download(current.exported.csv,'text/csv;charset=utf-8','veyrelo-csv-po-przycieciu.csv');
  status('Przygotowano lokalny plik CSV do pobrania.');
});
$('json-download').addEventListener('click', () => {
  if (!current) return;
  download(buildJSONReport(current.table,current.mapping,current.audit),'application/json;charset=utf-8','veyrelo-audyt-csv.json');
  status('Przygotowano lokalny raport JSON do pobrania.');
});
