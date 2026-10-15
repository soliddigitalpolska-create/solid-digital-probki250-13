"""Offline own configuration demonstrations. No network, credentials or live campaigns."""
from pathlib import Path
import json,hashlib,unittest,io,copy,re,decimal,datetime,html

ROOT=Path(__file__).resolve().parent
D=decimal.Decimal
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def esc(x):return html.escape(str(x),quote=True)

def validate_plan(plan):
    if plan['currency']!='PLN':raise ValueError('currency')
    ids=[r['id'] for r in plan['campaigns']]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate campaign id')
    budgets=[D(str(r['monthly_media_cap'])) for r in plan['campaigns']]
    if any(x<=0 for x in budgets):raise ValueError('nonpositive media cap')
    if sum(budgets)!=D(str(plan['monthly_media_total'])):raise ValueError('media caps sum')
    if D(str(plan['service_fee']))<=0:raise ValueError('service fee')
    for r in plan['campaigns']:
        if r['status']!='DRAFT_NOT_PUBLISHED':raise ValueError('not a draft')
        if r['objective'] not in ['LEADS','SALES']:raise ValueError('objective')
        if not re.fullmatch(r'[a-z0-9_-]+',r['utm_campaign']):raise ValueError('UTM')
    return True

def ingest_events(events):
    accepted=[];rejected=[];seen=set()
    for e in events:
        reason=None
        if not e.get('analytics_consent'):reason='consent_denied'
        elif not e.get('event_id'):reason='event_id_missing'
        elif e['event_id'] in seen:reason='duplicate'
        elif e.get('currency')!='PLN':reason='currency_mismatch'
        elif D(str(e.get('value',-1)))<0:reason='negative_value'
        elif any(k in e for k in ['email','phone','name','address']):reason='raw_personal_data'
        if reason:rejected.append(dict(event_id=e.get('event_id'),reason=reason));continue
        seen.add(e['event_id']);accepted.append(copy.deepcopy(e))
    return dict(accepted=accepted,rejected=rejected)

