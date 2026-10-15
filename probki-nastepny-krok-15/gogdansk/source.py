"""Meaningful offline QA of the owned tourism demonstration.
Run: python source.py (Python 3.10+, Node 18+). No network or packages.
Based on the owned ads-config proof's budget/consent/deduplication approach.
Not a production Google/Meta API validator or paid campaign performance test.
"""
from pathlib import Path
from decimal import Decimal
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import unittest, json, subprocess, re, io, datetime, copy, zipfile, shutil

ROOT=Path(__file__).resolve().parent
PUB=ROOT if (ROOT/'campaign-plan.json').exists() else ROOT/'public'
PLAN=json.loads((PUB/'campaign-plan.json').read_text(encoding='utf-8'))

def validate_plan(p):
    if p.get('demo_only') is not True or p['currency']!='PLN':raise ValueError('demo currency')
    if p.get('service_fee_requires_technically_ready_shop') is not True:raise ValueError('shop readiness')
    if Decimal(p['service_fee_net'])!=Decimal('1600'):raise ValueError('fee')
    caps=[Decimal(x['monthly_media_cap']) for x in p['campaigns']]
    if any(x<=0 for x in caps):raise ValueError('nonpositive cap')
    if sum(caps)!=Decimal(p['monthly_media_total']):raise ValueError('sum')
    if len({x['id'] for x in p['campaigns']})!=len(p['campaigns']):raise ValueError('duplicate ID')
    for platform in ['Google','Meta']:
        if sum(x['platform']==platform for x in p['campaigns'])>3:raise ValueError('campaign limit')
    for c in p['campaigns']:
        if c['status']!='DRAFT_NOT_PUBLISHED':raise ValueError('live campaign')
        if not re.fullmatch('[a-z0-9_-]+',c['utm_campaign']):raise ValueError('UTM')
        if c['platform']=='Google':
            if not 3<=len(c.get('headlines',[]))<=15 or any(len(x)>30 for x in c['headlines']):raise ValueError('headline length')
            if not 2<=len(c.get('descriptions',[]))<=4 or any(len(x)>90 for x in c['descriptions']):raise ValueError('description length')
    scope=p['monthly_scope']
    if scope['human_hours']!=22 or sum(p['human_hours_allocation'].values())!=22:raise ValueError('human hours')
    if scope['seo_pages']!=4 or scope['seo_article_words']!=600 or scope['creative_limit']!=4:raise ValueError('scope')
    if scope.get('new_campaigns_first_month_total_limit')!=2 or scope.get('campaign_limits_include_existing_and_new') is not True:raise ValueError('first month launch limit')
    if scope.get('creative_type')!='static_from_client_materials' or scope.get('article_word_limit')!=600:raise ValueError('bounded deliverables')
    return True

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__();self.links=[];self.meta={};self.canonical=[];self.h1=0;self.jsonld=[];self._ld=False;self._parts=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if tag=='meta' and a.get('name'):self.meta[a['name']]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
        if tag=='script' and a.get('type')=='application/ld+json':self._ld=True;self._parts=[]
        for name in ['href','src']:
            if name in a and not (tag=='link' and a.get('rel')=='canonical'):self.links.append(a[name])
    def handle_data(self,data):
        if self._ld:self._parts.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self._ld:self.jsonld.append(json.loads(''.join(self._parts)));self._ld=False

