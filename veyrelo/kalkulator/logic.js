const fields = {
  minutesPerTask: { label: 'Minuty na zadanie', max: 1440 },
  repetitionsPerDay: { label: 'Powtórzenia dziennie', max: 1000000 },
  daysPerMonth: { label: 'Dni w miesiącu', max: 31, integer: true },
  hourlyRate: { label: 'Wartość godziny', max: 1000000000000 },
  monthlyMaintenance: { label: 'Miesięczny koszt utrzymania', max: 1000000000000 },
  implementationCost: { label: 'Jednorazowy koszt wdrożenia', max: 1000000000000 },
};

function parseNumber(value) {
  if (typeof value === 'number') return value;
  if (typeof value !== 'string') return NaN;
  const trimmed = value.trim();
  if (!/^(?:\d+(?:[.,]\d+)?|[.,]\d+)$/.test(trimmed)) return NaN;
  const number = Number(trimmed.replace(',', '.'));
  return number === 0 && /[1-9]/.test(trimmed) ? NaN : number;
}

function validate(raw) {
  const errors = [];
  const inputs = {};
  for (const [field, rule] of Object.entries(fields)) {
    const value = parseNumber(raw?.[field]);
    if (!Number.isFinite(value) || value < 0 || value > rule.max || (rule.integer && !Number.isInteger(value))) {
      errors.push({ field, message: `${rule.label}: wpisz ${rule.integer ? 'całkowitą ' : ''}liczbę od 0 do ${rule.max}.` });
    } else {
      inputs[field] = value;
    }
  }
  if (!Array.isArray(raw?.reductions) || raw.reductions.length !== 3) {
    errors.push({ field: 'reductions', message: 'Podaj dokładnie trzy scenariusze ograniczenia pracy.' });
  } else {
    inputs.reductions = raw.reductions.map((value, index) => {
      const number = parseNumber(value);
      if (!Number.isFinite(number) || number < 0 || number > 100) {
        errors.push({ field: `reduction${index + 1}`, message: `Scenariusz ${index + 1}: wpisz procent od 0 do 100.` });
      }
      return number;
    });
  }
  return { errors, inputs };
}

function checked(value, unexpectedlyZero = false) {
  if (!Number.isFinite(value) || Math.abs(value) > Number.MAX_SAFE_INTEGER || unexpectedlyZero) {
    throw new RangeError('Unsafe calculation');
  }
  return Object.is(value, -0) ? 0 : value;
}

function multiply(a, b) {
  const value = a * b;
  return checked(value, a > 0 && b > 0 && value === 0);
}

function divide(a, b) {
  const value = a / b;
  return checked(value, a > 0 && value === 0);
}

export function calculate(raw) {
  const { errors, inputs } = validate(raw);
  if (errors.length) return { ok: false, errors };
  try {
    const dailyMinutes = multiply(inputs.minutesPerTask, inputs.repetitionsPerDay);
    const monthlyMinutes = multiply(dailyMinutes, inputs.daysPerMonth);
    const monthlyHours = divide(monthlyMinutes, 60);
    const scenarios = inputs.reductions.map(reductionPercent => {
      const releasedHours = multiply(monthlyHours, divide(reductionPercent, 100));
      const remainingHours = checked(monthlyHours - releasedHours);
      const timeValuePLN = multiply(releasedHours, inputs.hourlyRate);
      const monthlyPotentialPLN = checked(timeValuePLN - inputs.monthlyMaintenance);
      const costCoverageMonths = monthlyPotentialPLN > 0 ? divide(inputs.implementationCost, monthlyPotentialPLN) : null;
      return { reductionPercent, releasedHours, remainingHours, timeValuePLN, monthlyPotentialPLN, costCoverageMonths };
    });
    return { ok: true, inputs, workload: { dailyMinutes, monthlyMinutes, monthlyHours }, scenarios };
  } catch (error) {
    if (!(error instanceof RangeError)) throw error;
    return { ok: false, errors: [{ field: 'calculation', message: 'Dane dają wynik poza bezpiecznym zakresem obliczeń (zbyt duży lub zbyt mały). Zmień skalę założeń.' }] };
  }
}

