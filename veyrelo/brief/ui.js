import {
  LIMITS, SCENARIOS, createBrief, validateBrief, assessBrief,
  exportMarkdown, exportJSON, importJSON, exampleBrief,
} from './logic.js';

const byId = id => document.getElementById(id);
const form = byId('brief-form');
const dialog = byId('replace-dialog');
const exportsButtons = [byId('export-markdown'), byId('export-json')];
const textFields = ['title', 'goal', 'process', 'dependencies', 'constraints', 'exclusions', 'deadline'];
let currentScenario = 'ceny';
let snapshot = null;
let staged = null;
let importSequence = 0;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function field(id, labelText, options = {}) {
  const wrapper = node('div', undefined, 'field');
  const label = node('label', labelText);
  label.htmlFor = id;
  const control = document.createElement(options.options ? 'select' : options.multiline ? 'textarea' : 'input');
  control.id = id;
  if (options.role) control.dataset.role = options.role;
  if (options.options) {
    for (const [value, label] of options.options) {
      const option = node('option', label);
      option.value = value;
      control.append(option);
    }
  } else if (!options.multiline) {
    control.type = options.type || 'text';
  } else {
    control.rows = 2;
  }
  if (options.maxLength) control.maxLength = options.maxLength;
  if (options.placeholder) control.placeholder = options.placeholder;
  if (options.type === 'number') {
    control.min = '0';
    control.max = String(LIMITS.target);
    control.step = 'any';
    control.inputMode = 'decimal';
  }
  control.value = options.value === null || options.value === undefined ? '' : String(options.value);
  wrapper.append(label, control);
  return wrapper;
}

function renderCriteria(criteria) {
  const container = byId('acceptance');
  container.replaceChildren();
  criteria.forEach((criterion, index) => {
    const card = node('fieldset', undefined, 'criterion');
    card.append(node('legend', `Kryterium ${index + 1}`));
    card.append(field(`metric-${index}`, 'Co mierzysz?', { role: 'metric', value: criterion.metric, maxLength: 120, placeholder: SCENARIOS[currentScenario].metricHint }));
    const row = node('div', undefined, 'criterion-row three');
    row.append(
      field(`operator-${index}`, 'Warunek', { role: 'operator', value: criterion.operator, options: [['lte', 'Co najwyżej (≤)'], ['eq', 'Dokładnie (=)'], ['gte', 'Co najmniej (≥)']] }),
      field(`target-${index}`, 'Wartość docelowa', { role: 'target', value: criterion.target, type: 'number', placeholder: 'Np. 0' }),
      field(`unit-${index}`, 'Jednostka', { role: 'unit', value: criterion.unit, maxLength: 60, placeholder: 'Np. rekordów, sekund, %' }),
    );
    card.append(row);
    card.append(field(`verification-${index}`, 'Jak sprawdzisz wynik?', { role: 'verification', value: criterion.verification, multiline: true, maxLength: 500, placeholder: 'Opisz próbkę, pomiar i sposób porównania wyniku.' }));
    const remove = node('button', 'Usuń kryterium', 'button secondary criterion-remove');
    remove.type = 'button';
    remove.setAttribute('aria-label', `Usuń kryterium ${index + 1}`);
    remove.disabled = criteria.length <= 1;
    remove.addEventListener('click', () => {
      const rows = readBrief().acceptance;
      rows.splice(index, 1);
      renderCriteria(rows);
      invalidate();
      byId('add-criterion').focus();
      byId('message').textContent = 'Usunięto kryterium. Przygotuj nowy podgląd.';
    });
    card.append(remove);
    container.append(card);
  });
  byId('add-criterion').disabled = criteria.length >= LIMITS.criteria;
}

function renderMaterials(materials) {
  const container = byId('materials');
  container.replaceChildren();
  for (const material of materials) {
    const block = node('div', undefined, 'material');
    block.dataset.materialId = material.id;
    const definition = SCENARIOS[currentScenario].materials.find(item => item.id === material.id);
    block.append(node('p', definition.label, 'material-title'));
    block.append(field(`material-status-${material.id}`, 'Status materiału', {
      role: 'status', value: material.status,
      options: [['unknown', 'Do ustalenia'], ['ready', 'Gotowe'], ['needed', 'Do dostarczenia'], ['not-applicable', 'Nie dotyczy']],
    }));
    block.append(field(`material-note-${material.id}`, 'Notatka (opcjonalnie)', { role: 'note', value: material.note, maxLength: 500, placeholder: 'Np. próbka do przygotowania, format do ustalenia' }));
    container.append(block);
  }
}

