import concurrent.futures,hashlib,hmac,json,sqlite3,subprocess,sys,time,unittest,urllib.error,urllib.request,zipfile
from pathlib import Path
import payment_demo
HERE=Path(__file__).resolve().parent
RESULTS=HERE/'results';RESULTS.mkdir(exist_ok=True)
db=RESULTS/'fictional-demo.sqlite'
if db.exists():raise SystemExit('Use a fresh result database; the previous proof is preserved')
server=payment_demo.start_demo(db);trace=[]
def http(path,data=None,headers=None):
    raw=None if data is None else json.dumps(data,separators=(',',':')).encode()
    request=urllib.request.Request(server.base_url+path,data=raw,headers={'Content-Type':'application/json',**(headers or {})})
    try:
        with urllib.request.urlopen(request,timeout=10) as r:code=r.status;result=json.loads(r.read())
    except urllib.error.HTTPError as e:code=e.code;result=json.loads(e.read())
    trace.append({'method':'GET' if data is None else 'POST','path':path,'http_status':code,'request':data,'response':result})
    return code,result
def order(label):
    code,data=http('/orders',{'amount_minor':34900,'currency':'PLN','personalization':{'engraving':label+' / OWN DEMO'}})
    assert code==201;return data
def event(order,kind,eid,**fields):return {'id':eid,'type':kind,'session_id':order['session_id'],'amount_minor':34900,'currency':'PLN',**fields}
def webhook(data,bad=False):
    stamp=str(int(time.time()));raw=json.dumps(data,separators=(',',':')).encode()
    signature='0'*64 if bad else hmac.new(payment_demo.DEMO_KEY,stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
    return http('/webhook',data,{'X-Demo-Timestamp':stamp,'X-Demo-Signature':signature})
try:
    paid=order('PAID');http('/return?session_id='+paid['session_id']+'&paid=true')
    assert http('/orders/'+paid['order_id'])[1]['payment_status']=='awaiting_payment'
    assert webhook(event(paid,'payment.paid','evt_bad_signature'),bad=True)[0]==401
    assert webhook(event(paid,'payment.paid','evt_bad_amount',amount_minor=1))[0]==409
    success=event(paid,'payment.paid','evt_paid')
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:retries=list(pool.map(lambda _:webhook(success),range(20)))
    assert all(code==200 for code,_ in retries)
    assert sum(not data['duplicate'] for _,data in retries)==1
    assert http('/dispatch',{})[1]['dispatched']==[paid['order_id']]
    assert http('/dispatch',{})[1]['dispatched']==[]
    assert webhook(event(paid,'payment.refunded','evt_late_refund'))[0]==200
    assert http('/orders/'+paid['order_id'])[1]['fulfillment_status']=='recall_required'
    canceled=order('CANCELED');assert webhook(event(canceled,'payment.canceled','evt_cancel'))[0]==200
    failed=order('FAILED');assert webhook(event(failed,'payment.failed','evt_failed'))[0]==200
    early=order('EARLY REFUND');assert webhook(event(early,'payment.paid','evt_early_paid'))[0]==200
    refund=event(early,'payment.refunded','evt_early_refund');assert webhook(refund)[0]==200;assert webhook(refund)[1]['duplicate']
    assert http('/dispatch',{})[1]['dispatched']==[]
    final_states=[http('/orders/'+x['order_id'])[1] for x in [paid,canceled,failed,early]]
finally:server.close()
(RESULTS/'http-trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2),encoding='utf-8')
# Separate process, SQLite opened read-only, avoiding a self-reported in-memory state.
code="import json,sqlite3,sys;db=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;print(json.dumps({t:[dict(r) for r in db.execute('SELECT * FROM '+t)] for t in ['orders','events','fulfillment','refunds']}));db.close()"
readback=subprocess.run([sys.executable,'-c',code,str(db)],capture_output=True,text=True,check=True)
persisted=json.loads(readback.stdout)
assert len(persisted['orders'])==4 and len(persisted['events'])==6 and len(persisted['fulfillment'])==2 and len(persisted['refunds'])==2
(RESULTS/'independent-readback.json').write_text(json.dumps(persisted,ensure_ascii=False,indent=2),encoding='utf-8')
tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_payment.py','-v'],capture_output=True,text=True)
(HERE/'tests.log').write_text(tests.stdout+'\n'+tests.stderr,encoding='utf-8');assert tests.returncode==0
qa={'own_fictional_demo':True,'real_operator_adapter':False,'real_money_processed':0,'external_payment_calls':0,'external_fulfillment_calls':0,'customer_data_used':False,'public_key_is_dummy_not_a_credential':True,'bound_to_loopback_only':True,'test_count':15,'tests_passed':15,'tests_exit_code':tests.returncode,'concurrent_signed_retries':20,'concurrent_fulfillment_rows_created':1,'persisted_order_count':4,'persisted_event_count':6,'persisted_fulfillment_count':2,'persisted_refund_count':2,'independent_sqlite_readback_process':True,'invalid_signature_http':401,'wrong_amount_http':409,'browser_return_is_not_payment_authority':True,'states':final_states}
(HERE/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'README.txt').write_text('Własny fikcyjny protokół płatności, nie adapter realnego operatora. Python 3.13, tylko biblioteka standardowa.\nTesty: python -m unittest discover -s . -p test_payment.py -v\nDemo: python run_demo.py (wymaga nowej bazy results/fictional-demo.sqlite, nie nadpisuje poprzedniej).\nHMAC SHA256 timestamp.rawJSON. Publiczny klucz ma nazwę demo-only-not-a-real-payment-key i NIE jest rzeczywistym sekretem.\nSerwer wiąże wyłącznie127.0.0.1; nie wykonuje zewnętrznych płatności, maili ani wywołań realizacji.\nProdukcja wymaga adaptera operatora, HTTPS, autoryzowanego API systemu zamówień, bezpiecznych sekretów oraz idempotentnego odbiorcy zewnętrznej kolejki. Cena2200NET dotyczy pełnego uzgodnionego1API/1operatora, nie tego mocka.\n',encoding='utf-8')
html='''<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'self';style-src 'unsafe-inline';script-src 'none';connect-src 'none';form-action 'none'"><title>Podpisany webhook i bezpieczne statusy zamówienia — własny test</title><style>body{margin:0;background:#f4f1e9;color:#163b36;font:17px/1.7 Arial,sans-serif}main{max-width:1080px;margin:auto;padding:34px 24px}h1{font:normal clamp(40px,6vw,70px)/1.05 Georgia,serif}h2{font:normal 34px Georgia,serif}.tag{font-size:12px;letter-spacing:2px}.note{background:#e6dfd0;padding:22px;border-left:4px solid #ad764d}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.metric{padding:20px;background:#163b36;color:white}.metric b{display:block;font-size:34px}.flow{display:flex;flex-wrap:wrap;gap:12px}.flow span{padding:15px;background:white;border:1px solid #d7d5c8}.card{background:white;padding:24px;border:1px solid #ddd9cd;margin:20px 0}a{color:#146453}section{margin:42px 0}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px;border-bottom:1px solid #ddd;text-align:left}.small{font-size:13px}@media(max-width:650px){.grid{grid-template-columns:1fr}}</style><main><p class="tag">SOLID DIGITAL / WŁASNY TEST HTTP + SQLITE</p><h1>„Zapłacono” wymaga dowodu.</h1><p>Podpisany webhook, kontrola kwoty i waluty, trwała idempotencja oraz osobna kolejka przekazania zamówienia. Powrót z przeglądarki nie potwierdza płatności.</p><div class="note"><strong>Jawny fikcyjny protokół.</strong> To własna działająca demonstracja lokalnych żądań HTTP i SQLite, nie adapter realnego operatora ani płatne wdrożenie klientowskie. Nie przetworzono pieniędzy, sekretów operatora lub danych klientów. Pokazane „przekazanie do realizacji” jest lokalnym testem outbox; nie wykonuje zewnętrznego zlecenia.</div><section class="grid"><div class="metric"><b>15 / 15</b>testów integracyjnych</div><div class="metric"><b>20 → 1</b>powtórzeń callbacku → rekord realizacji</div><div class="metric"><b>4</b>trwałe scenariusze zamówień</div></section><section><h2>Pełna lokalna ścieżka</h2><div class="flow"><span>Personalizacja</span><span>Sesja zamówienia</span><span>Podpis HMAC</span><span>Kwota + waluta</span><span>Status opłacone</span><span>Kolejka realizacji</span></div><p>Każdy krok został wykonany jako żądanie HTTP do serwera 127.0.0.1. Kwota jest sprawdzana względem katalogu serwera. Callback jest weryfikowany na surowych bajtach, z oknem czasu i porównaniem stałoczasowym. Transakcja SQLite zapisuje zdarzenie oraz zmianę zamówienia razem.</p><p><a href="results/http-trace.json">Pełny rzeczywisty ślad HTTP</a> · <a href="results/independent-readback.json">Niezależny odczyt SQLite</a> · <a href="qa.json">Raport QA</a></p></section><section><h2>Co dzieje się z wyjątkami</h2><div class="card"><table><tr><th>Zdarzenie</th><th>Zweryfikowane zachowanie</th></tr><tr><td>Powrót ?paid=true w przeglądarce</td><td>Nadal oczekuje płatności; nie tworzy realizacji</td></tr><tr><td>Błędny podpis / stary timestamp</td><td>401, status płatności bez zmiany</td></tr><tr><td>Inna kwota / waluta</td><td>409, brak realizacji</td></tr><tr><td>20 jednoczesnych identycznych callbacków</td><td>Jeden zapis zdarzenia i jeden rekord realizacji</td></tr><tr><td>Ten sam ID z inną treścią</td><td>409, nie nadpisuje płatności</td></tr><tr><td>Nieudana lub anulowana płatność</td><td>Odpowiedni status i zero przekazań</td></tr><tr><td>Zwrot przed przekazaniem</td><td>Anuluje oczekującą kolejkę</td></tr><tr><td>Zwrot po przekazaniu</td><td>Jawny status recall_required; nie udaje cofnięcia wykonanej pracy</td></tr></table></div></section><section><h2>Rzeczywiste źródła i testy</h2><p><a href="payment_demo.py">Implementacja</a> · <a href="test_payment.py">15 testów</a> · <a href="tests.log">Zapis przebiegu</a> · <a href="payment-proof-source.zip">Pakiet źródłowy ZIP</a></p><p>Po zatrzymaniu serwera oddzielny proces otworzył SQLite w trybie tylko do odczytu: 4 zamówienia, 6 zaakceptowanych zdarzeń, 2 rekordy realizacji i 2 rekordy zwrotu. Nie jest to jedynie opis oczekiwanego zachowania.</p></section><section><h2>Pełne wdrożenie strony i integracji</h2><p><strong>2200 zł netto / 21 dni od wpłaty Useme.</strong> Gotowa strona HTML/CSS/JS na domenie i Hostingerze, jeden zewnętrzny system personalizacji/zamówień, jeden uzgodniony operator płatności, statusy i powiadomienia serwerowe, przekazanie opłaconych zamówień oraz testy udanych, nieudanych, przerwanych i anulowanych płatności oraz zwrotów na telefonie i komputerze.</p><p class="small">Przed finansowaniem poznajemy dokumentację API, możliwości pakietu Hostinger, wybranego operatora i jego sandbox. Produkcyjny adapter, sposób autoryzacji i konfiguracja sekretów są wdrażane dla rzeczywistego operatora; fikcyjnego HMAC z tej próbki nie przedstawiamy jako gotowej integracji jego API. Kwota brutto i obowiązkowe koszty są potwierdzane w kalkulatorze przed wpłatą.</p></section></main></html>'''
(HERE/'index.html').write_text(html,encoding='utf-8')
with zipfile.ZipFile(HERE/'payment-proof-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in ['payment_demo.py','test_payment.py','run_demo.py','README.txt','qa.json','tests.log','results/http-trace.json','results/independent-readback.json']:archive.write(HERE/name,name)
print(json.dumps({k:v for k,v in qa.items() if k!='states'},ensure_ascii=False,indent=2))
