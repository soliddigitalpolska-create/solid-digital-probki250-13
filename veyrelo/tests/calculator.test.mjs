import test from 'node:test';
import assert from 'node:assert/strict';
import { calculate, createDecisionNote } from '../kalkulator/logic.js';

const base = {
  minutesPerTask: 12,
  repetitionsPerDay: 10,
  daysPerMonth: 20,
  hourlyRate: 100,
  monthlyMaintenance: 100,
  implementationCost: 2400,
  reductions: [20, 40, 60],
};

// Catches wrong minute/hour conversion, reduction basis, cost subtraction or division.
test('calculates workload and three independently checked scenarios', () => {
  const result = calculate(base);
  assert.equal(result?.ok, true);
  assert.deepEqual(result.workload, { dailyMinutes: 120, monthlyMinutes: 2400, monthlyHours: 40 });
  assert.deepEqual(result.scenarios, [
    { reductionPercent: 20, releasedHours: 8, remainingHours: 32, timeValuePLN: 800, monthlyPotentialPLN: 700, costCoverageMonths: 3.4285714285714284 },
    { reductionPercent: 40, releasedHours: 16, remainingHours: 24, timeValuePLN: 1600, monthlyPotentialPLN: 1500, costCoverageMonths: 1.6 },
    { reductionPercent: 60, releasedHours: 24, remainingHours: 16, timeValuePLN: 2400, monthlyPotentialPLN: 2300, costCoverageMonths: 1.0434782608695652 },
  ]);
});

// Catches rounding hours before using the hourly value or implementation coverage.
test('preserves fractional workload through the calculation', () => {
  const result = calculate({ ...base, minutesPerTask: 1, repetitionsPerDay: 1, daysPerMonth: 1, reductions: [25, 50, 100], hourlyRate: 60, monthlyMaintenance: 0, implementationCost: 1 });
  assert.equal(result?.ok, true);
  assert.equal(result.scenarios[0].timeValuePLN, 0.25);
  assert.equal(result.scenarios[0].costCoverageMonths, 4);
});

// Catches empty coercion to zero or invalid normalization of Polish decimal input.
test('accepts decimal strings with a Polish comma without changing the scenario order', () => {
  const result = calculate({ ...base, minutesPerTask: ' 1,5 ', repetitionsPerDay: '2', reductions: ['60', '0', '100'] });
  assert.equal(result?.ok, true);
  assert.equal(result.workload.monthlyHours, 1);
  assert.deepEqual(result.scenarios.map(row => row.reductionPercent), [60, 0, 100]);
});

// Catches fabricated coverage when the denominator is negative or zero.
test('leaves cost coverage unavailable for nonpositive monthly potential', () => {
  const result = calculate({ ...base, reductions: [0, 25, 50], monthlyMaintenance: 1000 });
  assert.equal(result?.ok, true);
  assert.deepEqual(result.scenarios.map(row => row.monthlyPotentialPLN), [-1000, 0, 1000]);
  assert.deepEqual(result.scenarios.map(row => row.costCoverageMonths), [null, null, 2.4]);
});

// Catches a false division result for a zero cost with no positive benefit.
test('zero implementation cost yields zero months only with positive potential', () => {
  const result = calculate({ ...base, implementationCost: 0, reductions: [0, 25, 50], monthlyMaintenance: 1000 });
  assert.equal(result?.ok, true);
  assert.deepEqual(result.scenarios.map(row => row.costCoverageMonths), [null, null, 0]);
});

// Catches NaN from zero workload, rate, or all-zero input combinations.
test('zero workload and zero valuation remain finite with no cost coverage', () => {
  for (const change of [{ minutesPerTask: 0 }, { repetitionsPerDay: 0 }, { daysPerMonth: 0 }, { hourlyRate: 0 }]) {
    const result = calculate({ ...base, ...change, monthlyMaintenance: 0 });
    assert.equal(result?.ok, true);
    assert.deepEqual(result.scenarios.map(row => row.timeValuePLN), [0, 0, 0]);
    assert.deepEqual(result.scenarios.map(row => row.costCoverageMonths), [null, null, null]);
  }
});

// Catches acceptance of missing, NaN, infinite, negative or ambiguous values.
test('rejects invalid numeric inputs instead of returning a plausible total', () => {
  for (const value of [undefined, null, '', ' ', '1.2.3', '1,000.50', '1e3', NaN, Infinity, -Infinity, -1, true, {}, []]) {
    const result = calculate({ ...base, minutesPerTask: value });
    assert.equal(result?.ok, false, `Rejected ${String(value)}`);
    assert.ok(result.errors.some(error => error.field === 'minutesPerTask'));
  }
});