CAMPAIGNS=[
dict(id='meta-static-1',platform='Meta',objective='LEADS',monthly_media_cap='600.00',utm_campaign='b2b_integracje_static',status='DRAFT_NOT_PUBLISHED',creative_brief='Problem ręcznego przepisywania zamówień; pokaż proces przed i po, bez nieudokumentowanych liczb.',audience='Polska, osoby zainteresowane usługami dla firm; bez wrażliwych kategorii.'),
dict(id='meta-static-2',platform='Meta',objective='LEADS',monthly_media_cap='600.00',utm_campaign='b2b_automatyzacje_static',status='DRAFT_NOT_PUBLISHED',creative_brief='Jedna czynność, jeden wynik i formularz kontaktu; gotowy materiał klienta.',audience='Oddzielny test komunikatu; wykluczenie istniejących leadów dopiero po zatwierdzeniu podstawy i źródła danych.'),
dict(id='meta-video',platform='Meta',objective='LEADS',monthly_media_cap='550.00',utm_campaign='b2b_video',status='DRAFT_NOT_PUBLISHED',creative_brief='15–30 sekund: problem, pokazanie procesu, CTA. Bez obietnicy oszczędności niepopartej materiałami.',audience='Polska; test kreacji video.'),
dict(id='google-search',platform='Google',objective='LEADS',monthly_media_cap='1250.00',utm_campaign='b2b_search',status='DRAFT_NOT_PUBLISHED',keywords=['integracja zamówień dla firmy','automatyzacja procesów firmowych'],negative_keywords=['praca','kurs','darmowe','staż'],headlines=['Integracje dla Twojej firmy','Połącz systemy i procesy','Omów konkretną automatyzację']),
dict(id='google-pmax',platform='Google',objective='LEADS',monthly_media_cap='500.00',utm_campaign='b2b_pmax',status='DRAFT_NOT_PUBLISHED',asset_inventory='Materiały klienta: nagłówki, teksty, obrazy i video; kompletność sprawdzona przed publikacją.')]
PLAN=dict(demo_only=True,client='Własna fikcyjna marka: Studio Proces',currency='PLN',monthly_media_total='3500.00',service_fee='1100.00',campaigns=CAMPAIGNS,publication_gate=['approved_budget','approved_creatives','access_verified','conversion_test_passed','client_launch_approval'],weekly_review=['spend_vs_cap','qualified_leads','cost_per_qualified_lead','search_terms','creative_variant_result','change_log'],performance_history='None. This file is not a live platform export and contains no paid performance claim.')
EVENTS=[dict(event_id='lead-001',event_name='generate_lead',value='0.00',currency='PLN',analytics_consent=True),dict(event_id='order-001',event_name='purchase',value='249.00',currency='PLN',analytics_consent=True),dict(event_id='order-001',event_name='purchase',value='249.00',currency='PLN',analytics_consent=True),dict(event_id='lead-002',event_name='generate_lead',value='0.00',currency='PLN',analytics_consent=False),dict(event_id='order-usd',event_name='purchase',value='99.00',currency='USD',analytics_consent=True)]
TIKTOK_PLAN=dict(demo_only=True,client='Fikcyjna marka Studio Forma',currency='PLN',monthly_media_total='3000.00',service_fee='700.00',campaigns=[dict(id='tiktok-test',platform='TikTok',objective='SALES',monthly_media_cap='1500.00',utm_campaign='forma_video_test',status='DRAFT_NOT_PUBLISHED',creative_variants=['problem_solution','product_detail','outfit_use']),dict(id='tiktok-next-test',platform='TikTok',objective='SALES',monthly_media_cap='1500.00',utm_campaign='forma_next_test',status='DRAFT_NOT_PUBLISHED',creative_variants=['problem_solution_b','product_detail_b','outfit_use_b'])],ugc_briefs=[dict(id='problem_solution',hook='Co zakładasz, kiedy chcesz prostego zestawu?',shots=['detal produktu','cały fason','dwie możliwości zestawienia'],cta='Sprawdź rozmiary i dostępność'),dict(id='product_detail',hook='Najpierw zobacz detal, potem wybierz rozmiar.',shots=['zbliżenie szwu','materiał w ruchu','czytelna tabela rozmiarów'],cta='Zobacz kartę produktu'),dict(id='outfit_use',hook='Jedna bluza, dwie codzienne sytuacje.',shots=['zestaw do pracy','zestaw po pracy','detal koloru'],cta='Wybierz dostępny wariant')],measurement='Lokalny kontrakt purchase/value/currency/event_id. Mapowanie do aktualnych narzędzi konta wymaga osobnej walidacji przy wdrożeniu.',performance_history='None; configuration proposal only.')
ECOM_PLAN=dict(demo_only=True,client='Fikcyjna marka Studio Forma',currency='PLN',monthly_media_total='3000.00',service_fee='1100.00',campaigns=[dict(id='ecom-search',platform='Google',objective='SALES',monthly_media_cap='900.00',utm_campaign='forma_search',status='DRAFT_NOT_PUBLISHED'),dict(id='ecom-pmax',platform='Google',objective='SALES',monthly_media_cap='600.00',utm_campaign='forma_pmax',status='DRAFT_NOT_PUBLISHED'),dict(id='ecom-meta-1',platform='Meta',objective='SALES',monthly_media_cap='750.00',utm_campaign='forma_meta_product',status='DRAFT_NOT_PUBLISHED'),dict(id='ecom-meta-2',platform='Meta',objective='SALES',monthly_media_cap='750.00',utm_campaign='forma_meta_test',status='DRAFT_NOT_PUBLISHED')],feed_preflight=['product_id_unique','price_matches_product','currency_matches_checkout','availability_matches_stock','landing_url_validated_before_launch'],performance_history='None; draft configuration only.')

