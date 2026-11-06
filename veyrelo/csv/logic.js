export const LIMITS = Object.freeze({ bytes: 2097152, records: 5000, columns: 50, cells: 100000, field: 10000 });
const DELIMITERS = [',', ';', '\t'];
const FIELDS = ['sku', 'name', 'price', 'gtin', 'url'];
const LABELS = {sku:'SKU',name:'Nazwa',price:'Cena',gtin:'GTIN',url:'URL'};

function checkSize(text) {
  if (new TextEncoder().encode(text).byteLength > LIMITS.bytes) throw new Error('Przekroczono limit 2 MiB danych UTF-8.');
}

export function decodeUTF8(bytes) {
  if (bytes.byteLength > LIMITS.bytes) throw new Error('Przekroczono limit 2 MiB pliku.');
  try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { throw new Error('Plik nie jest poprawnym UTF-8. Zapisz go ponownie jako CSV UTF-8.'); }
}

export function parseCSV(source, delimiter) {
  if (typeof source !== 'string') throw new Error('CSV musi być tekstem.');
  checkSize(source);
  if (!DELIMITERS.includes(delimiter)) throw new Error('Nieobsługiwany separator CSV.');
  const text = source.replace(/^\uFEFF/, '');
  if (!text.trim()) throw new Error('Dane CSV są puste.');
  const rows = [];
  let values = [], field = '', state = 'start', line = 1, startLine = 1, cells = 0;
  const fail = message => {
    const error = new Error(`${message} (rekord ${rows.length + 1}, linia ${line}).`);
    error.record = rows.length + 1;
    error.line = line;
    error.code = 'CSV_STRUCTURE';
    throw error;
  };
  const pushField = () => {
    values.push(field);
    if (values.length > LIMITS.columns) fail('Przekroczono limit 50 kolumn');
    if (++cells > LIMITS.cells) fail('Przekroczono limit 100000 komórek (łącznie z nagłówkiem)');
    field = ''; state = 'start';
  };
  const pushRow = () => {
    pushField();
    if (rows.length && values.length !== rows[0].values.length) fail(`Niewłaściwa liczba pól: ${values.length}, oczekiwano ${rows[0].values.length}`);
    if (rows.length > LIMITS.records) fail('Przekroczono limit 5000 rekordów danych');
    rows.push({ number: rows.length + 1, line: startLine, values });
    values = [];
  };
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const newline = ch === '\r' || ch === '\n';
    if (state === 'quoted') {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else state = 'closed';
      } else {
        field += ch;
        if (newline) {
          if (ch === '\r' && text[i + 1] === '\n') { field += '\n'; i++; }
          line++;
        }
      }
    } else if (ch === delimiter) {
      pushField();
    } else if (newline) {
      pushRow();
      if (ch === '\r' && text[i + 1] === '\n') i++;
      line++; startLine = line;
    } else if (state === 'closed') {
      fail('Niedozwolony znak po zamykającym cudzysłowie');
    } else if (ch === '"') {
      if (state !== 'start') fail('Cudzysłów wewnątrz niecytowanego pola');
      state = 'quoted';
    } else {
      field += ch; state = 'plain';
    }
    if (field.length > LIMITS.field) fail('Przekroczono limit 10000 znaków w komórce');
  }
  if (state === 'quoted') fail('Niezamknięty cudzysłów');
  if (field.length || values.length || state !== 'start') pushRow();
  return { headers: rows[0].values, records: rows.slice(1), delimiter };
}

export function detectDelimiter(text) {
  checkSize(text);
  const candidates = [];
  for (const delimiter of DELIMITERS) {
    try {
      const parsed = parseCSV(text, delimiter);
      if (parsed.headers.length > 1) candidates.push(delimiter);
    } catch { /* A malformed candidate cannot establish a separator. Manual selection exposes the exact error. */ }
  }
  return { delimiter: candidates.length === 1 ? candidates[0] : null, ambiguous: candidates.length > 1, candidates };
}

export function profileColumns(table) {
  return table.headers.map((name, index) => {
    const values = table.records.map(row => row.values[index].trim());
    const nonempty = values.filter(Boolean);
    const unique = new Set(nonempty);
    return { column: index + 1, name, empty: values.length - nonempty.length, distinct: unique.size, samples: [...unique].slice(0, 3) };
  });
}

