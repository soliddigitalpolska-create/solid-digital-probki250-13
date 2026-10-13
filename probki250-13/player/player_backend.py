"""LOCAL ENGINEERING PROTOTYPE. SQLite links/leases, own files, simulated payments.

No PSP integration, no production CDN, no DRM. Binds loopback only.
Secrets must be supplied in environment; no default secrets and no secret logging.
"""
from contextlib import contextmanager
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import random
import re
import secrets
import sqlite3
import time
from urllib.parse import parse_qs, urlsplit


class Problem(Exception):
    def __init__(self,status,message):
        self.status,self.message=status,message
        super().__init__(message)


class Store:
    def __init__(self,db,secret,catalog,clock=time.time):
        if len(secret)<32:raise ValueError('Signing secret must contain at least32bytes')
        self.db,self.secret,self.catalog,self.clock=Path(db),secret,catalog,clock
        self.db.parent.mkdir(parents=True,exist_ok=True)
        with self.connection() as conn:
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS links(id TEXT PRIMARY KEY,expires_at INTEGER NOT NULL,revoked INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS leases(link_id TEXT PRIMARY KEY REFERENCES links(id),device TEXT NOT NULL,until_at INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS cycles(link_id TEXT NOT NULL REFERENCES links(id),profile TEXT NOT NULL,remaining TEXT NOT NULL,last TEXT,PRIMARY KEY(link_id,profile));
            CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,amount_minor INTEGER NOT NULL,currency TEXT NOT NULL,ttl INTEGER NOT NULL,status TEXT NOT NULL,link_id TEXT REFERENCES links(id));
            CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,payload_hash TEXT NOT NULL,result TEXT NOT NULL);
            ''')

    @contextmanager
    def connection(self,transaction=False):
        conn=sqlite3.connect(self.db,timeout=10,isolation_level=None)
        conn.row_factory=sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA busy_timeout=10000')
        try:
            if transaction:conn.execute('BEGIN IMMEDIATE')
            yield conn
            if transaction:conn.commit()
        except Exception:
            if transaction:conn.rollback()
            raise
        finally:conn.close()

    def pack(self,payload):
        body=base64.urlsafe_b64encode(json.dumps(payload,separators=(',',':'),sort_keys=True).encode()).decode().rstrip('=')
        signature=base64.urlsafe_b64encode(hmac.new(self.secret,body.encode(),hashlib.sha256).digest()).decode().rstrip('=')
        return '1.'+body+'.'+signature

    def unpack(self,token,purpose):
        try:
            if not isinstance(token,str) or len(token)>2048:raise ValueError()
            version,body,signature=token.split('.')
            if version!='1' or not re.fullmatch('[A-Za-z0-9_-]+',body+signature):raise ValueError()
            expected=base64.urlsafe_b64encode(hmac.new(self.secret,body.encode(),hashlib.sha256).digest()).decode().rstrip('=')
            if not hmac.compare_digest(expected,signature):raise ValueError()
            payload=json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
            if payload.get('purpose')!=purpose or payload.get('v')!=1 or payload['expires_at']<=int(self.clock()):raise ValueError()
            return payload
        except (ValueError,KeyError,TypeError,json.JSONDecodeError):raise Problem(403,'Link invalid, expired or revoked') from None

    def _link(self,conn,token):
        payload=self.unpack(token,'link')
        row=conn.execute('SELECT * FROM links WHERE id=?',(payload['jti'],)).fetchone()
        if not row or row['revoked'] or row['expires_at']<=int(self.clock()) or row['expires_at']!=payload['expires_at']:
            raise Problem(403,'Link invalid, expired or revoked')
        return row

    def _result(self,row):
        return {'id':row['id'],'expires_at':row['expires_at'],
                'token':self.pack({'v':1,'purpose':'link','jti':row['id'],'expires_at':row['expires_at']})}

    def _issue(self,conn,ttl):
        if not isinstance(ttl,int) or isinstance(ttl,bool) or not 1<=ttl<=366*86400:raise Problem(400,'Invalid link duration')
        identifier=secrets.token_hex(16)
        conn.execute('INSERT INTO links(id,expires_at) VALUES(?,?)',(identifier,int(self.clock())+ttl))
        return self._result(conn.execute('SELECT * FROM links WHERE id=?',(identifier,)).fetchone())

    def issue(self,ttl):
        with self.connection(True) as conn:return self._issue(conn,ttl)

    def revoke(self,identifier):
        with self.connection(True) as conn:
            conn.execute('UPDATE links SET revoked=1 WHERE id=?',(identifier,))
            conn.execute('DELETE FROM leases WHERE link_id=?',(identifier,))
        return {'revoked':True}

    def _device(self,device):
        if not isinstance(device,str) or not re.fullmatch('[A-Za-z0-9_-]{8,100}',device):raise Problem(400,'Invalid device identifier')
        return hashlib.sha256(device.encode()).hexdigest()

    def _owner(self,conn,row,device):
        device=self._device(device)
        lease=conn.execute('SELECT * FROM leases WHERE link_id=?',(row['id'],)).fetchone()
        if not lease or lease['device']!=device or lease['until_at']<=int(self.clock()):raise Problem(409,'This link is active on another device or lease has expired')
        return device

    def acquire(self,token,device):
        device=self._device(device)
        with self.connection(True) as conn:
            row=self._link(conn,token)
            lease=conn.execute('SELECT * FROM leases WHERE link_id=?',(row['id'],)).fetchone()
            if lease and lease['until_at']>int(self.clock()) and lease['device']!=device:raise Problem(409,'This link is active on another device')
            until=min(int(self.clock())+30,row['expires_at'])
            conn.execute('INSERT INTO leases(link_id,device,until_at) VALUES(?,?,?) ON CONFLICT(link_id) DO UPDATE SET device=excluded.device,until_at=excluded.until_at',(row['id'],device,until))
            return {'active':True,'lease_until':until,'profiles':list(self.catalog),'mode':'local-prototype'}

    def heartbeat(self,token,device):
        with self.connection(True) as conn:
            row=self._link(conn,token)
            self._owner(conn,row,device)
            until=min(int(self.clock())+30,row['expires_at'])
            conn.execute('UPDATE leases SET until_at=? WHERE link_id=?',(until,row['id']))
            return {'active':True,'lease_until':until}

    def release(self,token,device):
        with self.connection(True) as conn:
            row=self._link(conn,token)
            self._owner(conn,row,device)
            conn.execute('DELETE FROM leases WHERE link_id=?',(row['id'],))
            return {'released':True}

    def next_track(self,token,device,profile):
        if profile not in self.catalog:raise Problem(400,'Unknown profile')
        with self.connection(True) as conn:
            row=self._link(conn,token)
            device_hash=self._owner(conn,row,device)
            state=conn.execute('SELECT * FROM cycles WHERE link_id=? AND profile=?',(row['id'],profile)).fetchone()
            remaining=json.loads(state['remaining']) if state else []
            last=state['last'] if state else None
            if not remaining:
                remaining=list(self.catalog[profile]);random.SystemRandom().shuffle(remaining)
                if len(remaining)>1 and remaining[0]==last:remaining[0],remaining[1]=remaining[1],remaining[0]
            if not remaining:raise Problem(400,'Empty profile')
            track=remaining.pop(0)
            conn.execute('INSERT INTO cycles(link_id,profile,remaining,last) VALUES(?,?,?,?) ON CONFLICT(link_id,profile) DO UPDATE SET remaining=excluded.remaining,last=excluded.last',(row['id'],profile,json.dumps(remaining),track))
            ticket=self.pack({'v':1,'purpose':'media','jti':row['id'],'device':device_hash,'track':track,'expires_at':min(int(self.clock())+30,row['expires_at'])})
            return {'track':track,'ticket':ticket,'remaining_in_cycle':len(remaining),'url':f'/stream/{track}?ticket={ticket}'}

    def validate_media(self,ticket,track):
        payload=self.unpack(ticket,'media')
        if payload.get('track')!=track or track not in {item for values in self.catalog.values() for item in values}:raise Problem(403,'Invalid media ticket')
        with self.connection() as conn:
            row=conn.execute('SELECT * FROM links WHERE id=?',(payload['jti'],)).fetchone()
            lease=conn.execute('SELECT * FROM leases WHERE link_id=?',(payload['jti'],)).fetchone()
            if not row or row['revoked'] or row['expires_at']<=int(self.clock()) or not lease or lease['device']!=payload.get('device') or lease['until_at']<=int(self.clock()):raise Problem(403,'Media access is inactive')
        return track

    def create_test_order(self,identifier,amount_minor,ttl):
        if not isinstance(amount_minor,int) or isinstance(amount_minor,bool) or amount_minor<=0:raise Problem(400,'Invalid expected payment amount')
        if not isinstance(ttl,int) or not 1<=ttl<=366*86400:raise Problem(400,'Invalid duration')
        with self.connection(True) as conn:
            conn.execute('INSERT INTO orders(id,amount_minor,currency,ttl,status) VALUES(?,?,?, ?,?)',(identifier,amount_minor,'PLN',ttl,'created'))
        return {'order_id':identifier,'status':'created','mode':'SIMULATION_NO_PAYMENT'}

    def test_payment_event(self,raw,timestamp,signature,webhook_key):
        # Generic local simulator format; not any PSP's webhook contract.
        if abs(int(self.clock())-int(timestamp))>300:raise Problem(403,'Stale test event')
        expected=hmac.new(webhook_key,str(timestamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected,str(signature)):raise Problem(403,'Invalid test event signature')
        try:event=json.loads(raw)
        except (ValueError,TypeError):raise Problem(400,'Invalid test event') from None
        if set(event)!={'event_id','order_id','status','amount_minor','currency'} or event['status'] not in {'pending','paid','failed','refunded'}:raise Problem(400,'Invalid test event')
        digest=hashlib.sha256(raw).hexdigest()
        with self.connection(True) as conn:
            previous=conn.execute('SELECT * FROM events WHERE id=?',(event['event_id'],)).fetchone()
            if previous:
                if previous['payload_hash']!=digest:raise Problem(409,'Event identifier reused with different content')
                return json.loads(previous['result'])
            order=conn.execute('SELECT * FROM orders WHERE id=?',(event['order_id'],)).fetchone()
            if not order or event['amount_minor']!=order['amount_minor'] or event['currency']!=order['currency']:raise Problem(400,'Payment does not match registered test order')
            if order['status']=='refunded' and event['status']!='refunded':raise Problem(409,'Refunded order cannot be reactivated')
            result={'status':event['status'],'mode':'SIMULATION_NO_PAYMENT'}
            if event['status']=='paid':
                if order['link_id']:
                    result.update(self._result(conn.execute('SELECT * FROM links WHERE id=?',(order['link_id'],)).fetchone()))
                else:
                    result.update(self._issue(conn,order['ttl']))
                    conn.execute('UPDATE orders SET link_id=? WHERE id=?',(result['id'],order['id']))
            elif event['status'] in {'failed','refunded'} and order['link_id']:
                conn.execute('UPDATE links SET revoked=1 WHERE id=?',(order['link_id'],))
                conn.execute('DELETE FROM leases WHERE link_id=?',(order['link_id'],))
            conn.execute('UPDATE orders SET status=? WHERE id=?',(event['status'],order['id']))
            conn.execute('INSERT INTO events(id,payload_hash,result) VALUES(?,?,?)',(event['event_id'],digest,json.dumps(result)))
            return result


def make_server(store,admin_key,webhook_key,root,port=8892):
    root=Path(root)
    public={'index.html','styles.css','player.js','scheduler.js','catalog.json','verification.json','player-source-kit.zip','README.txt'}
    public.update(f'audio/t{i:02d}.mp3' for i in range(1,8))
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass  # Never log tokens, URLs, keys or headers.
        def respond(self,status,payload,content_type='application/json'):
            data=json.dumps(payload).encode() if isinstance(payload,(dict,list)) else payload
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; media-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers();self.wfile.write(data)
        def admin(self):
            value=self.headers.get('Authorization','')
            if not hmac.compare_digest(value,'Bearer '+admin_key):raise Problem(401,'Local administrator authentication required')
        def origin(self):
            value=self.headers.get('Origin')
            if value and value!=f'http://127.0.0.1:{self.server.server_port}':raise Problem(403,'Origin is not allowed')
        def do_GET(self):
            parsed=urlsplit(self.path)
            try:
                if parsed.path=='/api/status':return self.respond(200,{'mode':'local-prototype','payments':'SIMULATION_NO_PAYMENT','cdn':'local-signed-stream','tracks_total':7,'profiles':7})
                if parsed.path.startswith('/stream/'):
                    track=parsed.path.removeprefix('/stream/')
                    ticket=parse_qs(parsed.query).get('ticket',[''])[0]
                    store.validate_media(ticket,track)
                    return self.respond(200,(root/'audio'/f'{track}.mp3').read_bytes(),'audio/mpeg')
                name=parsed.path.lstrip('/') or 'index.html'
                if name not in public:raise Problem(404,'Not found')
                file=root/name
                if not file.is_file():raise Problem(404,'Not found')
                return self.respond(200,file.read_bytes(),mimetypes.guess_type(name)[0] or 'application/octet-stream')
            except Problem as error:self.respond(error.status,{'error':error.message})
            except Exception:self.respond(500,{'error':'Local prototype failure; no internal detail is exposed'})
        def do_POST(self):
            try:
                self.origin()
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=8192:raise Problem(400,'Invalid request size')
                raw=self.rfile.read(size)
                route=urlsplit(self.path).path
                if route=='/api/mock/webhook':
                    self.admin()
                    result=store.test_payment_event(raw,int(self.headers.get('X-Demo-Timestamp','0')),self.headers.get('X-Demo-Signature',''),webhook_key)
                else:
                    payload=json.loads(raw)
                    if route.startswith('/api/admin/'):
                        self.admin()
                        if route=='/api/admin/issue':result=store.issue(int(payload['ttl']))
                        elif route=='/api/admin/revoke':result=store.revoke(payload['id'])
                        elif route=='/api/admin/order':result=store.create_test_order(payload['id'],int(payload['amount_minor']),int(payload['ttl']))
                        else:raise Problem(404,'Not found')
                    elif route=='/api/lease':result=store.acquire(payload['token'],payload['device'])
                    elif route=='/api/heartbeat':result=store.heartbeat(payload['token'],payload['device'])
                    elif route=='/api/release':result=store.release(payload['token'],payload['device'])
                    elif route=='/api/next':result=store.next_track(payload['token'],payload['device'],payload['profile'])
                    else:raise Problem(404,'Not found')
                self.respond(200,result)
            except Problem as error:self.respond(error.status,{'error':error.message})
            except (ValueError,KeyError,TypeError):self.respond(400,{'error':'Invalid request'})
            except Exception:self.respond(500,{'error':'Local prototype failure; no internal detail is exposed'})
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


if __name__=='__main__':
    base=Path(__file__).resolve().parent
    required=['PLAYER_SIGNING_SECRET','PLAYER_ADMIN_KEY','PLAYER_WEBHOOK_SECRET','PLAYER_DB_PATH']
    if any(not os.environ.get(name) for name in required):raise SystemExit('Set required local environment values; no default secrets exist')
    catalog=json.loads((base/'catalog.json').read_text(encoding='utf-8'))
    store=Store(os.environ['PLAYER_DB_PATH'],os.environ['PLAYER_SIGNING_SECRET'].encode(),{profile['id']:[track['id'] for track in catalog['tracks']] for profile in catalog['profiles']})
    server=make_server(store,os.environ['PLAYER_ADMIN_KEY'],os.environ['PLAYER_WEBHOOK_SECRET'].encode(),base,int(os.environ.get('PLAYER_PORT','8892')))
    print(f'Local prototype listening at127.0.0.1:{server.server_port}; payment simulation only',flush=True)
    server.serve_forever()