class AdsTests(unittest.TestCase):
    def test_plan_valid(self):self.assertTrue(validate_plan(PLAN))
    def test_five_campaigns(self):self.assertEqual(len(PLAN['campaigns']),5)
    def test_platform_split(self):self.assertEqual({p:sum(D(r['monthly_media_cap']) for r in CAMPAIGNS if r['platform']==p) for p in ['Meta','Google']},{'Meta':D('1750'),'Google':D('1750')})
    def test_fee_not_media(self):self.assertEqual(sum(D(r['monthly_media_cap']) for r in CAMPAIGNS),D(PLAN['monthly_media_total']))
    def test_bad_sum_rejected(self):
        p=copy.deepcopy(PLAN);p['monthly_media_total']='3000'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_negative_budget_rejected(self):
        p=copy.deepcopy(PLAN);p['campaigns'][0]['monthly_media_cap']='-1'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_duplicate_campaign_rejected(self):
        p=copy.deepcopy(PLAN);p['campaigns'][1]['id']=p['campaigns'][0]['id']
        with self.assertRaises(ValueError):validate_plan(p)
    def test_unsafe_utm_rejected(self):
        p=copy.deepcopy(PLAN);p['campaigns'][0]['utm_campaign']='Bad value & token'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_live_status_rejected(self):
        p=copy.deepcopy(PLAN);p['campaigns'][0]['status']='ACTIVE'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_two_accepted_events(self):self.assertEqual(len(ingest_events(EVENTS)['accepted']),2)
    def test_duplicate_rejected(self):self.assertIn('duplicate',[x['reason'] for x in ingest_events(EVENTS)['rejected']])
    def test_no_consent_rejected(self):self.assertIn('consent_denied',[x['reason'] for x in ingest_events(EVENTS)['rejected']])
    def test_wrong_currency_rejected(self):self.assertIn('currency_mismatch',[x['reason'] for x in ingest_events(EVENTS)['rejected']])
    def test_missing_id_rejected(self):self.assertEqual(ingest_events([dict(analytics_consent=True,currency='PLN',value='0')])['rejected'][0]['reason'],'event_id_missing')
    def test_negative_value_rejected(self):self.assertEqual(ingest_events([dict(event_id='bad',analytics_consent=True,currency='PLN',value='-1')])['rejected'][0]['reason'],'negative_value')
    def test_raw_email_rejected(self):self.assertEqual(ingest_events([dict(event_id='bad',analytics_consent=True,currency='PLN',value='0',email='demo@example.invalid')])['rejected'][0]['reason'],'raw_personal_data')
    def test_tiktok_plan_valid(self):self.assertTrue(validate_plan(TIKTOK_PLAN))
    def test_tiktok_six_variants(self):self.assertEqual(sum(len(x['creative_variants']) for x in TIKTOK_PLAN['campaigns']),6)
    def test_tiktok_three_complete_briefs(self):self.assertTrue(len(TIKTOK_PLAN['ugc_briefs'])==3 and all(x['hook'] and len(x['shots'])==3 and x['cta'] for x in TIKTOK_PLAN['ugc_briefs']))
    def test_ecommerce_plan_valid(self):self.assertTrue(validate_plan(ECOM_PLAN))
    def test_ecommerce_all_sales(self):self.assertEqual({x['objective'] for x in ECOM_PLAN['campaigns']},{'SALES'})

PRODUCTS=[dict(handle='koszulka-dzien',title='Koszulka DZIEŃ',collection='codziennie',variants=[dict(sku='DZIEN-S',size='S',price='129.00',stock=8),dict(sku='DZIEN-M',size='M',price='129.00',stock=12),dict(sku='DZIEN-L',size='L',price='129.00',stock=6)]),dict(handle='bluza-miasto',title='Bluza MIASTO',collection='warstwy',variants=[dict(sku='MIASTO-S',size='S',price='249.00',stock=4),dict(sku='MIASTO-M',size='M',price='249.00',stock=7),dict(sku='MIASTO-L',size='L',price='249.00',stock=5)]),dict(handle='spodnie-spokoj',title='Spodnie SPOKÓJ',collection='codziennie',variants=[dict(sku='SPOKOJ-S',size='S',price='219.00',stock=3),dict(sku='SPOKOJ-M',size='M',price='219.00',stock=4),dict(sku='SPOKOJ-L',size='L',price='219.00',stock=2)])]
def validate_products(products):
    handles=[];skus=[]
    for p in products:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',p['handle']):raise ValueError('handle')
        handles.append(p['handle'])
        if not p['title'].strip():raise ValueError('title')
        if p['collection'] not in ['codziennie','warstwy']:raise ValueError('collection')
        for v in p['variants']:
            if not v['sku'].strip():raise ValueError('SKU')
            skus.append(v['sku'])
            if v['size'] not in ['XS','S','M','L','XL']:raise ValueError('size')
            if D(v['price'])<=0:raise ValueError('price')
            if v['stock']<0:raise ValueError('stock')
    if len(handles)!=len(set(handles)):raise ValueError('duplicate handle')
    if len(skus)!=len(set(skus)):raise ValueError('duplicate SKU')
    return dict(products=len(products),variants=len(skus),total_stock=sum(v['stock'] for p in products for v in p['variants']))

