import { calculate, createDecisionNote } from './logic.js';

const form = document.getElementById('calculator-form');
const status = document.getElementById('status');
const errors = document.getElementById('errors');
const results = document.getElementById('results');
const scenarioResults = document.getElementById('scenario-results');
const downloadButton = document.getElementById('download-note');
const moneyAndHours = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 2 });
let latestInputs = null;
let latestSignature = null;

function format(value) {
  return value !== 0 && Math.abs(value) < 0.005
    ? value.toExponential(2).replace('.', ',')
    : moneyAndHours.format(value);
}

function readInputs() {
  const input = id => document.getElementById(id).value;
  return {
    minutesPerTask: input('minutesPerTask'),
    repetitionsPerDay: input('repetitionsPerDay'),
    daysPerMonth: input('daysPerMonth'),
    hourlyRate: input('hourlyRate'),
    monthlyMaintenance: input('monthlyMaintenance'),
    implementationCost: input('implementationCost'),
    reductions: [input('reduction1'), input('reduction2'), input('reduction3')],
  };
}

function clearErrors() {
  errors.hidden = true;
  errors.replaceChildren();
  form.querySelectorAll('[aria-invalid]').forEach(input => input.removeAttribute('aria-invalid'));
}

function invalidate() {
  latestInputs = null;
  latestSignature = null;
  downloadButton.disabled = true;
  results.hidden = true;
  scenarioResults.replaceChildren();
  document.getElementById('workload-result').textContent = '';
}

function showErrors(items) {
  const heading = document.createElement('p');
  heading.textContent = 'Popraw dane, aby otrzymać wynik:';
  const list = document.createElement('ul');
  items.forEach(error => {
    const item = document.createElement('li');
    const field = document.getElementById(error.field);
    if (field) {
      field.setAttribute('aria-invalid', 'true');
      const link = document.createElement('a');
      link.href = `#${error.field}`;
      link.textContent = error.message;
      link.addEventListener('click', event => {
        event.preventDefault();
        field.focus();
      });
      item.append(link);
    } else {
      item.textContent = error.message;
    }
    list.append(item);
  });
  errors.replaceChildren(heading, list);
  errors.hidden = false;
  errors.focus();
  status.textContent = 'Nie obliczono wyniku. Dane wymagają poprawy.';
}

function renderScenario(row, index) {
  const card = document.createElement('article');
  card.className = 'scenario-card';
  const heading = document.createElement('h3');
  heading.textContent = `Scenariusz ${index + 1}`;
  const percent = document.createElement('p');
  percent.className = 'scenario-reduction';
  percent.textContent = `${format(row.reductionPercent)}% redukcji`;
  const definitions = document.createElement('dl');
  const values = [
    ['Uwolniony czas / miesiąc', `${format(row.releasedHours)} h`],
    ['Pozostała praca / miesiąc', `${format(row.remainingHours)} h`],
    ['Wartość uwolnionego czasu / miesiąc', `${format(row.timeValuePLN)} PLN`],
    ['Wartość czasu minus utrzymanie / miesiąc', `${format(row.monthlyPotentialPLN)} PLN`, row.monthlyPotentialPLN < 0],
    ['Pokrycie kosztu wdrożenia', row.costCoverageMonths === null ? 'Niedostępne' : `${format(row.costCoverageMonths)} mies.`],
  ];
  values.forEach(([label, value, negative]) => {
    const term = document.createElement('dt');
    term.textContent = label;
    const detail = document.createElement('dd');
    detail.textContent = value;
    if (negative) detail.className = 'negative';
    definitions.append(term, detail);
  });
  const note = document.createElement('p');
  note.className = 'coverage-note';
  note.textContent = row.costCoverageMonths === null
    ? 'Wartość czasu po odjęciu utrzymania jest równa lub mniejsza od zera. Brak dodatniej podstawy do obliczenia miesięcy.'
    : 'Porównanie wartości czasu z kosztem. Nie oznacza zwrotu gotówki ani gwarantowanego zysku.';
  card.append(heading, percent, definitions, note);
  return card;
}

form.addEventListener('input', () => {
  invalidate();
  clearErrors();
  status.textContent = 'Dane zmienione. Oblicz ponownie, aby zobaczyć aktualny wynik i pobrać notatkę.';
});

form.addEventListener('submit', event => {
  event.preventDefault();
  invalidate();
  clearErrors();
  const raw = readInputs();
  const result = calculate(raw);
  if (!result.ok) {
    showErrors(result.errors);
    return;
  }
  latestInputs = result.inputs;
  latestSignature = JSON.stringify(raw);
  const { dailyMinutes, monthlyMinutes, monthlyHours } = result.workload;
  document.getElementById('workload-result').textContent = `Obciążenie bazowe: ${format(dailyMinutes)} min dziennie, ${format(monthlyMinutes)} min miesięcznie, czyli ${format(monthlyHours)} godzin miesięcznie.`;
  scenarioResults.replaceChildren(...result.scenarios.map(renderScenario));
  results.hidden = false;
  downloadButton.disabled = false;
  status.textContent = 'Obliczono trzy scenariusze. Wyniki są poniżej; notatka jest gotowa do pobrania.';
});

downloadButton.addEventListener('click', () => {
  if (!latestInputs || latestSignature !== JSON.stringify(readInputs())) {
    invalidate();
    status.textContent = 'Oblicz aktualne dane przed pobraniem notatki.';
    return;
  }
  const note = createDecisionNote(latestInputs);
  if (!note.ok) {
    invalidate();
    showErrors(note.errors);
    return;
  }
  try {
    const blob = new Blob([note.markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'veyrelo-notatka-automatyzacja.md';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = 'Przekazano notatkę do pobrania w przeglądarce. Dane pozostają lokalne.';
  } catch {
    status.textContent = 'Przeglądarka nie rozpoczęła pobierania. Spróbuj ponownie i sprawdź jej ustawienia pobierania.';
  }
});