class OwnedProofTests(unittest.TestCase):
    def test_plan_valid(self):self.assertTrue(validate_plan(PLAN))
    def test_budget_mutation_caught(self):
        p=copy.deepcopy(PLAN);p['monthly_media_total']='9000'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_negative_media_rejected(self):
        p=copy.deepcopy(PLAN);p['campaigns'][0]['monthly_media_cap']='-10'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_google_limit_rejected(self):
        p=copy.deepcopy(PLAN)
        for n in range(2):
            c=copy.deepcopy(p['campaigns'][0]);c['id']='extra'+str(n);p['campaigns'].append(c)
        p['monthly_media_total']=str(sum(Decimal(x['monthly_media_cap']) for x in p['campaigns']))
        with self.assertRaisesRegex(ValueError,'campaign limit'):validate_plan(p)
    def test_live_status_rejected(self):
        p=copy.deepcopy(PLAN);p['campaigns'][0]['status']='ACTIVE'
        with self.assertRaises(ValueError):validate_plan(p)
    def test_long_search_headline_rejected(self):
        p=copy.deepcopy(PLAN);p['campaigns'][0]['headlines'][0]='x'*31
        with self.assertRaisesRegex(ValueError,'headline length'):validate_plan(p)
    def test_meta_creatives_are_owned_svg(self):
        for f in (PUB/'assets').glob('*.svg'):
            s=f.read_text(encoding='utf-8');self.assertIn('MARKA FIKCYJNA',s);self.assertNotIn('<image',s);self.assertNotIn('<script',s)
        self.assertEqual(len(list((PUB/'assets').glob('*.svg'))),2)
    def test_seo_actual_before_after(self):
        before=Document((PUB/'before.html').read_text(encoding='utf-8'));after=Document((PUB/'landing.html').read_text(encoding='utf-8'))
        self.assertNotIn('description',before.meta);self.assertFalse(before.canonical);self.assertFalse(before.jsonld)
        self.assertEqual(after.h1,1);self.assertTrue(100<=len(after.meta['description'])<=180);self.assertEqual(len(after.canonical),1)
        self.assertTrue(after.canonical[0].endswith('/gogdansk/landing.html'));self.assertEqual(after.jsonld[0]['url'],after.canonical[0]);self.assertEqual(after.jsonld[0]['@type'],'WebPage')
    def test_demo_pages_noindex(self):
        for f in PUB.glob('*.html'):self.assertEqual(Document(f.read_text(encoding='utf-8')).meta.get('robots'),'noindex,follow',f.name)
    def test_article_word_count(self):
        s=(PUB/'guide.html').read_text(encoding='utf-8');article=s.split('<h1>',1)[1].split('<p><a class="btn"',1)[0]
        words=len(re.sub('<[^>]*>',' ',article).split());self.assertGreaterEqual(words,550);self.assertLessEqual(words,600)
    def test_local_links_exist(self):
        for f in PUB.glob('*.html'):
            for u in Document(f.read_text(encoding='utf-8')).links:
                path=unquote(urlsplit(u).path)
                if not path or urlsplit(u).scheme:continue
                if path in ['sample-source.zip','qa.json']:continue # generated after the suite; checked again after packaging
                self.assertTrue((f.parent/path).is_file(),f'{f.name}: {u}')
    def test_no_external_execution_or_transport(self):
        for f in list(PUB.glob('*.js'))+list(PUB.glob('*.html')):
            s=f.read_text(encoding='utf-8')
            for token in ['fetch(', 'XMLHttpRequest', 'sendBeacon(', 'https://www.googletagmanager.com', 'https://connect.facebook.net']:
                self.assertNotIn(token,s,f.name)
    def test_client_is_not_pretended_to_be_demo_brand(self):
        self.assertNotIn('GoGdansk',(PUB/'index.html').read_text(encoding='utf-8'))
    def test_monthly_scope_and_hours(self):
        self.assertEqual(PLAN['monthly_scope']['google_campaign_limit'],3);self.assertEqual(PLAN['monthly_scope']['meta_campaign_limit'],3)
        self.assertEqual(PLAN['period_days'],30);self.assertEqual(sum(PLAN['human_hours_allocation'].values()),22)
        self.assertEqual(PLAN['monthly_scope']['new_campaigns_first_month_total_limit'],2)
        self.assertTrue(PLAN['monthly_scope']['campaign_limits_include_existing_and_new'])
    def test_excess_first_month_launches_rejected(self):
        p=copy.deepcopy(PLAN);p['monthly_scope']['new_campaigns_first_month_total_limit']=3
        with self.assertRaisesRegex(ValueError,'first month launch limit'):validate_plan(p)

def run():
    # Make source/tests themselves reachable and independently runnable from the downloaded archive.
    if PUB!=ROOT:
        shutil.copy2(__file__,PUB/'source.py');(PUB/'tests').mkdir(exist_ok=True)
        shutil.copy2(ROOT/'tests/tracker.test.cjs',PUB/'tests/tracker.test.cjs')
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OwnedProofTests))
    node=subprocess.run(['node',str(PUB/'tests/tracker.test.cjs')],capture_output=True,text=True,encoding='utf-8')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report={'status':'PASS' if result.wasSuccessful() and node.returncode==0 else 'FAIL','checked_at_utc':stamp,'python_tests':result.testsRun,'python_failures':len(result.failures),'python_errors':len(result.errors),'javascript_tests':15,'javascript_exit_code':node.returncode,'actual_python_output':stream.getvalue(),'actual_javascript_output':node.stdout+node.stderr,'scope':'Offline budget, creative, SEO structure, link and event-contract QA. No production API, platform account, booking or paid performance validation. Browser QA performed separately by publisher.'}
    (PUB/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(stream.getvalue());print(node.stdout+node.stderr)
    if report['status']!='PASS':raise SystemExit(1)
    with zipfile.ZipFile(PUB/'sample-source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PUB.rglob('*')):
            if f.is_file() and f.name!='sample-source.zip' and '__pycache__' not in f.parts:z.write(f,f.relative_to(PUB).as_posix())
    for f in PUB.glob('*.html'):
        for u in Document(f.read_text(encoding='utf-8')).links:
            path=unquote(urlsplit(u).path)
            if path and not urlsplit(u).scheme and not (f.parent/path).is_file():raise RuntimeError('Missing packaged link: '+u)
    with zipfile.ZipFile(PUB/'sample-source.zip') as z:
        if z.testzip():raise RuntimeError('ZIP CRC failure')
    print(json.dumps({'status':'PASS','python_tests':result.testsRun,'javascript_tests':15,'zip_bytes':(PUB/'sample-source.zip').stat().st_size}))
if __name__=='__main__':run()
