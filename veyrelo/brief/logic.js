const freeze = value => {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
};

export const LIMITS = freeze({ jsonBytes: 131072, criteria: 10, longText: 2000, money: 10000000, target: 1000000000 });
export const SCENARIOS = freeze({
  ceny: {
    label: 'Ceny i cenniki',
    description: 'Uporządkuj źródła cen, reguły przeliczeń i sposób zatwierdzania zmian.',
    goalHint: 'Np. wykrywać błędne ceny przed importem do sklepu.',
    metricHint: 'Np. liczba błędnych cen w próbce',
    materials: [
      { id: 'price-sample', label: 'Przykładowy cennik bez danych osobowych' },
      { id: 'price-rules', label: 'Reguły cen, walut i zaokrągleń' },
      { id: 'price-output', label: 'Wzór oczekiwanego pliku wynikowego' },
      { id: 'price-approval', label: 'Opis procesu akceptacji zmian' },
    ],
  },
  integracje: {
    label: 'Integracje systemów',
    description: 'Opisz kierunek danych, zdarzenia uruchamiające i obsługę wyjątków.',
    goalHint: 'Np. przenosić zatwierdzone zamówienia między dwoma systemami.',
    metricHint: 'Np. czas przekazania testowego zamówienia',
    materials: [
      { id: 'system-list', label: 'Lista systemów i kierunków przepływu' },
      { id: 'integration-docs', label: 'Dokumentacja integracji i dostępnych operacji' },
      { id: 'integration-sample', label: 'Anonimowe przykłady wejścia i wyniku' },
      { id: 'integration-test', label: 'Opis środowiska testowego i uprawnień, bez haseł' },
    ],
  },
  raporty: {
    label: 'Raporty i zestawienia',
    description: 'Ustal definicje wskaźników, źródła danych i rytm aktualizacji raportu.',
    goalHint: 'Np. co tydzień porównywać sprzedaż z uzgodnionymi celami.',
    metricHint: 'Np. różnica sum raportu i pliku źródłowego',
    materials: [
      { id: 'report-sample', label: 'Anonimowa próbka danych źródłowych' },
      { id: 'report-metrics', label: 'Definicje wskaźników i filtrów' },
      { id: 'report-layout', label: 'Wzór lub szkic oczekiwanego raportu' },
      { id: 'report-schedule', label: 'Zasady aktualizacji i kontroli wyniku' },
    ],
  },
});

const briefKeys = ['scenario', 'title', 'goal', 'process', 'acceptance', 'dependencies', 'constraints', 'exclusions', 'materials', 'budgetPLN', 'deadline'];
const operators = { eq: '=', lte: '≤', gte: '≥' };
const statuses = { unknown: 'Do ustalenia', ready: 'Gotowe', needed: 'Do dostarczenia', 'not-applicable': 'Nie dotyczy' };
const dangerous = new Set(['__proto__', 'constructor', 'prototype']);

function safeTree(value, depth = 0) {
  if (!value || typeof value !== 'object') return;
  if (depth > 8) throw new Error('Niedozwolona głębokość danych.');
  if (!Array.isArray(value) && Object.getPrototypeOf(value) !== Object.prototype) throw new Error('Wymagany jest zwykły obiekt danych.');
  if (Object.keys(value).length > 100) throw new Error('Przekroczono limit elementów.');
  for (const [key, child] of Object.entries(value)) {
    if (dangerous.has(key)) throw new Error('Niedozwolone pole w pliku JSON.');
    safeTree(child, depth + 1);
  }
}

function exactKeys(value, expected, label) {
  if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error(`${label}: wymagany obiekt.`);
  const keys = Object.keys(value);
  if (keys.length !== expected.length || keys.some(key => !expected.includes(key))) throw new Error(`${label}: brakujące lub nieznane pole.`);
}

function string(value, max, label) {
  if (typeof value !== 'string') throw new Error(`${label}: wymagany tekst.`);
  if (value.length > max) throw new Error(`${label}: przekroczony limit długości ${max} znaków.`);
}

function numberOrNull(value, max, label) {
  if (value !== null && (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > max)) {
    throw new Error(`${label}: wpisz liczbę od 0 do ${max} lub pozostaw puste pole.`);
  }
}

function scenarioConfig(scenario) {
  if (typeof scenario !== 'string' || !Object.hasOwn(SCENARIOS, scenario)) throw new Error('Nieznany scenariusz briefu.');
  return SCENARIOS[scenario];
}

export function createBrief(scenario = 'ceny') {
  const config = scenarioConfig(scenario);
  return {
    scenario, title: '', goal: '', process: '',
    acceptance: [{ metric: '', operator: 'lte', target: null, unit: '', verification: '' }],
    dependencies: '', constraints: '', exclusions: '',
    materials: config.materials.map(item => ({ id: item.id, status: 'unknown', note: '' })),
    budgetPLN: null, deadline: '',
  };
}

