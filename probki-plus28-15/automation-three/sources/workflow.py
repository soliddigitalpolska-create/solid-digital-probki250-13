"""Three own, offline business workflow demos. Python standard library only.
No email transport, no paid API/LLM, no real customer data. Not a hosted service.
"""
from pathlib import Path
from contextlib import contextmanager
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit
import urllib.request,urllib.error,json,csv,sqlite3,threading,time,html,datetime

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
class BlockedOutbound(ValueError):pass

class Workspace:
 def __init__(self,root):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
  for name in ['documents','reports']: (self.root/name).mkdir(exist_ok=True)
  self.db=self.root/'workflow.sqlite';self.allowed_fixture_urls=set()
  with self.connection() as con:
   con.executescript('''
CREATE TABLE IF NOT EXISTS contacts(id TEXT PRIMARY KEY,name TEXT,email TEXT);
CREATE TABLE IF NOT EXISTS processed(key TEXT PRIMARY KEY,done_at TEXT);
CREATE TABLE IF NOT EXISTS dead_letters(id INTEGER PRIMARY KEY,workflow TEXT,key TEXT,reason TEXT,at TEXT);
CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,buyer TEXT,quantity INTEGER,unit_cents INTEGER,review_status TEXT,reviewer TEXT,document TEXT);
CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY,document_name TEXT,status TEXT,email_sent INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY,subject TEXT,body TEXT,category TEXT,review_status TEXT DEFAULT 'pending',reviewer TEXT);
CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,category TEXT,status TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,at TEXT,kind TEXT,payload TEXT);
''')
 @contextmanager
 def connection(self):
  con=sqlite3.connect(self.db,timeout=10)
  try:
   yield con;con.commit()
  except BaseException:con.rollback();raise
  finally:con.close()
 def event(self,kind,**payload):
  with self.connection() as con:con.execute('INSERT INTO events(at,kind,payload) VALUES(?,?,?)',(now(),kind,json.dumps(payload,ensure_ascii=False)))
 def count(self,table):
  if table not in {'contacts','processed','dead_letters','orders','outbox','tickets','tasks','events'}:raise ValueError('Unknown table')
  with self.connection() as con:return con.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
 def csv_to_crm(self,path,client):
  result={'workflow':'CSV → CRM fixture','created':0,'skipped':0,'invalid':0,'dead_letter':0}
  with open(path,encoding='utf-8',newline='') as f:
   reader=csv.DictReader(f)
   if reader.fieldnames!=['external_id','name','email']:raise ValueError('CSV schema mismatch')
   for line,row in enumerate(reader,2):
    id=row['external_id'].strip();name=row['name'].strip();email=row['email'].strip()
    if not id or not name or '@' not in email or not email.endswith('.invalid'):
     result['invalid']+=1;self.event('csv_rejected',line=line,reason='invalid own-demo identifier/name/email');continue
    key='crm:'+id
    with self.connection() as con:done=con.execute('SELECT 1 FROM processed WHERE key=?',(key,)).fetchone()
    if done:result['skipped']+=1;continue
    try:client.request('POST','/contacts',{'id':id,'name':name,'email':email})
    except Exception as exc:
     with self.connection() as con:con.execute('INSERT INTO dead_letters(workflow,key,reason,at) VALUES(?,?,?,?)',('csv_crm',key,str(exc),now()))
     result['dead_letter']+=1;self.event('dead_letter',workflow='csv_crm',key=key);continue
    with self.connection() as con:con.execute('INSERT OR IGNORE INTO processed VALUES(?,?)',(key,now()))
    result['created']+=1;self.event('crm_contact_confirmed',key=key)
  return result
 def stage_orders(self,path):
  result={'workflow':'Orders → human review → document','pending':0,'invalid':0,'duplicates':0}
  with open(path,encoding='utf-8',newline='') as f:
   reader=csv.DictReader(f)
   if reader.fieldnames!=['id','buyer','quantity','unit_net']:raise ValueError('CSV schema mismatch')
   for row in reader:
    try:
     id=row['id'].strip();buyer=row['buyer'].strip();qty=int(row['quantity']);money=Decimal(row['unit_net'])
     if not id or not buyer or not 0<qty<=1000 or not money.is_finite() or not 0<money<=Decimal('1000000'):raise ValueError('Invalid order')
     cents=int((money*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except (ValueError,InvalidOperation,TypeError):result['invalid']+=1;self.event('order_rejected',id=row.get('id'),reason='invalid quantity/amount/fields');continue
    with self.connection() as con:
     inserted=con.execute('INSERT OR IGNORE INTO orders VALUES(?,?,?,?,?,?,?)',(id,buyer,qty,cents,'pending',None,None)).rowcount
    result['pending' if inserted else 'duplicates']+=1
  return result
 def approve_order(self,id,reviewer,client):
  if not reviewer.strip():raise ValueError('Explicit named human reviewer required')
  with self.connection() as con:row=con.execute('SELECT buyer,quantity,unit_cents,review_status,document FROM orders WHERE id=?',(id,)).fetchone()
  if row is None:raise ValueError('Unknown staged order')
  buyer,qty,cents,state,doc=row;total=f'{Decimal(qty*cents)/100:.2f}'
  # Idempotent API upsert allows safe retry if local document save failed previously.
  filename='order-'+''.join(c for c in id if c.isalnum() or c in '-_')+'.html'
  with self.connection() as con:con.execute('UPDATE orders SET review_status=?,reviewer=? WHERE id=?',('approved',reviewer,id))
  client.request('POST','/outbox',{'id':id,'document_name':filename})
  doc=self.root/'documents'/filename
  doc.write_text('<!doctype html><html lang="pl"><meta charset="utf-8"><title>Własne potwierdzenie demonstracyjne</title><h1>Potwierdzenie zamówienia — fikcyjny przykład</h1><p>To nie jest faktura ani dokument rzeczywistej transakcji.</p><dl><dt>Numer</dt><dd>'+html.escape(id)+'</dd><dt>Nabywca</dt><dd>'+html.escape(buyer)+'</dd><dt>Ilość</dt><dd>'+str(qty)+'</dd><dt>Wartość netto PLN</dt><dd>'+total+'</dd><dt>Ręcznie zaakceptował</dt><dd>'+html.escape(reviewer)+'</dd></dl><p>Status: zapisane lokalnie do outbox. Żadna wiadomość nie została wysłana.</p></html>',encoding='utf-8')
  with self.connection() as con:con.execute('UPDATE orders SET review_status=?,reviewer=?,document=? WHERE id=?',('approved',reviewer,str(doc),id))
  self.event('order_human_approved',id=id,reviewer=reviewer,email_sent=False)
  return {'id':id,'document':str(doc),'net_total':total,'email_sent':False,'outbox_status':'staged_not_sent'}
 def review_ticket(self,id,decision,reviewer,client):
  if decision not in ('approved','rejected') or not reviewer.strip():raise ValueError('Explicit human decision and reviewer required')
  with self.connection() as con:row=con.execute('SELECT category FROM tickets WHERE id=?',(id,)).fetchone()
  if not row:raise ValueError('Unknown ticket')
  with self.connection() as con:con.execute('UPDATE tickets SET review_status=?,reviewer=? WHERE id=?',(decision,reviewer,id))
  if decision=='approved':client.request('POST','/tasks',{'id':id,'category':row[0]})
  self.event('ticket_human_review',id=id,decision=decision,reviewer=reviewer)
 def ticket_report(self):
  path=self.root/'reports/tickets.csv'
  with self.connection() as con:rows=con.execute('SELECT id,subject,category,review_status,reviewer FROM tickets ORDER BY id').fetchall()
  with path.open('w',encoding='utf-8',newline='') as f:
   w=csv.writer(f);w.writerow(['id','subject','category','review_status','reviewer'])
   for row in rows:w.writerow([("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v) for v in row])
  self.event('report_created',filename=path.name,rows=len(rows));return str(path)
 def export_evidence(self):
  result={'checked_at':now(),'own_fictional_local_demo_only':True,'email_sent':False,'LLM_used':False,'tables':{}}
  with self.connection() as con:
   for name in ['contacts','orders','outbox','tickets','tasks','dead_letters','events']:
    cur=con.execute('SELECT * FROM '+name);cols=[x[0] for x in cur.description];result['tables'][name]=[dict(zip(cols,r)) for r in cur.fetchall()]
  return result

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):raise BlockedOutbound('Redirect blocked: local fixture only')

class Client:
 def __init__(self,base,workspace):
  if base not in workspace.allowed_fixture_urls:raise BlockedOutbound('Only the explicitly started own local fixture URL is allowed')
  self.base=base;self.workspace=workspace;self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 def request(self,method,path,payload=None):
  if path not in {'/contacts','/outbox','/tasks','/webhooks/tickets','/health'}:raise BlockedOutbound('Endpoint outside fixed fixture allowlist')
  data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
  for attempt in range(1,4):
   try:
    req=urllib.request.Request(self.base+path,data=data,method=method,headers={'Content-Type':'application/json'})
    with self.opener.open(req,timeout=3) as response:return json.loads(response.read(65536))
   except urllib.error.HTTPError as exc:
    if exc.code in (429,500,503) and attempt<3:
     self.workspace.event('api_retry',path=path,status=exc.code,attempt=attempt,backoff_seconds=0.02*attempt);time.sleep(0.02*attempt);continue
    if exc.code in (400,422):raise ValueError('Fixture validation HTTP '+str(exc.code)) from None
    raise RuntimeError('Fixture failed after '+str(attempt)+' attempt(s), HTTP '+str(exc.code)) from None

class LocalAPI:
 def __init__(self,workspace):self.workspace=workspace;self.attempts={};self.lock=threading.Lock()
 def start(self):
  owner=self;ws=self.workspace
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def respond(self,status,obj):
    data=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   def do_GET(self):self.respond(200,{'status':'own_local_fixture','email_transport':False}) if self.path=='/health' else self.respond(404,{'error':'unknown'})
   def do_POST(self):
    try:
     length=int(self.headers.get('Content-Length','0'))
     if not 0<length<=65536:raise ValueError()
     data=json.loads(self.rfile.read(length));id=data.get('id','')
     if not isinstance(id,str) or not id or len(id)>80:raise ValueError()
     key='POST:'+self.path+':'+id
     with owner.lock:owner.attempts[key]=owner.attempts.get(key,0)+1;attempt=owner.attempts[key]
     if self.path=='/contacts':
      if not data.get('name') or not isinstance(data.get('email'),str) or not data['email'].endswith('.invalid'):raise ValueError()
      if id=='FAIL':self.respond(503,{'error':'injected permanent failure'});return
      if id=='A1' and attempt<=2:self.respond([429,503][attempt-1],{'error':'injected transient failure'});return
      with ws.connection() as con:con.execute('INSERT OR IGNORE INTO contacts VALUES(?,?,?)',(id,data['name'],data['email']))
      self.respond(200,{'id':id,'persisted':True});return
     if self.path=='/outbox':
      if not data.get('document_name'):raise ValueError()
      with ws.connection() as con:
       if not con.execute("SELECT 1 FROM orders WHERE id=? AND review_status='approved' AND reviewer IS NOT NULL",(id,)).fetchone():raise ValueError()
       con.execute('INSERT OR IGNORE INTO outbox VALUES(?,?,?,0)',(id,data['document_name'],'staged_not_sent'))
      self.respond(200,{'id':id,'staged':True,'email_sent':False});return
     if self.path=='/webhooks/tickets':
      subject=data.get('subject');body=data.get('body')
      if not isinstance(subject,str) or not isinstance(body,str) or not subject.strip() or not body.strip():raise ValueError()
      content=(subject+' '+body).lower();category='billing' if any(k in content for k in ['płatno','faktur','payment']) else 'support' if any(k in content for k in ['błąd','nie działa','error']) else 'manual'
      with ws.connection() as con:
       con.execute('INSERT OR IGNORE INTO tickets(id,subject,body,category) VALUES(?,?,?,?)',(id,subject,body,category));category=con.execute('SELECT category FROM tickets WHERE id=?',(id,)).fetchone()[0]
      ws.event('ticket_rule_classified',id=id,category=category,LLM=False,human_required=True);self.respond(200,{'id':id,'category':category,'human_required':True});return
     if self.path=='/tasks':
      with ws.connection() as con:
       if not con.execute("SELECT 1 FROM tickets WHERE id=? AND review_status='approved' AND reviewer IS NOT NULL",(id,)).fetchone():raise ValueError()
       con.execute('INSERT OR IGNORE INTO tasks VALUES(?,?,?)',(id,data.get('category','manual'),'ready_after_human_review'))
      self.respond(200,{'id':id,'created':True});return
     self.respond(404,{'error':'unknown'})
    except (ValueError,TypeError,AttributeError,json.JSONDecodeError):self.respond(422,{'error':'invalid fixed schema'})
  self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.url='http://127.0.0.1:'+str(self.server.server_port);ws.allowed_fixture_urls.add(self.url)
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();return self
 def close(self):self.server.shutdown();self.server.server_close();self.thread.join(timeout=3);self.workspace.allowed_fixture_urls.discard(self.url)