export function inferMapping(headers) {
  const aliases = {sku:['sku','id','kod','identyfikator'],name:['name','nazwa','nazwa produktu','title'],price:['price','cena'],gtin:['gtin','ean','upc'],url:['url','link','adres','product url']};
  const normalized = headers.map(value => value.trim().toLowerCase());
  return Object.fromEntries(FIELDS.map(field => [field, normalized.findIndex(value => aliases[field].includes(value))]));
}

export function validateMapping(mapping, columns) {
  const errors = [], used = new Set();
  for (const field of FIELDS) {
    const index = mapping[field] ?? -1;
    if (index === -1 && ['gtin', 'url'].includes(field)) continue;
    if (!Number.isInteger(index) || index < 0 || index >= columns) { errors.push(`Wybierz kolumnę dla pola ${LABELS[field]}.`); continue; }
    if (used.has(index)) errors.push(`Kolumna ${index + 1} jest przypisana do kilku pól.`);
    used.add(index);
  }
  return errors;
}

export function validateGTIN(source) {
  const value = String(source).trim();
  if (!/^(?:\d{8}|\d{12}|\d{13}|\d{14})$/.test(value)) return { valid: false, code: 'GTIN_FORMAT', message: 'GTIN wymaga dokładnie 8, 12, 13 lub 14 cyfr; zera początkowe są istotne.' };
  let sum = 0, weight = 3;
  for (let i = value.length - 2; i >= 0; i--) { sum += Number(value[i]) * weight; weight = weight === 3 ? 1 : 3; }
  const valid = (10 - sum % 10) % 10 === Number(value.at(-1));
  return valid ? { valid: true } : { valid: false, code: 'GTIN_CHECKSUM', message: 'Nieprawidłowa cyfra kontrolna GTIN. Zweryfikuj kod u źródła; narzędzie go nie poprawia.' };
}

export function parsePrice(source) {
  const value = String(source).trim();
  const invalid = { valid: false, code: 'PRICE_INVALID', message: 'Podaj nieujemną cenę bez waluty, np. 1234,50; maksymalnie 2 cyfry po separatorze.' };
  if ((value.includes(',') && value.includes('.')) || /[.,]\d{3,}$/.test(value)) return { valid:false, code:'PRICE_AMBIGUOUS', message:'Niejednoznaczna cena. Użyj np. 1234,50 lub 1 234,50; narzędzie nie zgaduje separatorów.' };
  if (!/^(?:\d+|\d{1,3}(?:[ \u00a0\u202f]\d{3})+)(?:[.,]\d{1,2})?$/.test(value)) return invalid;
  const numeric = Number(value.replace(/[ \u00a0\u202f]/g, '').replace(',', '.'));
  if (!Number.isFinite(numeric) || numeric > Number.MAX_SAFE_INTEGER / 100) return { ...invalid, message:'Cena przekracza bezpieczny zakres liczbowy narzędzia.' };
  return { valid: true, value: numeric };
}

