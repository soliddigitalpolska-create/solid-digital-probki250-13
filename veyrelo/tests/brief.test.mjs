import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createBrief, validateBrief, assessBrief, exportMarkdown,
  exportJSON, importJSON, exampleBrief,
} from '../brief/logic.js';

function completeBrief(scenario = 'ceny') {
  const brief = createBrief(scenario);
  assert.ok(brief && typeof brief === 'object', 'Factory must return an editable brief');
  Object.assign(brief, {
    title: 'Porządkowanie cennika',
    goal: 'Ograniczyć liczbę błędów w cenach',
    process: 'Eksport CSV → kontrola → ręczna akceptacja',
    dependencies: 'Plik CSV dostarczony przed startem',
    constraints: 'Bez zapisu do sklepu',
    exclusions: 'Zmiana cen w sklepie i wdrożenie ERP',
    acceptance: [{ metric: 'Błędne ceny po korekcie', operator: 'eq', target: 0, unit: 'rekordów', verification: 'Ponowna walidacja 200 rekordów' }],
    budgetPLN: null,
    deadline: '',
  });
  brief.materials.forEach(item => { item.status = 'ready'; item.note = ''; });
  return brief;
}

test('B01 scenarios produce distinct checklists without filling the user goal', () => {
  for (const [scenario, expectedId] of [['ceny', 'price-sample'], ['integracje', 'system-list'], ['raporty', 'report-sample']]) {
    const brief = createBrief(scenario);
    assert.ok(brief && brief.scenario === scenario, 'Scenario must be retained');
    assert.equal(brief.goal, '');
    assert.ok(brief.materials.some(item => item.id === expectedId));
    assert.ok(brief.materials.every(item => item.status === 'unknown'));
  }
});

test('B01 unknown scenario is rejected instead of silently selecting prices', () => {
  assert.throws(() => createBrief('nieznany'), /scenariusz/i);
});

test('B02 numeric zero is a complete measurable acceptance target', () => {
  assert.equal(assessBrief(completeBrief())?.complete, true);
});

test('B02 a missing target leaves acceptance incomplete', () => {
  const brief = completeBrief(); brief.acceptance[0].target = null;
  assert.ok(assessBrief(brief).missing.some(item => item.field === 'acceptance'));
});

test('B02 a metric without a verification method cannot be counted as complete', () => {
  const brief = completeBrief(); brief.acceptance[0].verification = ' ';
  assert.equal(assessBrief(brief).complete, false);
});

test('B02 every acceptance row must be completed', () => {
  const brief = completeBrief();
  brief.acceptance.push({ metric: '', operator: 'lte', target: null, unit: '', verification: '' });
  assert.equal(assessBrief(brief).complete, false);
});

for (const field of ['dependencies', 'constraints', 'exclusions']) {
  test(`B03/B04 empty ${field} is reported rather than inferred`, () => {
    const brief = completeBrief(); brief[field] = '\n   ';
    assert.ok(assessBrief(brief).missing.some(item => item.field === field));
  });
}

test('B05 a reviewed but missing material makes the brief complete but not ready', () => {
  const brief = completeBrief(); brief.materials[0].status = 'needed';
  const result = assessBrief(brief);
  assert.equal(result.complete, true);
  assert.equal(result.materialsReady, false);
  assert.equal(result.neededMaterials.length, 1);
});

test('B05 an unchecked material is a missing brief field', () => {
  const brief = completeBrief(); brief.materials[0].status = 'unknown';
  assert.ok(assessBrief(brief).missing.some(item => item.field === 'materials'));
});

test('B06 omitted budget and deadline do not reduce completeness', () => {
  const result = assessBrief(completeBrief());
  assert.equal(result?.percent, 100);
  assert.deepEqual(result?.missing, []);
});

test('B06 a valid leap day and zero budget survive export and import', () => {
  const brief = completeBrief(); brief.deadline = '2028-02-29'; brief.budgetPLN = 0;
  const imported = importJSON(exportJSON(brief));
  assert.equal(imported.deadline, '2028-02-29');
  assert.equal(imported.budgetPLN, 0);
});

for (const deadline of ['2026-02-29', '2026-13-01', '2026-11-31', '06.11.2026']) {
  test(`B06 impossible or non-ISO deadline ${deadline} is rejected`, () => {
    const brief = completeBrief(); brief.deadline = deadline;
    assert.throws(() => validateBrief(brief), /termin/i);
  });
}

test('B07 a blank brief has zero completeness and all eight missing sections', () => {
  const result = assessBrief(createBrief('ceny'));
  assert.equal(result?.percent, 0);
  assert.equal(result?.missing?.length, 8);
});

test('B08 an incomplete Markdown export explicitly labels the draft and missing fields', () => {
  const markdown = exportMarkdown(createBrief('ceny'));
  assert.equal(typeof markdown, 'string');
  assert.match(markdown, /SZKIC/);
  assert.match(markdown, /Braki/);
  assert.match(markdown, /Kryteria odbioru/);
});

