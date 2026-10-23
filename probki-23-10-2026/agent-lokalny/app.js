'use strict';
// Prototyp: lokalny system agentów AI z kontrolą człowieka. Wszystko działa w przeglądarce na fikcyjnych danych.
const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };

// ── 1. Opisy elementów schematu ─────────────────────────────────────────────────────────────────────────
const NODES = {
  db: ['Baza operacyjna (PostgreSQL, w biurze)', 'Zamówienia, kontrahenci, faktury i statusy. Jedyne źródło prawdy.', ['Dostęp ma tylko agent prywatny i operatorzy.', 'Nie jest widoczna z internetu.', 'Kopia nocna na NAS.']],
  archive: ['Archiwum dokumentów (NAS)', 'Skany, PDF-y i załączniki, z wersjonowaniem.', ['RAID1 chroni przed awarią dysku, kopia offline przed szyfrowaniem przez złośliwe oprogramowanie.', 'Dokumenty nie opuszczają biura.']],
  private: ['Agent prywatny (model lokalny)', 'Czyta bazę i archiwum, pisze szkice odpowiedzi i dokumentów.', ['Model działa lokalnie (np. Ollama), dane nie trafiają do publicznych usług AI.', 'Nie wysyła niczego sam — każdy szkic trafia do kolejki akceptacji.', 'Nie przyjmuje wolnego tekstu od kontrahenta — tylko wnioski w schemacie.']],
  n8n: ['Przepływy (n8n)', 'Orkiestracja: pobiera wnioski, uruchamia kroki, zapisuje wyniki.', ['Pobiera wnioski z przekaźnika tunelem wychodzącym — biuro nie otwiera portów.', 'Każdy przepływ ma test na kopii danych przed włączeniem.']],
  python: ['Reguły i walidacja (Python)', 'Deterministyczne sprawdzenia: schemat wniosku, identyfikatory, uprawnienia kontrahenta.', ['Kwoty i daty liczy kod, nie model.', 'Wniosek spoza schematu jest odrzucany przed modelem.']],
  hitl: ['Kolejka akceptacji (człowiek)', 'Operator widzi szkic i dane źródłowe; zatwierdza, poprawia albo odrzuca.', ['Bez akceptacji nic nie jest zapisane ani wysłane.', 'Każda decyzja trafia do dziennika audytu z nazwą operatora.']],
  audit: ['Dziennik audytu', 'Każdy krok: kto, co, kiedy, na jakiej podstawie.', ['Wpis zawiera skrót poprzedniego wpisu — zmiana historii jest widoczna.', 'Przechowywany lokalnie, z kopią.']],
  relay: ['Przekaźnik (strefa brzegowa)', 'Przyjmuje wnioski od agenta publicznego i oddaje je biuru; odbiera zatwierdzone odpowiedzi.', ['Nie przechowuje danych po doręczeniu.', 'Szyfrowanie w transmisji; dostęp tylko z biura (tunel wychodzący).', 'Nie ma żadnego połączenia z bazą.']],
  public: ['Agent publiczny (dla kontrahentów)', 'Odpowiada z wiedzy publicznej (godziny, oferta, procedury) i składa wnioski.', ['Fizycznie nie ma dostępu do bazy prywatnej — jego jedyne narzędzie to „złóż wniosek”.', 'Wiadomość kontrahenta nie jest przekazywana do biura; przekazywane są tylko pola schematu.', 'Próba zmiany instrukcji nie daje dostępu do danych.']],
  contractor: ['Kontrahent', 'Pisze przez czat albo formularz.', ['Widzi tylko odpowiedzi zatwierdzone przez człowieka.', 'Identyfikowany przez konto kontrahenta (tu fikcyjne K-17).']],
};
const nodeInfo = $('nodeInfo');
function showNode(key) {
  const [title, lead, points] = NODES[key];
  nodeInfo.replaceChildren(el('b', null, title), el('p', null, lead));
  const ul = el('ul'); for (const p of points) ul.append(el('li', null, p)); nodeInfo.append(ul);
  for (const b of document.querySelectorAll('.node')) b.classList.toggle('on', b.dataset.node === key);
}
for (const b of document.querySelectorAll('.node')) b.addEventListener('click', () => showNode(b.dataset.node));
const pulse = (key) => { const n = document.querySelector(`.node[data-node="${key}"]`); if (n) { n.classList.remove('pulse'); void n.offsetWidth; n.classList.add('pulse'); } };