export function validateBrief(brief) {
  safeTree(brief);
  exactKeys(brief, briefKeys, 'Brief');
  const config = scenarioConfig(brief.scenario);
  string(brief.title, 160, 'Nazwa projektu');
  for (const key of ['goal', 'process', 'dependencies', 'constraints', 'exclusions']) string(brief[key], LIMITS.longText, key);
  if (!Array.isArray(brief.acceptance) || brief.acceptance.length > LIMITS.criteria) throw new Error('Lista kryteriów: limit 10 kryteriów.');
  for (const criterion of brief.acceptance) {
    exactKeys(criterion, ['metric', 'operator', 'target', 'unit', 'verification'], 'Kryterium');
    string(criterion.metric, 120, 'Metryka');
    string(criterion.unit, 60, 'Jednostka');
    string(criterion.verification, 500, 'Sprawdzenie');
    if (typeof criterion.operator !== 'string' || !Object.hasOwn(operators, criterion.operator)) throw new Error('Nieznany operator kryterium.');
    numberOrNull(criterion.target, LIMITS.target, 'Cel kryterium');
  }
  if (!Array.isArray(brief.materials) || brief.materials.length !== config.materials.length) throw new Error('Niepełna lista materiałów.');
  const ids = new Set();
  for (const material of brief.materials) {
    exactKeys(material, ['id', 'status', 'note'], 'Materiał');
    if (typeof material.id !== 'string' || !config.materials.some(item => item.id === material.id) || ids.has(material.id)) throw new Error('Nieprawidłowa lista materiałów.');
    ids.add(material.id);
    if (typeof material.status !== 'string' || !Object.hasOwn(statuses, material.status)) throw new Error('Nieprawidłowy status materiału.');
    string(material.note, 500, 'Notatka do materiału');
  }
  numberOrNull(brief.budgetPLN, LIMITS.money, 'Budżet');
  string(brief.deadline, 10, 'Termin');
  if (brief.deadline !== '') {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(brief.deadline);
    if (!match || Number(match[1]) < 1900 || Number(match[1]) > 9999) throw new Error('Termin: podaj poprawną datę RRRR-MM-DD.');
    const date = new Date(`${brief.deadline}T12:00:00Z`);
    if (Number.isNaN(date.valueOf()) || date.toISOString().slice(0, 10) !== brief.deadline) throw new Error('Termin: taka data nie istnieje.');
  }
  return brief;
}

export function assessBrief(brief) {
  validateBrief(brief);
  const checks = [
    ['title', 'Nazwa projektu', Boolean(brief.title.trim())],
    ['goal', 'Cel i problem', Boolean(brief.goal.trim())],
    ['process', 'Proces: wejście, działanie i wynik', Boolean(brief.process.trim())],
    ['acceptance', 'Kryteria odbioru: metryka, liczba, jednostka i sprawdzenie', brief.acceptance.length > 0 && brief.acceptance.every(row => row.metric.trim() && row.target !== null && row.unit.trim() && row.verification.trim())],
    ['dependencies', 'Zależności od innych działań', Boolean(brief.dependencies.trim())],
    ['constraints', 'Ograniczenia procesu', Boolean(brief.constraints.trim())],
    ['exclusions', 'Jawne wyłączenia zakresu', Boolean(brief.exclusions.trim())],
    ['materials', 'Status każdego materiału', brief.materials.every(item => item.status !== 'unknown')],
  ];
  const missing = checks.filter(([, , complete]) => !complete).map(([field, label]) => ({ field, label }));
  const config = scenarioConfig(brief.scenario);
  const neededMaterials = brief.materials.filter(item => item.status === 'needed' || item.status === 'unknown').map(item => ({ ...item, label: config.materials.find(material => material.id === item.id).label }));
  return { complete: missing.length === 0, percent: Math.round((checks.length - missing.length) / checks.length * 100), missing, materialsReady: neededMaterials.length === 0, neededMaterials };
}