LIQUID='''{% if section.settings.enabled %}
<section class="studio-note" aria-label="{{ section.settings.title | escape }}">
  {% if section.settings.image != blank %}
    {{ section.settings.image | image_url: width: 1600 | image_tag: alt: section.settings.title }}
  {% endif %}
  <h2>{{ section.settings.title | escape }}</h2>
  <div>{{ section.settings.body }}</div>
  {% if section.settings.link != blank %}
    <a href="{{ section.settings.link }}">{{ section.settings.link_label | escape }}</a>
  {% endif %}
</section>
{% endif %}
{% schema %}
{"name":"Studio info","settings":[{"type":"checkbox","id":"enabled","label":"Pokaż sekcję","default":true},{"type":"text","id":"title","label":"Nagłówek","default":"Ubrania na co dzień"},{"type":"richtext","id":"body","label":"Treść","default":"<p>Wybierz wygodę i prosty krój.</p>"},{"type":"image_picker","id":"image","label":"Obraz"},{"type":"url","id":"link","label":"Link"},{"type":"text","id":"link_label","label":"Tekst linku","default":"Zobacz kolekcję"}],"presets":[{"name":"Studio info"}]}
{% endschema %}
'''
def liquid_schema(source):
    match=re.search(r'{% schema %}(.*?){% endschema %}',source,re.S)
    if not match:raise ValueError('schema')
    data=json.loads(match[1]);ids=[x['id'] for x in data['settings']]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate setting')
    tags=re.findall(r'{%\s*(.*?)\s*%}',source);stack=[]
    for t in tags:
        if t.startswith('if '):stack.append('if')
        elif t=='endif':
            if not stack:raise ValueError('unbalanced conditional')
            stack.pop()
    if stack:raise ValueError('unbalanced conditional')
    if '{{ section.settings.title | escape }}' not in source:raise ValueError('unescaped title')
    return data
def newsletter_recipients(records):return [x['id'] for x in records if x.get('marketing_opt_in') and not x.get('unsubscribed')]

class ShopifyTests(unittest.TestCase):
    def test_catalog(self):self.assertEqual(validate_products(PRODUCTS),dict(products=3,variants=9,total_stock=51))
    def test_duplicate_sku_rejected(self):
        p=copy.deepcopy(PRODUCTS);p[1]['variants'][0]['sku']=p[0]['variants'][0]['sku']
        with self.assertRaises(ValueError):validate_products(p)
    def test_duplicate_handle_rejected(self):
        p=copy.deepcopy(PRODUCTS);p[1]['handle']=p[0]['handle']
        with self.assertRaises(ValueError):validate_products(p)
    def test_zero_price_rejected(self):
        p=copy.deepcopy(PRODUCTS);p[0]['variants'][0]['price']='0'
        with self.assertRaises(ValueError):validate_products(p)
    def test_negative_stock_rejected(self):
        p=copy.deepcopy(PRODUCTS);p[0]['variants'][0]['stock']=-1
        with self.assertRaises(ValueError):validate_products(p)
    def test_unknown_collection_rejected(self):
        p=copy.deepcopy(PRODUCTS);p[0]['collection']='missing'
        with self.assertRaises(ValueError):validate_products(p)
    def test_invalid_size_rejected(self):
        p=copy.deepcopy(PRODUCTS);p[0]['variants'][0]['size']='unknown'
        with self.assertRaises(ValueError):validate_products(p)
    def test_empty_title_rejected(self):
        p=copy.deepcopy(PRODUCTS);p[0]['title']=''
        with self.assertRaises(ValueError):validate_products(p)
    def test_schema(self):self.assertEqual(len(liquid_schema(LIQUID)['settings']),6)
    def test_broken_conditional_rejected(self):
        with self.assertRaises(ValueError):liquid_schema(LIQUID.replace('{% endif %}','',1))
    def test_unescaped_title_rejected(self):
        with self.assertRaises(ValueError):liquid_schema(LIQUID.replace('{{ section.settings.title | escape }}','{{ section.settings.title }}'))
    def test_unsubscribed_excluded(self):self.assertEqual(newsletter_recipients([dict(id='a',marketing_opt_in=True,unsubscribed=True)]),[])
    def test_opt_in_required(self):self.assertEqual(newsletter_recipients([dict(id='a',marketing_opt_in=False,unsubscribed=False)]),[])
    def test_opted_in_selected(self):self.assertEqual(newsletter_recipients([dict(id='a',marketing_opt_in=True,unsubscribed=False)]),['a'])