test('B08 complete Markdown includes boundaries and measurable acceptance', () => {
  const markdown = exportMarkdown(completeBrief());
  assert.match(markdown, /0 rekordów/);
  assert.match(markdown, /Ponowna walidacja 200 rekordów/);
  assert.match(markdown, /Zmiana cen w sklepie i wdrożenie ERP/);
  assert.match(markdown, /Nie podano/);
});

test('B08 untrusted Markdown markup is escaped in exported content', () => {
  const brief = completeBrief(); brief.title = '<script>bad</script> [otwórz](javascript:alert(1))';
  const markdown = exportMarkdown(brief);
  assert.ok(!markdown.includes('<script>'));
  assert.ok(!markdown.includes('[otwórz]('));
});

test('B09 JSON round trip preserves every editable field without changing the original', () => {
  const brief = completeBrief('raporty');
  brief.materials[0].note = 'Plik testowy bez danych osobowych';
  const original = structuredClone(brief);
  const json = exportJSON(brief);
  const envelope = JSON.parse(json);
  assert.equal(envelope.schema, 'veyrelo-brief');
  assert.equal(envelope.version, 1);
  assert.deepEqual(importJSON(json), original);
  assert.deepEqual(brief, original);
});

test('B10 import accepts a leading UTF-8 BOM', () => {
  const imported = importJSON('\uFEFF' + exportJSON(completeBrief()));
  assert.equal(imported.title, 'Porządkowanie cennika');
});

for (const [key, value] of [['schema', 'other-tool'], ['version', 2], ['version', '1']]) {
  test(`B10 import rejects unsupported ${key} ${value}`, () => {
    const envelope = { schema: 'veyrelo-brief', version: 1, brief: completeBrief() };
    envelope[key] = value;
    assert.throws(() => importJSON(JSON.stringify(envelope)), /format|wersj/i);
  });
}

test('B10 import rejects malformed JSON', () => {
  assert.throws(() => importJSON('{broken'), /JSON/i);
});

test('B10 import rejects oversized files before parsing', () => {
  assert.throws(() => importJSON(' '.repeat(131073)), /rozmiar|128/i);
});

test('B10 import rejects a JSON primitive', () => {
  assert.throws(() => importJSON('null'), /obiekt|format/i);
});

test('B10 unexpected envelope fields are rejected', () => {
  const envelope = { schema: 'veyrelo-brief', version: 1, brief: completeBrief(), injected: true };
  assert.throws(() => importJSON(JSON.stringify(envelope)), /pole/i);
});

test('B10 unexpected brief fields are rejected', () => {
  const brief = completeBrief(); brief.extra = true;
  assert.throws(() => importJSON(JSON.stringify({ schema: 'veyrelo-brief', version: 1, brief })), /pole/i);
});

for (const key of ['__proto__', 'constructor', 'prototype']) {
  test(`B10 dangerous key ${key} is rejected at any nesting level`, () => {
    const brief = completeBrief();
    Object.defineProperty(brief.acceptance[0], key, { value: { polluted: true }, enumerable: true });
    const json = JSON.stringify({ schema: 'veyrelo-brief', version: 1, brief });
    assert.throws(() => importJSON(json), /niedozwolon|pole/i);
    assert.equal({}.polluted, undefined);
  });
}

test('B10 strings longer than their limit are rejected rather than truncated', () => {
  const brief = completeBrief(); brief.goal = 'x'.repeat(2001);
  assert.throws(() => validateBrief(brief), /limit|dług/i);
});

test('B10 more than ten criteria are rejected', () => {
  const brief = completeBrief(); brief.acceptance = Array.from({ length: 11 }, () => ({ ...brief.acceptance[0] }));
  assert.throws(() => validateBrief(brief), /kryteri|limit/i);
});

test('B10 checklist IDs cannot be duplicated to fake a complete list', () => {
  const brief = completeBrief(); brief.materials[1].id = brief.materials[0].id;
  assert.throws(() => validateBrief(brief), /materiał|lista/i);
});

for (const invalid of [NaN, Infinity, -1, '1200']) {
  test(`B10 budget rejects nonfinite, negative or wrong typed value ${invalid}`, () => {
    const brief = completeBrief(); brief.budgetPLN = invalid;
    assert.throws(() => validateBrief(brief), /budżet/i);
  });
}

test('B10 imported material status must be from the allowed set', () => {
  const brief = completeBrief(); brief.materials[0].status = true;
  assert.throws(() => validateBrief(brief), /status/i);
});

test('B10 imported acceptance operator must be from the allowed set', () => {
  const brief = completeBrief(); brief.acceptance[0].operator = 'execute';
  assert.throws(() => validateBrief(brief), /operator/i);
});

test('B10 an array coercible to a valid operator is still rejected', () => {
  const brief = completeBrief(); brief.acceptance[0].operator = ['eq'];
  assert.throws(() => validateBrief(brief), /operator/i);
});

test('Fictional sample is labelled and produces a complete draft in each scenario', () => {
  for (const scenario of ['ceny', 'integracje', 'raporty']) {
    const brief = exampleBrief(scenario);
    assert.ok(brief && /FIKCYJNY/.test(brief.title));
    assert.equal(assessBrief(brief).complete, true);
  }
});