export function createDecisionNote(raw) {
  const result = calculate(raw);
  if (!result.ok) return result;
  const { inputs, workload, scenarios } = result;
  const rows = scenarios.map((row, index) => `| ${index + 1} | ${row.reductionPercent} | ${row.releasedHours} | ${row.remainingHours} | ${row.timeValuePLN} | ${row.monthlyPotentialPLN} | ${row.costCoverageMonths ?? 'niedostępne'} |`);
  return {
    ok: true,
    markdown: [
      '# Veyrelo — notatka decyzyjna o automatyzacji',
      '',
      '## Założenia użytkownika',
      '',
      `- Minuty na zadanie: ${inputs.minutesPerTask}`,
      `- Powtórzenia dziennie: ${inputs.repetitionsPerDay}`,
      `- Dni w miesiącu: ${inputs.daysPerMonth}`,
      `- Wartość godziny: ${inputs.hourlyRate} PLN`,
      `- Miesięczny koszt utrzymania: ${inputs.monthlyMaintenance} PLN`,
      `- Jednorazowy koszt wdrożenia: ${inputs.implementationCost} PLN`,
      `- Redukcje pracy: ${inputs.reductions.map(value => `${value}%`).join(', ')}`,
      '- Wszystkie kwoty podane przez użytkownika oznaczają całkowite wartości w PLN, według jednej, spójnej podstawy kosztowej. Kalkulator nie dolicza ani nie odlicza VAT.',
      '',
      '## Obciążenie bazowe',
      '',
      `- Minuty dziennie: ${workload.dailyMinutes}`,
      `- Minuty miesięcznie: ${workload.monthlyMinutes}`,
      `- Godziny miesięcznie: ${workload.monthlyHours}`,
      '',
      '## Wyniki scenariuszy na miesiąc',
      '',
      '| Scenariusz | Redukcja (%) | Uwolniony czas (h) | Pozostała praca (h) | Wartość czasu (PLN) | Wartość czasu minus utrzymanie (PLN) | Pokrycie kosztu wdrożenia (mies.) |',
      '| --- | --- | --- | --- | --- | --- | --- |',
      ...rows,
      '',
      '## Wzory',
      '',
      '- Minuty miesięcznie = minuty na zadanie × powtórzenia dziennie × dni w miesiącu.',
      '- Godziny miesięcznie = minuty miesięcznie / 60.',
      '- Uwolniony czas = godziny miesięcznie × redukcja / 100.',
      '- Pozostała praca = godziny miesięcznie − uwolniony czas.',
      '- Wartość uwolnionego czasu = uwolniony czas × wartość godziny.',
      '- Potencjał miesięczny = wartość uwolnionego czasu − miesięczny koszt utrzymania.',
      '- Pokrycie kosztu wdrożenia = jednorazowy koszt wdrożenia / dodatni potencjał miesięczny. Dla potencjału ≤ 0 wynik jest niedostępny; zerowy koszt wdrożenia daje 0 miesięcy wyłącznie przy dodatnim potencjale.',
      '',
      '## Ograniczenia i interpretacja',
      '',
      '- Wartość uwolnionego czasu nie oznacza, że powstaną oszczędności gotówkowe. Nie jest przychodem ani zyskiem i nie gwarantuje zwrotu pieniędzy.',
      '- Domyślne scenariusze 20%, 40% i 60% są wyłącznie ilustracyjne. Nie pochodzą z pomiarów ani z obietnicy skuteczności. Każdy procent można zmienić.',
      '- Pokrycie kosztu jest porównaniem wartości czasu z kosztem przy stałych założeniach; nie jest prognozą przepływów pieniężnych.',
      '- Model zakłada stałą liczbę zadań, wartość godziny i koszt utrzymania oraz natychmiastowe osiągnięcie podanej redukcji. Nie uwzględnia wdrażania zespołu, ryzyka błędów, przestojów, zmian jakości, sezonowości, dyskonta ani innych kosztów, których użytkownik nie ujął.',
      '- Obciążenie może obejmować cały zespół. Powtórzenia dziennie mogą być średnią; liczba dni musi być całkowita od 0 do 31.',
      '- Zakresy: 0–1440 minut na zadanie; 0–1000000 powtórzeń dziennie; 0–1000000000000 PLN dla każdej kwoty; trzy redukcje od 0% do 100%. Wyniki spoza bezpiecznego zakresu liczb są odrzucane.',
      '- Obliczenia używają liczb zmiennoprzecinkowych bez celowego zaokrąglania etapów. Ekran zaokrągla prezentację; eksport zachowuje wartości obliczone, więc mogą wystąpić typowe drobne różnice reprezentacji dziesiętnej.',
      '- Przed decyzją zmierz czas reprezentatywnej próbki zadań, potwierdź koszty i sprawdź redukcję w pilotażu. Sposób wykorzystania odzyskanych godzin wymaga osobnej decyzji.',
      '- Notatka powstaje lokalnie w przeglądarce. Dane nie są wysyłane ani automatycznie zapisywane; pobranie pliku jest działaniem użytkownika.',
      '',
    ].join('\n'),
  };
}