// ── 2. Fikcyjne dane biura ───────────────────────────────────────────────────────────────────────────────
const ORDERS = { 'ZK/1041': 'w realizacji, planowana wysyłka 28.10', 'ZK/1042': 'wysłane 21.10, numer przesyłki w panelu', 'ZK/1043': 'skompletowane, odbiór przez przewoźnika 27.10', 'ZK/1044': 'wstrzymane — brak potwierdzenia specyfikacji' };
const INVOICES = { 'FV/2026/10/118': 'faktura 4 920,00 zł brutto, opłacona 15.10', 'FV/2026/10/121': 'faktura 1 845,00 zł brutto, termin płatności 30.10' };
const PUBLIC_FAQ = [[/godzin|otwar|pracuje/i, 'Biuro pracuje od poniedziałku do piątku w godzinach 8:00–16:00 (dane przykładowe).'], [/kontakt|telefon|mail/i, 'Kontakt z biurem jest możliwy przez ten czat; sprawy wymagające danych firmy przekazuję jako wniosek.']];
const INJECTION = /zignoruj|pomiń|ignore|instrukcj|prompt|wypisz wszystk|pokaż wszystk|cał[aą] baz|wszystkie faktury|jesteś teraz|tryb administratora|admin/i;
const SCHEMA = { STATUS_ZAMOWIENIA: /^ZK\/\d{4}$/, KOPIA_FAKTURY: /^FV\/\d{4}\/\d{2}\/\d{1,4}$/ };