def run_suite(cls):
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    record=dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_run_output=stream.getvalue())
    if not result.wasSuccessful():raise RuntimeError(stream.getvalue())
    return record

def page(title,subtitle,body,links):
    footer='Próbka własnego warsztatu. Dane i materiały marki klienta wymagają osobnego uzgodnienia.'
    if 'Shopify' in title:footer+=' Sekcja Liquid ma lokalną kontrolę struktury i schematu; nie była uruchomiona w sklepie Shopify.'
    return '<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>body{margin:0;background:#f3f1eb;color:#233a34;font:16px/1.7 system-ui,sans-serif}main{max-width:1080px;margin:auto;padding:48px 25px}h1{font-size:clamp(32px,5vw,60px);line-height:1.1;letter-spacing:-2px}h2{margin-top:38px}.note{padding:20px;background:#e5e9dc;border-left:4px solid #62804c}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}.card{background:white;border:1px solid #d9dece;padding:22px;border-radius:9px}table{border-collapse:collapse;width:100%;background:white}td,th{text-align:left;padding:14px;border-bottom:1px solid #e1e5db}th{background:#274b3f;color:white}a{color:#21694c}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:22px;font-size:13px}footer{margin-top:40px;font-size:13px}small{color:#647668}</style><main><small>SOLID DIGITAL · WŁASNA PRÓBKA · OFFLINE</small><h1>'+esc(title)+'</h1><p>'+esc(subtitle)+'</p><p class="note">Własna demonstracja na fikcyjnych danych. Bez konta klienta, bez publikacji kampanii lub sklepu i bez wyników komercyjnych. Testy dotyczą załączonego kodu lokalnego. Nie stanowią testu zgodności bieżącego API platformy.</p>'+body+'<h2>Źródła i rzeczywiste wyniki testów</h2><ul>'+''.join('<li><a href="'+esc(path)+'">'+esc(label)+'</a></li>' for path,label in links)+'</ul><footer>'+esc(footer)+'</footer></main></html>'

