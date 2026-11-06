import test from 'node:test';
import assert from 'node:assert/strict';
import { parseCSV, detectDelimiter, decodeUTF8, profileColumns, inferMapping, validateMapping, validateGTIN, parsePrice, validateHTTPURL, auditTable, tidyTable, buildCSVExport, buildJSONReport } from '../csv/logic.js';

const mapping = { sku: 0, name: 1, price: 2, gtin: 3, url: 4 };
const fixture = () => parseCSV('SKU;Nazwa;Cena;GTIN;URL\n A ; Kubek ;12,50;00012345600012;https://example.invalid/p\nA;Drugi;1,234;4006381333932;javascript:alert(1)', ';');

// Break caught: splitting quoted text instead of respecting CSV records.
test('reads quoted delimiters, escaped quotes and BOM without losing leading zeros', () => {
  const table = parseCSV('\uFEFFsku,nazwa,cena\r\n001,"Kubek, ""duży""",12.50\r\n', ',');
  assert.deepEqual(table.headers, ['sku', 'nazwa', 'cena']);
  assert.deepEqual(table.records, [{ number: 2, line: 2, values: ['001', 'Kubek, "duży"', '12.50'] }]);
});
test('reports logical record numbers independently of multiline physical lines', () => {
  const table = parseCSV('sku;nazwa;cena\nA;"Pierwsza\ndruga";10\nB;Inny;20', ';');
  assert.equal(table.records[1].number, 3);
  assert.equal(table.records[1].line, 4);
  assert.equal(table.records[0].values[1], 'Pierwsza\ndruga');
});
for (const source of ['a;b\n"oops;x', 'a;b\nx"y;z', 'a;b\n"x"extra;y', 'a;b\nx;y;z']) {
  test(`rejects malformed CSV: ${JSON.stringify(source)}`, () => assert.throws(() => parseCSV(source, ';'), /rekord 2/i));
}
test('rejects empty input and unsupported delimiters', () => {
  assert.throws(() => parseCSV('', ';'), /pust/i);
  assert.throws(() => parseCSV('a|b', '|'), /separator/i);
});
test('enforces file size before parsing', () => assert.throws(() => parseCSV('x'.repeat(2097153), ';'), /2 MiB/));
test('enforces row, column, cell and field bounds', () => {
  assert.throws(() => parseCSV('a\n' + 'b\n'.repeat(5001), ';'), /5000/);
  assert.throws(() => parseCSV(Array(51).fill('a').join(';'), ';'), /50 kolumn/);
  assert.throws(() => parseCSV('a\n' + 'x'.repeat(10001), ';'), /10000/);
  const wide = Array(50).fill('x').join(';');
  assert.throws(() => parseCSV((wide + '\n').repeat(2002), ';'), /100000/);
});
test('decodes UTF-8 BOM and rejects malformed bytes', () => {
  assert.equal(decodeUTF8(new Uint8Array([239,187,191,197,130])), 'ł');
  assert.throws(() => decodeUTF8(new Uint8Array([195,40])), /UTF-8/);
});
for (const [delimiter, source] of [[',','a,b,c\nx,"y,z",1'],[';','a;b;c\nx;y;1,20'],['\t','a\tb\tc\nx\ty\t1']]) {
  test(`detects ${JSON.stringify(delimiter)} outside quotes`, () => assert.equal(detectDelimiter(source).delimiter, delimiter));
}
test('requires manual separator for ambiguous or single-column text', () => {
  assert.equal(detectDelimiter('a,b;c\nx,y;z').ambiguous, true);
  assert.equal(detectDelimiter('a\nx').delimiter, null);
});
test('profiles empty cells and distinct trimmed values, preserving string samples', () => {
  const profile = profileColumns(parseCSV('SKU;Nazwa\n001; Kot \n001; \n002;Pies', ';'));
  assert.equal(profile[0].distinct, 2);
  assert.equal(profile[1].empty, 1);
  assert.deepEqual(profile[0].samples, ['001', '002']);
});
test('suggests familiar headers but requires unique mapped required columns', () => {
  assert.deepEqual(inferMapping(['SKU','Nazwa','Cena','GTIN','URL']), mapping);
  assert.equal(validateMapping({sku:0,name:1,price:2,gtin:-1,url:-1}, 3).length, 0);
  assert.ok(validateMapping({sku:0,name:0,price:-1}, 3).length >= 2);
  assert.ok(validateMapping({sku:0,name:1,price:99}, 3).length > 0);
});
for (const gtin of ['96385074','036000291452','4006381333931','00012345600012']) {
  test(`accepts hand-checked GTIN ${gtin}`, () => assert.equal(validateGTIN(gtin).valid, true));
}
for (const gtin of ['4006381333932','123','abcdefgh','4006381333931.0']) {
  test(`rejects invalid GTIN ${gtin}`, () => assert.equal(validateGTIN(gtin).valid, false));
}
for (const [source, value] of [['12,50',12.5],['12.50',12.5],['1234',1234],['1 234,50',1234.5],['1\u00a0234.50',1234.5],['0',0],[' 9,9 ',9.9]]) {
  test(`parses price ${JSON.stringify(source)} without rewriting source`, () => assert.equal(parsePrice(source).value, value));
}
for (const source of ['1,234','1.234','1,234.56','1.234,56','1e3','-5','+5','NaN','Infinity','12 zł','12 34','', '9007199254740993']) {
  test(`rejects ambiguous or invalid price ${JSON.stringify(source)}`, () => assert.equal(parsePrice(source).valid, false));
}
test('validates HTTP syntax only, including local/private hosts, without checking availability', () => {
  for (const url of ['https://example.invalid/p?q=1','http://localhost:3000/p','https://127.0.0.1']) assert.equal(validateHTTPURL(url).valid, true);
  for (const url of ['javascript:alert(1)','ftp://example.com','https:/example.com','https://','https://example.com/a b','https://user:pass@example.com','https://example.com\\x']) assert.equal(validateHTTPURL(url).valid, false);
});
test('audits duplicates, required data and optional validators using actual record numbers', () => {
  const audit = auditTable(fixture(), mapping);
  assert.deepEqual(audit.issues.filter(x=>x.code==='DUPLICATE_SKU').map(x=>x.record), [2,3]);
  assert.ok(audit.issues.some(x=>x.code==='PRICE_AMBIGUOUS' && x.record===3));
  assert.ok(audit.issues.some(x=>x.code==='GTIN_CHECKSUM' && x.record===3));
  assert.ok(audit.issues.some(x=>x.code==='URL_INVALID' && x.record===3));
  const empty = auditTable(parseCSV('sku;nazwa;cena\n;;', ';'), {sku:0,name:1,price:2});
  assert.equal(empty.issues.filter(x=>x.code==='REQUIRED_EMPTY').length, 3);
});
test('rejects audits with incomplete mapping instead of hiding unchecked required fields', () => assert.throws(() => auditTable(fixture(), {sku:0,name:1}), /mapowan/i));
test('trim-only tidy preserves content and provides original/change record details', () => {
  const table = parseCSV(' SKU ;Nazwa;Cena\n 001 ;" Tekst\nwewnątrz ";12,50', ';');
  const tidy = tidyTable(table);
  assert.equal(table.records[0].values[0], ' 001 ');
  assert.equal(tidy.table.records[0].values[0], '001');
  assert.equal(tidy.table.records[0].values[1], 'Tekst\nwewnątrz');
  assert.equal(tidy.changes.length, 3);
  assert.deepEqual(tidy.changes[0], {record:1,column:1,before:' SKU ',after:'SKU'});
});
test('CSV export quotes separators, multiline content and quotes and round-trips', () => {
  const table = parseCSV('sku;nazwa;cena\n001;"A; ""B""\nC";12,50', ';');
  const output = buildCSVExport(table);
  assert.equal(output.blocked, false);
  assert.equal(output.csv, '\uFEFFsku;nazwa;cena\r\n001;"A; ""B""\nC";12,50\r\n');
  assert.deepEqual(parseCSV(output.csv, ';').records[0].values, ['001','A; "B"\nC','12,50']);
});
for (const value of ['=1+1',' +SUM(A1)','-1','@SUM(A1)','\ttext','\rtext','\ntext','＝1','＋1','－1','＠x','  ＝1','\u200b=1']) {
  test(`blocks formula-leading source cell ${JSON.stringify(value)} without altering payload`, () => {
    const table = {headers:['sku','name','price'],delimiter:';',records:[{number:2,line:2,values:['A',value,'1']}]};
    const out = buildCSVExport(table);
    assert.equal(out.blocked, true);
    assert.equal(out.csv, null);
    assert.ok(out.unsafe.some(cell=>cell.record===2 && cell.column===2));
  });
}
test('blocks unsafe headers and source control-prefix even if trim would remove it', () => {
  assert.equal(buildCSVExport(parseCSV('=header;a\nx;y',';')).blocked, true);
  const original = parseCSV('sku;nazwa;cena\nA;"\ttext";1',';');
  assert.equal(buildCSVExport(tidyTable(original).table, original).blocked, true);
});
test('JSON report contains record provenance and remains available when CSV is blocked', () => {
  const table = fixture();
  table.records[0].values[1] = '=1+1';
  const audit = auditTable(table, mapping);
  const report = JSON.parse(buildJSONReport(table, mapping, audit));
  assert.equal(report.schemaVersion, 1);
  assert.equal(report.records, 2);
  assert.equal(report.csvExport.blocked, true);
  assert.ok(report.issues.some(x=>x.record===3 && x.line===3));
  assert.equal(report.mapping.sku.column, 1);
});