// ── Dziennik audytu ze skrótem łańcuchowym (FNV-1a, demonstracja) ────────────────────────────────────────
let lastHash = '00000000';
const fnv = (text) => { let h = 0x811c9dc5; for (let i = 0; i < text.length; i += 1) { h ^= text.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return h.toString(16).padStart(8, '0'); };
function audit(event, detail) {
  const time = new Date().toLocaleTimeString('pl-PL');
  const hash = fnv(lastHash + event + JSON.stringify(detail));
  const li = el('li'); li.append(el('code', null, hash), document.createTextNode(` ${time} ${event} ${detail ? JSON.stringify(detail) : ''}`));
  $('audit').prepend(li); lastHash = hash;
}

// ── Kroki ────────────────────────────────────────────────────────────────────────────────────────────────
const steps = [...document.querySelectorAll('#steps li')];
const setStep = (n, cls) => { const li = steps[n - 1]; li.classList.remove('active', 'done', 'blocked'); if (cls) li.classList.add(cls); };
const resetSteps = () => steps.forEach((li) => li.classList.remove('active', 'done', 'blocked'));
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const chat = (text, cls) => { const m = el('div', 'msg ' + cls, text); $('chat').append(m); m.scrollIntoView({ block: 'nearest' }); };

let busy = false, nextId = 1;
async function handle(message) {
  if (busy || !message.trim()) return;
  busy = true; resetSteps(); chat(message, 'in');
  setStep(1, 'active'); pulse('public'); await wait(500);
  if (INJECTION.test(message)) {
    setStep(1, 'blocked');
    $('request').textContent = 'Brak wniosku.\nWiadomość próbuje zmienić instrukcje agenta. Agent publiczny odpowiada bezpiecznie i niczego nie przekazuje.\nNawet gdyby ten filtr zawiódł: agent publiczny nie ma narzędzia do bazy — może tylko złożyć wniosek w schemacie, a schemat nie ma pola na „wszystkie faktury”.';
    chat('Agent publiczny: mogę sprawdzić status zamówienia albo przesłać kopię faktury po numerze. Nie mam dostępu do bazy firmy.', 'sys');
    audit('INJECTION_BLOCKED', { kontrahent: 'K-17' }); busy = false; return;
  }
  const faq = PUBLIC_FAQ.find(([re]) => re.test(message));
  const order = message.match(/ZK\/\d{4}/i), invoice = message.match(/FV\/\d{4}\/\d{2}\/\d{1,4}/i);
  if (!order && !invoice) {
    setStep(1, 'done');
    $('request').textContent = 'Brak wniosku: pytanie ogólne, odpowiedź z wiedzy publicznej. Biuro nie jest angażowane.';
    chat('Agent publiczny: ' + (faq ? faq[1] : 'mogę pomóc w statusie zamówienia (np. ZK/1043) albo w kopii faktury (np. FV/2026/10/118).'), 'out');
    audit('PUBLIC_ANSWER', { kontrahent: 'K-17' }); busy = false; return;
  }
  const request = { id: `W-${String(nextId++).padStart(4, '0')}`, typ: order ? 'STATUS_ZAMOWIENIA' : 'KOPIA_FAKTURY', numer: (order || invoice)[0].toUpperCase(), kontrahent: 'K-17', utworzono: new Date().toISOString() };
  setStep(1, 'done'); setStep(2, 'active'); pulse('relay');
  $('request').textContent = JSON.stringify(request, null, 2) + '\n\nTreść wiadomości kontrahenta nie trafia do biura — tylko pola schematu.';
  await wait(600);
  if (!SCHEMA[request.typ].test(request.numer)) { setStep(2, 'blocked'); audit('REQUEST_REJECTED', { id: request.id }); chat('Agent publiczny: numer ma niepoprawny format.', 'sys'); busy = false; return; }
  audit('REQUEST_ACCEPTED', { id: request.id, typ: request.typ });
  setStep(2, 'done'); setStep(3, 'active'); pulse('n8n'); await wait(600);
  setStep(3, 'done'); setStep(4, 'active'); pulse('private'); pulse('db'); await wait(700);
  const found = request.typ === 'STATUS_ZAMOWIENIA' ? ORDERS[request.numer] : INVOICES[request.numer];
  const draft = found ? (request.typ === 'STATUS_ZAMOWIENIA' ? `Zamówienie ${request.numer}: ${found}.` : `Kopia dokumentu ${request.numer} (${found}) jest gotowa do przesłania.`) : `Nie znaleziono ${request.numer} dla kontrahenta K-17. Proszę sprawdzić numer.`;
  setStep(4, 'done'); setStep(5, 'active'); pulse('hitl');
  audit('DRAFT_CREATED', { id: request.id, zrodlo: found ? 'baza lokalna' : 'brak rekordu' });
  addToQueue(request, draft, found);
  busy = false;
}

function addToQueue(request, draft, found) {
  const queue = $('queue'); if (queue.querySelector('.muted')) queue.replaceChildren();
  const item = el('div', 'qitem');
  item.append(el('div', null, `${request.id} · ${request.typ} · ${request.numer}`), el('div', 'src', `Źródło: ${found ? 'baza lokalna (fikcyjna)' : 'brak rekordu'} · szkic agenta prywatnego`));
  const area = el('textarea'); area.value = draft; item.append(area);
  const btns = el('div', 'qbtns'), ok = el('button', 'ok', 'Zatwierdź i wyślij'), bad = el('button', 'bad', 'Odrzuć');
  btns.append(ok, bad); item.append(btns); queue.prepend(item); updateCount();
  ok.addEventListener('click', () => {
    chat('Biuro: ' + area.value.trim(), 'out'); audit('HUMAN_APPROVED', { id: request.id, operator: 'operator-demo', zmieniono: area.value !== draft });
    setStep(5, 'done'); setStep(6, 'done'); pulse('audit'); item.remove(); updateCount();
  });
  bad.addEventListener('click', () => {
    chat('Biuro: odpowiedź zostanie przygotowana osobno.', 'sys'); audit('HUMAN_REJECTED', { id: request.id, operator: 'operator-demo' });
    setStep(5, 'blocked'); item.remove(); updateCount();
  });
}
function updateCount() {
  const n = $('queue').querySelectorAll('.qitem').length;
  $('queueCount').textContent = String(n);
  if (!n) $('queue').replaceChildren(el('p', 'muted', 'Brak szkiców do akceptacji.'));
}

for (const b of document.querySelectorAll('[data-example]')) b.addEventListener('click', () => handle(b.dataset.example));
$('chatForm').addEventListener('submit', (e) => { e.preventDefault(); const v = $('chatInput').value; $('chatInput').value = ''; handle(v); });

// ── 4. Kalkulator czasu ─────────────────────────────────────────────────────────────────────────────────
const PROCESSES = [['Odpowiedzi na zapytania kontrahentów', 6], ['Faktury kosztowe i archiwizacja', 4], ['Przygotowanie ofert i dokumentów', 5], ['Raporty dla zarządu', 3], ['Przypomnienia o płatnościach', 2]];
const rows = $('calcRows');
for (const [name, hours] of PROCESSES) {
  const row = el('label', 'calc-row'); const check = el('input'); check.type = 'checkbox'; check.checked = true;
  const num = el('input'); num.type = 'number'; num.min = '0'; num.max = '80'; num.step = '0.5'; num.value = String(hours);
  row.append(check, el('span', null, name), num); rows.append(row);
}
function recalc() {
  const share = Number($('share').value) / 100; $('shareOut').textContent = Math.round(share * 100) + '%';
  let now = 0; for (const row of rows.children) { const [check, , num] = row.querySelectorAll('input, span'); if (check.checked) now += Math.max(0, Number(num.value) || 0); }
  // Automat przejmuje część pracy; z tej części ok. 20% zostaje na akceptację człowieka.
  const after = now * (1 - share) + now * share * 0.2;
  $('hoursNow').textContent = now.toFixed(1).replace('.', ','); $('hoursAfter').textContent = after.toFixed(1).replace('.', ',');
  $('hoursSaved').textContent = Math.round((now - after) * 4.33).toString();
}
rows.addEventListener('input', recalc); $('share').addEventListener('input', recalc); recalc();
audit('PROTOTYP_START', { dane: 'fikcyjne' });