function renderBrief(brief) {
  validateBrief(brief);
  currentScenario = brief.scenario;
  byId('scenario').value = currentScenario;
  byId('scenario-description').textContent = SCENARIOS[currentScenario].description;
  byId('goal').placeholder = SCENARIOS[currentScenario].goalHint;
  for (const id of textFields) byId(id).value = brief[id];
  byId('budgetPLN').value = brief.budgetPLN === null ? '' : String(brief.budgetPLN);
  renderCriteria(brief.acceptance);
  renderMaterials(brief.materials);
}

function readBrief() {
  const brief = createBrief(currentScenario);
  for (const id of textFields) brief[id] = byId(id).value;
  brief.budgetPLN = byId('budgetPLN').value === '' ? null : Number(byId('budgetPLN').value);
  brief.acceptance = [...byId('acceptance').querySelectorAll('fieldset')].map(card => {
    const value = role => card.querySelector(`[data-role="${role}"]`).value;
    return { metric: value('metric'), operator: value('operator'), target: value('target') === '' ? null : Number(value('target')), unit: value('unit'), verification: value('verification') };
  });
  brief.materials = [...byId('materials').children].map(block => ({
    id: block.dataset.materialId,
    status: block.querySelector('[data-role="status"]').value,
    note: block.querySelector('[data-role="note"]').value,
  }));
  return brief;
}

function invalidate() {
  snapshot = null;
  exportsButtons.forEach(button => { button.disabled = true; });
  byId('preview').hidden = true;
  byId('preview-text').textContent = '';
  byId('completeness').textContent = '—';
  byId('summary-status').textContent = 'Formularz zmieniony. Przygotuj nowy podgląd.';
  byId('completeness-caption').textContent = '8 sprawdzanych obszarów';
  byId('missing-summary').replaceChildren();
  byId('materials-summary').textContent = '';
  byId('message').textContent = '';
}

function stageReplacement(brief, description, success) {
  staged = { brief, success };
  byId('replace-description').textContent = description;
  if (!dialog.open) dialog.showModal();
}

function previewBrief() {
  if (!form.reportValidity()) return;
  try {
    const brief = readBrief();
    const result = assessBrief(brief);
    const markdown = exportMarkdown(brief);
    snapshot = structuredClone(brief);
    byId('summary-status').textContent = result.complete ? 'Zakres opisany. Sprawdź go z wykonawcą.' : 'Szkic — uzupełnij wskazane braki lub zapisz go na później.';
    byId('completeness').textContent = `${result.percent}%`;
    byId('completeness-caption').textContent = `${8 - result.missing.length} z 8 obszarów opisanych`;
    const missing = byId('missing-summary');
    missing.replaceChildren();
    if (result.missing.length) {
      missing.append(node('strong', 'Do uzupełnienia:'));
      const list = node('ul');
      for (const item of result.missing) {
        const li = node('li');
        const link = node('a', item.label);
        link.href = `#${item.field}`;
        li.append(link);
        list.append(li);
      }
      missing.append(list);
    } else {
      missing.append(node('p', 'Wszystkie wymagane sekcje są opisane.'));
    }
    byId('materials-summary').textContent = result.materialsReady
      ? 'Materiały: wszystkie oznaczono jako gotowe lub nie dotyczą zakresu.'
      : `Materiały do dostarczenia lub ustalenia: ${result.neededMaterials.length}. To osobny warunek rozpoczęcia prac.`;
    byId('preview-text').textContent = markdown;
    byId('preview').hidden = false;
    exportsButtons.forEach(button => { button.disabled = false; });
    byId('message').textContent = `Podgląd gotowy. Kompletność: ${result.percent}%. Możesz pobrać Markdown albo zapisać JSON.`;
    byId('summary-heading').tabIndex = -1;
    byId('summary-heading').focus({ preventScroll: true });
    byId('summary-heading').scrollIntoView({ block: 'nearest' });
  } catch (error) {
    invalidate();
    byId('message').textContent = error.message;
  }
}