function markdownText(value) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/[\\`*_{}\[\]()#+.!|~-]/g, '\\$&');
}

export function exportMarkdown(brief) {
  const result = assessBrief(brief);
  const config = scenarioConfig(brief.scenario);
  const text = value => value.trim() ? markdownText(value) : 'Nie podano';
  const lines = [
    '# Brief Veyrelo', '',
    `**Status: ${result.complete ? 'KOMPLETNY OPIS' : 'SZKIC — NIEKOMPLETNY'} (${result.percent}%)**`,
    'Kompletność oznacza opisanie zakresu. Nie jest akceptacją zlecenia ani potwierdzeniem dostarczenia materiałów.', '',
    `## ${text(brief.title)}`, `Scenariusz: ${config.label}`, '',
    '## Cel i problem', text(brief.goal), '',
    '## Proces: wejście → działanie → wynik', text(brief.process), '',
    '## Kryteria odbioru',
  ];
  if (!brief.acceptance.length) lines.push('Nie podano');
  brief.acceptance.forEach((row, index) => {
    lines.push(`${index + 1}. ${text(row.metric)}: ${operators[row.operator]} ${row.target === null ? '[brak liczby]' : row.target} ${text(row.unit)}`, `   Sprawdzenie: ${text(row.verification)}`);
  });
  for (const [heading, field] of [['Zależności', 'dependencies'], ['Ograniczenia', 'constraints'], ['Poza zakresem', 'exclusions']]) lines.push('', `## ${heading}`, text(brief[field]));
  lines.push('', '## Materiały do rozpoczęcia');
  for (const material of brief.materials) {
    const label = config.materials.find(item => item.id === material.id).label;
    lines.push(`- ${label}: **${statuses[material.status]}**${material.note.trim() ? ` — ${text(material.note)}` : ''}`);
  }
  lines.push('', `Gotowość materiałów: ${result.materialsReady ? 'wszystkie oznaczono jako gotowe lub nie dotyczą zakresu' : `${result.neededMaterials.length} do dostarczenia lub ustalenia`}.`, '',
    '## Opcjonalne ograniczenia',
    `Budżet: ${brief.budgetPLN === null ? 'Nie podano' : `${brief.budgetPLN.toFixed(2)} PLN (deklarowany limit; nie wycena)`}`,
    `Termin: ${brief.deadline || 'Nie podano'}`, '', '## Braki');
  lines.push(...(result.missing.length ? result.missing.map(item => `- ${item.label}`) : ['Brak brakujących sekcji.']));
  lines.push('', 'Plik utworzony lokalnie w narzędziu Veyrelo. Formularz nie wysyła danych.');
  return lines.join('\n') + '\n';
}

export function exportJSON(brief) {
  validateBrief(brief);
  return JSON.stringify({ schema: 'veyrelo-brief', version: 1, brief }, null, 2) + '\n';
}

export function importJSON(source) {
  if (typeof source !== 'string') throw new Error('Plik JSON musi zawierać tekst.');
  if (new TextEncoder().encode(source).length > LIMITS.jsonBytes) throw new Error('Przekroczono maksymalny rozmiar pliku: 128 KiB.');
  let envelope;
  try {
    envelope = JSON.parse(source.replace(/^\uFEFF/, ''));
  } catch {
    throw new Error('Niepoprawna składnia JSON. Wybierz plik wyeksportowany przez ten brief.');
  }
  safeTree(envelope);
  exactKeys(envelope, ['schema', 'version', 'brief'], 'Format JSON');
  if (envelope.schema !== 'veyrelo-brief' || envelope.version !== 1) throw new Error('Nieobsługiwany format lub wersja briefu. Wymagana wersja 1.');
  validateBrief(envelope.brief);
  return envelope.brief;
}

export function exampleBrief(scenario = 'ceny') {
  const brief = createBrief(scenario);
  const examples = {
    ceny: { title: 'Kontrola cennika', goal: 'Wykryć nieprawidłowe ceny przed ręcznym importem.', process: 'CSV z 200 produktami → sprawdzenie cen i walut → raport błędów do akceptacji.', metric: 'Błędne ceny w poprawionej próbce', target: 0, unit: 'rekordów', verification: 'Ponowna walidacja tych samych 200 rekordów.' },
    integracje: { title: 'Przepływ zamówień', goal: 'Przekazywać zatwierdzone zamówienia w środowisku testowym.', process: 'Zatwierdzenie zamówienia w systemie A → mapowanie danych → wpis w systemie B.', metric: 'Czas przekazania testowego zamówienia', target: 60, unit: 'sekund', verification: 'Pomiar 20 prób na uzgodnionym środowisku testowym.' },
    raporty: { title: 'Tygodniowe zestawienie', goal: 'Porównywać sprzedaż z uzgodnionymi celami.', process: 'Anonimowy CSV → sumowanie według tygodnia → raport z trzema wskaźnikami.', metric: 'Różnica sum raportu i źródła', target: 0.01, unit: 'PLN', verification: 'Porównanie sum z ręcznym zestawieniem dla 4 tygodni.' },
  };
  const example = examples[scenario];
  brief.title = `PRZYKŁAD FIKCYJNY — ${example.title}`;
  brief.goal = example.goal;
  brief.process = example.process;
  brief.acceptance = [{ metric: example.metric, operator: 'lte', target: example.target, unit: example.unit, verification: example.verification }];
  brief.dependencies = 'Dostarczenie próbki danych oraz ustalenie reguł przed rozpoczęciem prac.';
  brief.constraints = 'Praca na danych testowych. Wynik wymaga ręcznego sprawdzenia.';
  brief.exclusions = 'Uruchomienie na produkcji, utrzymanie i nowe funkcje poza opisanym procesem.';
  brief.materials.forEach((item, index) => { item.status = index === 0 ? 'ready' : 'needed'; item.note = 'Fikcyjny status do demonstracji formularza.'; });
  return brief;
}