if __name__=='__main__':
    ads=ROOT/'proofs'/'ads-config';shop=ROOT/'proofs'/'shopify-ops'
    ads.mkdir(parents=True,exist_ok=True);shop.mkdir(parents=True,exist_ok=True)
    adsqa=run_suite(AdsTests);shopqa=run_suite(ShopifyTests)
    save(ads/'campaign-plan.json',PLAN);save(ads/'campaign-plan-tiktok.json',TIKTOK_PLAN);save(ads/'campaign-plan-ecommerce.json',ECOM_PLAN);save(ads/'event-fixtures.json',EVENTS);save(ads/'event-results.json',ingest_events(EVENTS));save(ads/'qa.json',adsqa)
    adsbody='<h2>Pięć kampanii. Jeden jawny budżet.</h2><p>Planowany limit mediów: <b>3500 PLN / miesiąc</b>. Osobne wynagrodzenie za usługę: <b>1100 PLN</b>. Te kwoty nie są mieszane.</p><table><tr><th>Kampania</th><th>Cel</th><th>Plan miesięczny</th></tr>'+''.join('<tr><td>'+esc(x['id'])+'</td><td>'+esc(x['objective'])+'</td><td>'+esc(x['monthly_media_cap'])+' PLN</td></tr>' for x in CAMPAIGNS)+'</table><h2>Próba pomiaru wykonana lokalnie</h2><div class="grid"><div class="card"><b>5 zdarzeń wejściowych</b><p>2 przyjęte; powtórzenie, odmowa zgody i błędna waluta zostały odrzucone.</p></div><div class="card"><b>'+str(adsqa['tests_run'])+' wykonanych testów</b><p>Limity, waluta, UTM, duplikaty, brak zgody i surowe dane osobowe. Wszystkie przeszły.</p></div></div><h2>Przykład konkretnego briefu</h2><p>15–30 sekund: pokaż ręczne przepisywanie zamówienia, następnie połączenie dwóch systemów i pojedynczy formularz kontaktu. Nie dodawaj nieudokumentowanych oszczędności ani fikcyjnych wyników. Materiał i budżet wymagają akceptacji przed emisją.</p>'
    (ads/'index.html').write_text(page('Konfiguracja kampanii i kontrola pomiaru','Przykładowy plan kampanii i lokalne testy kontroli danych.',adsbody,[('campaign-plan.json','Pełny plan B2B Meta + Google'),('campaign-plan-tiktok.json','TikTok: 2 kampanie, 6 wariantów, 3 kompletne briefy UGC'),('campaign-plan-ecommerce.json','E-commerce: Search, PMax i dwie kampanie Meta'),('event-fixtures.json','Dane wejściowe próby'),('event-results.json','Rzeczywisty wynik lokalnego przetwarzania'),('qa.json','Wynik wykonanych testów'),('source.py','Kod źródłowy i testy')]),encoding='utf-8')
    save(shop/'products.json',PRODUCTS);save(shop/'catalog-result.json',validate_products(PRODUCTS));save(shop/'qa.json',shopqa);(shop/'section-banner.liquid').write_text(LIQUID,encoding='utf-8')
    operations=dict(demo_only=True,catalog=validate_products(PRODUCTS),collections=['codziennie','warstwy'],newsletters=[dict(subject='Proste warstwy na chłodniejszy dzień',preheader='Bluza MIASTO w trzech rozmiarach',body='Wybierz wygodny fason, sprawdź tabelę rozmiarów i zobacz dostępne warianty. Cena 249 PLN pochodzi z danych testowego katalogu.',cta='Zobacz kolekcję warstwy'),dict(subject='Twoja codzienna baza',preheader='Koszulka i spodnie z kolekcji codziennie',body='Porównaj rozmiary, sprawdź dostępność i skomponuj własny zestaw. Newsletter jest lokalnym szkicem i nie został wysłany.',cta='Zobacz kolekcję codziennie')],release_checklist=['copy_theme_before_changes','validate_product_data','review_mobile_and_desktop','test_newsletter_to_control_address','confirm_opt_in_and_unsubscribe','get_client_approval','publish_approved_version','keep_rollback_copy'])
    save(shop/'operations-pack.json',operations)
    shopbody='<h2>Gotowy katalog testowy</h2><div class="grid">'+''.join('<div class="card"><small>STUDIO FORMA · FIKCYJNA MARKA</small><h2>'+esc(x['title'])+'</h2><p>'+esc(x['variants'][0]['price'])+' PLN · S / M / L</p><p>Kolekcja: '+esc(x['collection'])+'</p></div>' for x in PRODUCTS)+'</div><h2>Kontrola danych i wdrożenia</h2><p>3 karty, 9 wariantów, 51 sztuk stanu testowego. SKU są unikalne. Nieprawidłowa cena, rozmiar, stan i kolekcja przerywają walidację. '+str(shopqa['tests_run'])+' testów wykonanych rzeczywiście, wszystkie PASS.</p><h2>Dwa gotowe szkice newsletterów</h2><div class="grid">'+''.join('<div class="card"><h3>'+esc(x['subject'])+'</h3><p>'+esc(x['body'])+'</p><b>'+esc(x['cta'])+'</b></div>' for x in operations['newsletters'])+'</div><h2>Źródło sekcji Liquid</h2><p>Załączona sekcja ma ustawienia tekstu, obrazu, linku i włączenia. Schemat JSON i zamknięcia warunków są kontrolowane lokalnie. Native Shopify runtime i publikacja na koncie nie są tu deklarowane.</p>'
    (shop/'index.html').write_text(page('Obsługa Shopify — produkty, treści i Liquid','Własny pakiet źródłowy: spójność wariantów, dwa newslettery i sekcja motywu do wdrożenia na kopii.',shopbody,[('products.json','Pełne dane produktów i wariantów'),('catalog-result.json','Rzeczywisty wynik walidacji katalogu'),('operations-pack.json','Newslettery i lista kontroli publikacji'),('section-banner.liquid','Źródło sekcji Liquid'),('qa.json','Rzeczywisty wynik testów'),('source.py','Kod walidacji i testy')]),encoding='utf-8')
    source=Path(__file__).read_bytes();(ads/'source.py').write_bytes(source);(shop/'source.py').write_bytes(source)
    manifest=[]
    for folder in [ads,shop]:
        for p in folder.iterdir():manifest.append(dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    save(ROOT/'owned-proof-manifest.json',dict(status='LOCAL_TESTS_PASS_NOT_PUBLISHED',ads_tests=adsqa['tests_run'],shopify_tests=shopqa['tests_run'],network_requests=0,files=manifest))
    print(json.dumps(dict(status='PASS',ads_tests=adsqa['tests_run'],shopify_tests=shopqa['tests_run'],files=len(manifest),network_requests=0)))