function download(format) {
  if (!snapshot) return;
  const isJSON = format === 'json';
  const content = isJSON ? exportJSON(snapshot) : exportMarkdown(snapshot);
  const status = assessBrief(snapshot).complete ? 'opisany' : 'szkic';
  const blob = new Blob([content], { type: isJSON ? 'application/json;charset=utf-8' : 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = node('a');
  anchor.href = url;
  anchor.download = `veyrelo-brief-${snapshot.scenario}-${status}.${isJSON ? 'json' : 'md'}`;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  byId('message').textContent = `Przekazano plik ${isJSON ? 'JSON' : 'Markdown'} do pobrania w przeglądarce. Sprawdź folder pobranych plików.`;
}

form.addEventListener('submit', event => {
  event.preventDefault();
  previewBrief();
});
for (const eventName of ['input', 'change']) {
  form.addEventListener(eventName, event => { if (event.target.id !== 'scenario') invalidate(); });
}

byId('add-criterion').addEventListener('click', () => {
  const criteria = readBrief().acceptance;
  if (criteria.length >= LIMITS.criteria) return;
  criteria.push({ metric: '', operator: 'lte', target: null, unit: '', verification: '' });
  renderCriteria(criteria);
  invalidate();
  byId(`metric-${criteria.length - 1}`).focus();
  byId('message').textContent = `Dodano kryterium ${criteria.length}.`;
});

byId('scenario').addEventListener('change', event => {
  const nextScenario = event.target.value;
  event.target.value = currentScenario;
  if (nextScenario === currentScenario) return;
  stageReplacement(createBrief(nextScenario), `Zmiana scenariusza na „${SCENARIOS[nextScenario].label}” otworzy pusty brief z odpowiednią listą materiałów.`, 'Zmieniono scenariusz. Wypełnij nowy brief.');
});

byId('sample-button').addEventListener('click', () => {
  stageReplacement(exampleBrief(currentScenario), 'Wstawisz przykład fikcyjny, służący wyłącznie demonstracji. Dane, statusy i założenia nie opisują żadnego rzeczywistego zlecenia.', 'Wstawiono wyraźnie oznaczony przykład fikcyjny. Przygotuj podgląd, aby zobaczyć kompletność i eksporty.');
});

byId('confirm-replace').addEventListener('click', () => {
  if (!staged) return;
  const replacement = staged;
  staged = null;
  renderBrief(replacement.brief);
  invalidate();
  dialog.close();
  byId('import-file').value = '';
  byId('message').textContent = replacement.success;
  byId('title').focus();
});
byId('cancel-replace').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => { staged = null; byId('import-file').value = ''; });

byId('import-file').addEventListener('change', async event => {
  const file = event.target.files?.[0];
  const sequence = ++importSequence;
  if (!file) return;
  byId('message').textContent = 'Sprawdzanie lokalnego pliku JSON…';
  try {
    if (file.size > LIMITS.jsonBytes) throw new Error('Plik jest za duży. Maksymalny rozmiar: 128 KiB.');
    const content = await file.text();
    if (sequence !== importSequence) return;
    const brief = importJSON(content);
    stageReplacement(brief, `Poprawny JSON wersji 1. Scenariusz: ${SCENARIOS[brief.scenario].label}. Nazwa: ${brief.title || '(jeszcze nie podano)'}.`, 'Wczytano brief lokalnie. Sprawdź pola i przygotuj nowy podgląd.');
    byId('message').textContent = 'Plik jest poprawny. Potwierdź zastąpienie formularza albo anuluj.';
  } catch (error) {
    if (sequence !== importSequence) return;
    byId('message').textContent = `Nie wczytano pliku: ${error.message} Bieżący formularz pozostaje bez zmian.`;
    event.target.value = '';
  }
});

byId('export-markdown').addEventListener('click', () => download('markdown'));
byId('export-json').addEventListener('click', () => download('json'));
renderBrief(createBrief());
