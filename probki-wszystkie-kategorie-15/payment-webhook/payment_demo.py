"""Fictional payment protocol, bound only to 127.0.0.1.
Not a real operator adapter; the public demo key is not a credential.
No real money, external requests, customer data, email or fulfillment transport.
"""
from contextlib import contextmanager,closing
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import hashlib,hmac,json,sqlite3,threading,time,uuid
from urllib.parse import urlsplit

DEMO_KEY=b'demo-only-not-a-real-payment-key'
class Rejected(Exception):
    def __init__(self,code,message):self.code=code;self.message=message;super().__init__(message)

class Store:
    def __init__(self,path):
        self.path=Path(path)
        with closing(self.connect()) as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.executescript('''
            CREATE TABLE orders(order_id TEXT PRIMARY KEY,session_id TEXT UNIQUE NOT NULL,amount_minor INTEGER NOT NULL CHECK(amount_minor>0),currency TEXT NOT NULL,personalization TEXT NOT NULL,payment_status TEXT NOT NULL);
            CREATE TABLE events(event_id TEXT PRIMARY KEY,body_sha256 TEXT NOT NULL,event_type TEXT NOT NULL,order_id TEXT NOT NULL);
            CREATE TABLE fulfillment(order_id TEXT PRIMARY KEY,status TEXT NOT NULL);
            CREATE TABLE refunds(order_id TEXT PRIMARY KEY,event_id TEXT UNIQUE NOT NULL);
            ''')
    def connect(self):
        con=sqlite3.connect(self.path,timeout=10,isolation_level=None);con.row_factory=sqlite3.Row
        con.execute('PRAGMA busy_timeout=10000');return con
    @contextmanager
    def transaction(self):
        con=self.connect()
        try:con.execute('BEGIN IMMEDIATE');yield con;con.commit()
        except Exception:con.rollback();raise
        finally:con.close()
    def create_order(self,data):
        amount=data.get('amount_minor');currency=data.get('currency')
        if type(amount) is not int or amount<=0:raise Rejected(400,'amount_minor must be positive integer minor units')
        # This fixture has one catalogue item. Production prices must come from
        # the authorized personalization/order API, never from a browser field.
        if amount!=34900:raise Rejected(400,'price does not match the server-side demo catalogue')
        if currency!='PLN':raise Rejected(400,'demo catalogue currency is PLN')
        personalization=data.get('personalization',{})
        if not isinstance(personalization,dict):raise Rejected(400,'personalization must be an object')
        oid='ord_demo_'+uuid.uuid4().hex[:12];sid='session_demo_'+uuid.uuid4().hex[:12]
        with self.transaction() as con:con.execute('INSERT INTO orders VALUES(?,?,?,?,?,?)',(oid,sid,amount,currency,json.dumps(personalization,ensure_ascii=False),'awaiting_payment'))
        return {'order_id':oid,'session_id':sid,'amount_minor':amount,'currency':currency,'payment_status':'awaiting_payment','demo_checkout':'/demo-checkout/'+sid}
    def state(self,oid):
        with closing(self.connect()) as con:
            row=con.execute('SELECT * FROM orders WHERE order_id=?',(oid,)).fetchone()
            if not row:raise Rejected(404,'order not found')
            result=dict(row);ful=con.execute('SELECT status FROM fulfillment WHERE order_id=?',(oid,)).fetchone()
            result['fulfillment_status']=ful['status'] if ful else None
            result['fulfillment_rows']=con.execute('SELECT COUNT(*) FROM fulfillment WHERE order_id=?',(oid,)).fetchone()[0]
            result['refund_rows']=con.execute('SELECT COUNT(*) FROM refunds WHERE order_id=?',(oid,)).fetchone()[0]
            result['event_rows']=con.execute('SELECT COUNT(*) FROM events WHERE order_id=?',(oid,)).fetchone()[0]
            return result
    def webhook(self,raw,headers):
        try:timestamp=int(headers.get('X-Demo-Timestamp',''))
        except ValueError:raise Rejected(401,'missing/invalid timestamp')
        if abs(time.time()-timestamp)>300:raise Rejected(401,'stale timestamp')
        supplied=headers.get('X-Demo-Signature','')
        expected=hmac.new(DEMO_KEY,str(timestamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(supplied,expected):raise Rejected(401,'invalid signature')
        try:event=json.loads(raw)
        except json.JSONDecodeError:raise Rejected(400,'malformed event JSON')
        if not isinstance(event,dict):raise Rejected(400,'event must be an object')
        kind=event.get('type');eid=event.get('id');sid=event.get('session_id')
        if kind not in ('payment.paid','payment.failed','payment.canceled','payment.refunded'):raise Rejected(400,'unsupported demo event type')
        if not isinstance(eid,str) or not eid or not isinstance(sid,str):raise Rejected(400,'missing event/session identifier')
        body_hash=hashlib.sha256(raw).hexdigest()
        with self.transaction() as con:
            old=con.execute('SELECT body_sha256 FROM events WHERE event_id=?',(eid,)).fetchone()
            if old:
                if old['body_sha256']!=body_hash:raise Rejected(409,'event id collision with changed payload')
                return {'accepted':True,'duplicate':True}
            order=con.execute('SELECT * FROM orders WHERE session_id=?',(sid,)).fetchone()
            if not order:raise Rejected(404,'unknown session')
            if type(event.get('amount_minor')) is not int or event['amount_minor']!=order['amount_minor'] or event.get('currency')!=order['currency']:raise Rejected(409,'amount or currency mismatch')
            oid=order['order_id'];state=order['payment_status']
            if kind=='payment.paid':
                if state not in ('awaiting_payment','paid'):raise Rejected(409,'late payment requires manual reconciliation')
                con.execute("UPDATE orders SET payment_status='paid' WHERE order_id=?",(oid,))
                con.execute("INSERT OR IGNORE INTO fulfillment VALUES(?,'queued')",(oid,))
            elif kind=='payment.refunded':
                if state!='paid':raise Rejected(409,'refund without a prior confirmed payment')
                con.execute("UPDATE orders SET payment_status='refunded' WHERE order_id=?",(oid,))
                con.execute('INSERT INTO refunds VALUES(?,?)',(oid,eid))
                con.execute("UPDATE fulfillment SET status=CASE WHEN status='sent_to_demo_realization' THEN 'recall_required' ELSE 'canceled' END WHERE order_id=?",(oid,))
            else:
                if state!='awaiting_payment':raise Rejected(409,'cannot overwrite a settled payment with failure/cancellation')
                con.execute('UPDATE orders SET payment_status=? WHERE order_id=?',('failed' if kind=='payment.failed' else 'canceled',oid))
            con.execute('INSERT INTO events VALUES(?,?,?,?)',(eid,body_hash,kind,oid))
        return {'accepted':True,'duplicate':False,'order_id':oid}
    def dispatch(self):
        # Only a local outbox acknowledgement, not a real fulfillment API call.
        with self.transaction() as con:
            rows=con.execute("SELECT f.order_id FROM fulfillment f JOIN orders o ON o.order_id=f.order_id WHERE f.status='queued' AND o.payment_status='paid' ORDER BY f.order_id").fetchall()
            ids=[row['order_id'] for row in rows]
            con.executemany("UPDATE fulfillment SET status='sent_to_demo_realization' WHERE order_id=?",[(oid,) for oid in ids])
        return {'dispatched':ids,'external_transport_called':False}

def handler_for(store):
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args):pass
        def reply(self,code,data):
            raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            try:
                path=urlsplit(self.path).path
                if path.startswith('/orders/'):return self.reply(200,store.state(path.split('/')[-1]))
                if path=='/return':return self.reply(200,{'payment_authority':False,'message':'Browser return is informational. Signed webhook is authoritative.'})
                raise Rejected(404,'unknown route')
            except Rejected as err:self.reply(err.code,{'error':err.message})
        def do_POST(self):
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<=0 or length>65536:raise Rejected(400,'invalid body size')
                raw=self.rfile.read(length)
                if self.path=='/webhook':return self.reply(200,store.webhook(raw,self.headers))
                try:data=json.loads(raw)
                except json.JSONDecodeError:raise Rejected(400,'malformed JSON')
                if not isinstance(data,dict):raise Rejected(400,'JSON object required')
                if self.path=='/orders':return self.reply(201,store.create_order(data))
                if self.path=='/dispatch':return self.reply(200,store.dispatch())
                raise Rejected(404,'unknown route')
            except Rejected as err:self.reply(err.code,{'error':err.message})
            except (ValueError,TypeError):self.reply(400,{'error':'invalid request value'})
    return Handler

@dataclass
class DemoServer:
    server:ThreadingHTTPServer
    thread:threading.Thread
    store:Store
    @property
    def base_url(self):return f'http://127.0.0.1:{self.server.server_port}'
    def close(self):self.server.shutdown();self.server.server_close();self.thread.join(timeout=5)

def start_demo(path):
    store=Store(path);server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(store));server.daemon_threads=True
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();return DemoServer(server,thread,store)