export function validateHTTPURL(source) {
  const value = String(source).trim();
  const invalid = { valid: false, code: 'URL_INVALID', message: 'Wymagany pełny adres HTTP lub HTTPS bez spacji, znaków sterujących i danych logowania.' };
  if (!/^https?:\/\//i.test(value) || /[\s\u0000-\u001f\u007f\\]/.test(value) || /%(?![\da-f]{2})/i.test(value)) return invalid;
  try {
    const url = new URL(value);
    return url.hostname && !url.username && !url.password ? { valid: true } : invalid;
  } catch { return invalid; }
}

export function auditTable(table, mapping) {
  const mappingErrors = validateMapping(mapping, table.headers.length);
  if (mappingErrors.length) throw new Error(`Nieprawidłowe mapowanie: ${mappingErrors.join(' ')}`);
  const issues = [], seenSKU = new Map();
  const add = (row, field, result) => issues.push({ record:row.number, line:row.line, column:mapping[field]+1, field, code:result.code, message:result.message });
  for (const row of table.records) {
    for (const field of ['sku', 'name', 'price']) {
      if (!row.values[mapping[field]].trim()) add(row, field, {code:'REQUIRED_EMPTY',message:`Brak wartości wymaganego pola ${LABELS[field]}.`});
    }
    const sku = row.values[mapping.sku].trim();
    if (sku) {
      const group = seenSKU.get(sku) || [];
      group.push(row); seenSKU.set(sku, group);
    }
    for (const [field, validate] of [['price',parsePrice],['gtin',validateGTIN],['url',validateHTTPURL]]) {
      const index = mapping[field];
      if (!Number.isInteger(index) || index < 0) continue;
      const value = row.values[index].trim();
      if (!value) continue;
      const result = validate(value);
      if (!result.valid) add(row, field, result);
    }
  }
  for (const rows of seenSKU.values()) if (rows.length > 1) {
    for (const row of rows) add(row, 'sku', {code:'DUPLICATE_SKU',message:`Powtórzony SKU w ${rows.length} rekordach; porównanie po przycięciu brzegów, z rozróżnieniem wielkości liter.`});
  }
  issues.sort((a,b) => a.record-b.record || a.column-b.column);
  return { records:table.records.length, issues, affectedRecords:new Set(issues.map(issue=>issue.record)).size };
}

export function tidyTable(table) {
  const changes = [];
  const trim = (value, record, column) => {
    const after = value.trim();
    if (after !== value) changes.push({record,column,before:value,after});
    return after;
  };
  return {
    table: {delimiter:table.delimiter,headers:table.headers.map((value,index)=>trim(value,1,index+1)),records:table.records.map(row=>({...row,values:row.values.map((value,index)=>trim(value,row.number,index+1))}))},
    changes
  };
}

function unsafeCells(table) {
  const unsafe = [];
  const inspect = (values, record) => values.forEach((value,index) => {
    // Conservative block. This is not a promise of universal spreadsheet sanitisation.
    const prefix = value.match(/^[\s\p{Cc}\p{Cf}]*/u)?.[0] || '';
    const remainder = value.slice(prefix.length);
    if (/[\t\r\n\u0000-\u001f\u007f]/.test(prefix) || /^[=+\-@＝＋－＠]/.test(remainder)) unsafe.push({record,column:index+1,reason:'Początek komórki może być interpretowany jako formuła lub zawiera znak sterujący.'});
  });
  inspect(table.headers,1);
  table.records.forEach(row => inspect(row.values,row.number));
  return unsafe;
}

export function buildCSVExport(table, original = table) {
  const byCell = new Map([...unsafeCells(original),...unsafeCells(table)].map(cell=>[`${cell.record}:${cell.column}`,cell]));
  const unsafe = [...byCell.values()];
  if (unsafe.length) return { blocked:true, csv:null, unsafe };
  const encode = value => /["\r\n]/.test(value) || value.includes(table.delimiter) ? `"${value.replace(/"/g,'""')}"` : value;
  const rows = [table.headers,...table.records.map(row=>row.values)];
  return { blocked:false, csv:'\uFEFF' + rows.map(row=>row.map(encode).join(table.delimiter)).join('\r\n') + '\r\n', unsafe:[] };
}

export function buildJSONReport(table, mapping, audit = auditTable(table, mapping)) {
  const tidy = tidyTable(table);
  const exported = buildCSVExport(tidy.table, table);
  return JSON.stringify({
    schemaVersion:1, tool:'Veyrelo — audyt CSV', records:table.records.length, columns:table.headers.length,
    recordNumbering:'Nagłówek = rekord 1. Pole wielowierszowe pozostaje jednym rekordem. line = pierwsza linia rekordu.',
    delimiter:table.delimiter,
    mapping:Object.fromEntries(FIELDS.map(field=>[field,Number.isInteger(mapping[field]) && mapping[field]>=0 ? {column:mapping[field]+1,header:table.headers[mapping[field]]} : null])),
    summary:{issues:audit.issues.length,affectedRecords:audit.affectedRecords},
    issues:audit.issues, trimChanges:tidy.changes,
    csvExport:{blocked:exported.blocked,unsafeCells:exported.unsafe},
    limits:LIMITS,
    limitations:['Walidacja GTIN sprawdza format i sumę kontrolną, nie rejestrację ani tożsamość produktu.','URL jest sprawdzany składniowo; dostępność i treść nie są pobierane.','Eksport CSV zmienia tylko białe znaki na brzegach pól. Kontrole nie stanowią certyfikacji ani gwarancji przyjęcia pliku przez platformę.','Raport może zawierać dane źródłowe w nazwach nagłówków i liście zmian; sprawdź go przed udostępnieniem.']
  },null,2);
}