// Catches omitted domain limits and silent scenario truncation/padding.
test('enforces input ranges and exactly three percentages', () => {
  for (const change of [
    { minutesPerTask: 1441 }, { repetitionsPerDay: 1000001 },
    { daysPerMonth: 32 }, { daysPerMonth: 20.5 },
    { hourlyRate: 1e12 + 1 }, { monthlyMaintenance: -1 }, { implementationCost: -1 },
    { reductions: [] }, { reductions: [10, 20] }, { reductions: [10, 20, 30, 40] },
    { reductions: [0, 50, 101] }, { reductions: [0, -1, 100] }, { reductions: [0, NaN, 100] },
  ]) {
    assert.equal(calculate({ ...base, ...change })?.ok, false, JSON.stringify(change));
  }
});

// Catches accepting huge finite intermediate outputs outside safe arithmetic range.
test('rejects unsafe monetary totals and overflowing coverage rather than emitting Infinity', () => {
  for (const change of [
    { minutesPerTask: 1440, repetitionsPerDay: 1e6, daysPerMonth: 31, hourlyRate: 1e12 },
    { hourlyRate: 1e-300, monthlyMaintenance: 0, implementationCost: 1e12 },
  ]) {
    const result = calculate({ ...base, ...change });
    assert.equal(result?.ok, false);
    assert.ok(result.errors.some(error => error.field === 'calculation'));
  }
});

// Catches silently rounding tiny nonzero work down to zero.
test('rejects arithmetic underflow instead of presenting zero workload', () => {
  const result = calculate({ ...base, minutesPerTask: Number.MIN_VALUE, repetitionsPerDay: 0.1 });
  assert.equal(result?.ok, false);
  assert.ok(result.errors.some(error => error.field === 'calculation'));
});

// Catches conversion of a nonzero decimal string into a misleading zero.
test('rejects numeric strings too small to represent', () => {
  const result = calculate({ ...base, minutesPerTask: `0.${'0'.repeat(400)}1` });
  assert.equal(result?.ok, false);
  assert.ok(result.errors.some(error => error.field === 'minutesPerTask'));
});

// Catches omitted inputs, dropped scenarios, or a lossy export that differs from the calculation.
test('exports every assumption and unrounded result in a standalone Markdown note', () => {
  const note = createDecisionNote(base);
  assert.equal(note?.ok, true);
  for (const pattern of [
    /Minuty na zadanie: 12\b/, /Powtórzenia dziennie: 10\b/, /Dni w miesiącu: 20\b/,
    /Wartość godziny: 100 PLN/, /Miesięczny koszt utrzymania: 100 PLN/,
    /Jednorazowy koszt wdrożenia: 2400 PLN/, /Redukcje pracy: 20%, 40%, 60%/,
    /Minuty dziennie: 120\b/, /Minuty miesięcznie: 2400\b/, /Godziny miesięcznie: 40\b/,
  ]) assert.match(note.markdown, pattern);
  assert.ok(note.markdown.includes('| 1 | 20 | 8 | 32 | 800 | 700 | 3.4285714285714284 |'));
  assert.ok(note.markdown.includes('| 2 | 40 | 16 | 24 | 1600 | 1500 | 1.6 |'));
  assert.ok(note.markdown.includes('| 3 | 60 | 24 | 16 | 2400 | 2300 | 1.0434782608695652 |'));
  assert.match(note.markdown, /oszczędności gotówkowe/);
  assert.match(note.markdown, /VAT/);
  assert.match(note.markdown, /przychodu|przychodem/);
  assert.match(note.markdown, /zysku|zyskiem/);
  assert.match(note.markdown, /ilustracyjne/);
  assert.match(note.markdown, /minuty na zadanie × powtórzenia dziennie × dni w miesiącu/);
});

// Catches exporting invalid numbers or skipping recalculation at the export boundary.
test('refuses a decision note for invalid input', () => {
  const note = createDecisionNote({ ...base, hourlyRate: Infinity });
  assert.equal(note?.ok, false);
  assert.equal(note.markdown, undefined);
  assert.ok(note.errors.some(error => error.field === 'hourlyRate'));
});

// Catches a textual Infinity or fictitious month count for a nonpositive denominator.
test('export explicitly marks unavailable coverage for negative monthly potential', () => {
  const note = createDecisionNote({ ...base, reductions: [0, 0, 0] });
  assert.equal(note?.ok, true);
  assert.ok(note.markdown.includes('| 1 | 0 | 0 | 40 | 0 | -100 | niedostępne |'));
  assert.doesNotMatch(note.markdown, /Infinity|NaN/);
});
