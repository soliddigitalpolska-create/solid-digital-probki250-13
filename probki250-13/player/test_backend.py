"""Behavior tests against actual SQLite and local HTTP. No payment network calls."""
import concurrent.futures
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

try:
    from player_backend import Store, Problem, make_server
except ImportError:
    Store = Problem = make_server = None


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Store, 'Backend feature missing: implement real SQLite/token/lease behavior')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = [1000000]
        self.key = secrets.token_bytes(32)
        self.catalog = {f'p{i:02d}':[f't{j:02d}' for j in range(1,8)] for i in range(1,8)}
        self.store = Store(Path(self.tmp.name)/'state.sqlite', self.key, self.catalog, lambda:self.now[0])

    def issue(self, ttl=100):
        return self.store.issue(ttl)

    def test_forged_token_cannot_start_lease(self):
        token=self.issue()['token']
        forged=token[:-5]+'abcde'
        with self.assertRaises(Problem): self.store.acquire(forged,'device_a_123')

    def test_expired_link_cannot_start_or_stream(self):
        issued=self.issue(10)
        self.store.acquire(issued['token'],'device_a_123')
        self.now[0]+=10
        with self.assertRaises(Problem): self.store.acquire(issued['token'],'device_a_123')

    def test_revocation_blocks_old_link_and_signed_audio_ticket(self):
        issued=self.issue()
        self.store.acquire(issued['token'],'device_a_123')
        item=self.store.next_track(issued['token'],'device_a_123','p01')
        self.store.revoke(issued['id'])
        with self.assertRaises(Problem): self.store.acquire(issued['token'],'device_a_123')
        with self.assertRaises(Problem): self.store.validate_media(item['ticket'],item['track'])

    def test_two_simultaneous_devices_only_one_acquires(self):
        issued=self.issue()
        barrier=threading.Barrier(12)
        def claim(index):
            barrier.wait()
            try:
                self.store.acquire(issued['token'],f'device_{index:03d}')
                return 200
            except Problem as error:return error.status
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            statuses=list(pool.map(claim,range(12)))
        self.assertEqual(statuses.count(200),1)
        self.assertEqual(statuses.count(409),11)
        database=sqlite3.connect(self.store.db)
        try:
            self.assertEqual(database.execute('SELECT COUNT(*) FROM leases').fetchone()[0],1)
        finally:database.close()

    def test_expired_lease_allows_new_device_and_rejects_old_heartbeat(self):
        issued=self.issue()
        self.store.acquire(issued['token'],'device_a_123')
        self.now[0]+=31
        self.store.acquire(issued['token'],'device_b_123')
        with self.assertRaises(Problem): self.store.heartbeat(issued['token'],'device_a_123')
        self.store.heartbeat(issued['token'],'device_b_123')

    def test_owner_release_does_not_allow_foreign_release(self):
        issued=self.issue()
        self.store.acquire(issued['token'],'device_a_123')
        with self.assertRaises(Problem):self.store.release(issued['token'],'device_b_123')
        self.store.release(issued['token'],'device_a_123')
        self.store.acquire(issued['token'],'device_b_123')

    def test_shuffle_plays_every_track_before_repetition_and_avoids_boundary_repeat(self):
        issued=self.issue()
        self.store.acquire(issued['token'],'device_a_123')
        tracks=[self.store.next_track(issued['token'],'device_a_123','p01')['track'] for _ in range(70)]
        for start in range(0,70,7): self.assertEqual(set(tracks[start:start+7]),{'t01','t02','t03','t04','t05','t06','t07'})
        for boundary in range(7,70,7):self.assertNotEqual(tracks[boundary-1],tracks[boundary])

    def test_signed_media_rejects_other_track_wrong_device_or_expiration(self):
        issued=self.issue()
        self.store.acquire(issued['token'],'device_a_123')
        item=self.store.next_track(issued['token'],'device_a_123','p01')
        self.assertEqual(self.store.validate_media(item['ticket'],item['track']),item['track'])
        wrong='t02' if item['track']!='t02' else 't03'
        with self.assertRaises(Problem):self.store.validate_media(item['ticket'],wrong)
        self.store.release(issued['token'],'device_a_123')
        self.store.acquire(issued['token'],'device_b_123')
        with self.assertRaises(Problem):self.store.validate_media(item['ticket'],item['track'])

    def test_audio_ticket_expiration_denies_request_even_while_link_valid(self):
        issued=self.issue(100)
        self.store.acquire(issued['token'],'device_a_123')
        item=self.store.next_track(issued['token'],'device_a_123','p01')
        self.now[0]+=31
        self.store.acquire(issued['token'],'device_a_123')
        with self.assertRaises(Problem):self.store.validate_media(item['ticket'],item['track'])

    def test_payment_event_replay_with_changed_content_is_rejected(self):
        self.store.create_test_order('order_test',19900,100)
        self.event('same_event','pending')
        with self.assertRaises(Problem):self.event('same_event','paid')

    def test_server_does_not_serve_database_source_or_private_config(self):
        admin=secrets.token_urlsafe(32)
        server=make_server(self.store,admin,self.key,Path(self.tmp.name),port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        base=f'http://127.0.0.1:{server.server_port}'
        for route in ['/state.sqlite','/player_backend.py','/.env','/../player-runtime-private.json']:
            with self.assertRaises(urllib.error.HTTPError) as context:urllib.request.urlopen(base+route,timeout=5)
            self.assertEqual(context.exception.code,404)

    def test_server_returns_static_catalog_as_object_not_reserialised_bytes(self):
        root=Path(self.tmp.name)
        (root/'catalog.json').write_text('{"profiles":[{"id":"p01"}],"tracks":[{"id":"t01"}]}',encoding='utf-8')
        server=make_server(self.store,secrets.token_urlsafe(32),self.key,root,port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        try:response=urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/catalog.json',timeout=5)
        except urllib.error.HTTPError as error:response=error
        with response:
            result=json.load(response)
            self.assertEqual(response.status,200)
            self.assertEqual(result['profiles'][0]['id'],'p01')
            self.assertEqual(result['tracks'][0]['id'],'t01')

    def test_all_seven_profiles_have_independent_complete_cycles(self):
        issued=self.issue()
        self.store.acquire(issued['token'],'device_a_123')
        for profile in self.catalog:
            tracks=[self.store.next_track(issued['token'],'device_a_123',profile)['track'] for _ in range(7)]
            self.assertEqual(set(tracks),{'t01','t02','t03','t04','t05','t06','t07'})

    def test_seven_profiles_with75_logical_records_each_complete_two_cycles(self):
        # Real SQLite queue,525 logical IDs. No claim that525 audio files exist.
        catalog={f'p{i:02d}':[f'p{i:02d}_t{j:03d}' for j in range(1,76)] for i in range(1,8)}
        store=Store(Path(self.tmp.name)/'scale.sqlite',self.key,catalog,lambda:self.now[0])
        issued=store.issue(100)
        store.acquire(issued['token'],'device_a_123')
        for profile in catalog:
            values=[store.next_track(issued['token'],'device_a_123',profile)['track'] for _ in range(150)]
            self.assertEqual(set(values[:75]),set(catalog[profile]))
            self.assertEqual(set(values[75:]),set(catalog[profile]))
            self.assertNotEqual(values[74],values[75])

    def test_unknown_profile_and_device_input_are_rejected(self):
        issued=self.issue()
        with self.assertRaises(Problem):self.store.acquire(issued['token'],"' OR 1=1;")
        self.store.acquire(issued['token'],'device_a_123')
        with self.assertRaises(Problem):self.store.next_track(issued['token'],'device_a_123','../secret')

    def event(self,event_id,status='paid',amount=19900,key=None):
        raw=json.dumps({'event_id':event_id,'order_id':'order_test','status':status,'amount_minor':amount,'currency':'PLN'},separators=(',',':')).encode()
        signature=hmac.new(key or self.key,str(self.now[0]).encode()+b'.'+raw,hashlib.sha256).hexdigest()
        return self.store.test_payment_event(raw,self.now[0],signature,self.key)

    def test_test_payment_requires_signed_confirmed_amount_and_is_idempotent(self):
        self.store.create_test_order('order_test',19900,100)
        with self.assertRaises(Problem):self.event('event_forged',key=secrets.token_bytes(32))
        with self.assertRaises(Problem):self.event('event_wrong_amount',amount=19901)
        pending=self.event('event_pending','pending')
        self.assertNotIn('token',pending)
        paid=self.event('event_paid')
        repeated=self.event('event_paid')
        self.assertEqual(paid['token'],repeated['token'])
        self.assertEqual(paid['id'],repeated['id'])
        self.store.acquire(paid['token'],'device_a_123')
        refunded=self.event('event_refunded','refunded')
        self.assertEqual(refunded['status'],'refunded')
        with self.assertRaises(Problem):self.store.acquire(paid['token'],'device_a_123')

    def test_http_two_clients_and_admin_authorization(self):
        admin=secrets.token_urlsafe(32)
        server=make_server(self.store,admin,self.key,Path(self.tmp.name),port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        base=f'http://127.0.0.1:{server.server_port}'
        def request(route,payload=None,key=None):
            data=json.dumps(payload).encode() if payload is not None else None
            headers={'Content-Type':'application/json'}
            if key:headers['Authorization']='Bearer '+key
            req=urllib.request.Request(base+route,data=data,headers=headers)
            try:
                with urllib.request.urlopen(req,timeout=5) as response:return response.status,json.load(response)
            except urllib.error.HTTPError as response:return response.code,json.load(response)
        self.assertEqual(request('/api/admin/issue',{'ttl':100})[0],401)
        status,issued=request('/api/admin/issue',{'ttl':100},admin)
        self.assertEqual(status,200)
        self.assertEqual(request('/api/lease',{'token':issued['token'],'device':'device_a_123'})[0],200)
        self.assertEqual(request('/api/lease',{'token':issued['token'],'device':'device_b_123'})[0],409)
        self.assertEqual(request('/api/heartbeat',{'token':issued['token'],'device':'device_b_123'})[0],409)
        self.assertEqual(request('/api/admin/revoke',{'id':issued['id']},admin)[0],200)
        self.assertEqual(request('/api/lease',{'token':issued['token'],'device':'device_a_123'})[0],403)

    def test_http_owner_release_allows_second_client_and_blocks_old_heartbeat(self):
        admin=secrets.token_urlsafe(32)
        server=make_server(self.store,admin,self.key,Path(self.tmp.name),port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        base=f'http://127.0.0.1:{server.server_port}'
        issued=self.issue()
        def request(route,device):
            payload=json.dumps({'token':issued['token'],'device':device}).encode()
            req=urllib.request.Request(base+route,data=payload,headers={'Content-Type':'application/json'})
            try:response=urllib.request.urlopen(req,timeout=5)
            except urllib.error.HTTPError as error:response=error
            with response:return response.status,json.load(response)
        self.assertEqual(request('/api/lease','device_a_123')[0],200)
        self.assertEqual(request('/api/release','device_b_123')[0],409)
        status,result=request('/api/release','device_a_123')
        self.assertEqual(status,200);self.assertTrue(result['released'])
        with self.store.connection() as database:
            self.assertEqual(database.execute('SELECT COUNT(*) FROM leases').fetchone()[0],0)
        self.assertEqual(request('/api/lease','device_b_123')[0],200)
        self.assertEqual(request('/api/heartbeat','device_a_123')[0],409)


if __name__=='__main__':unittest.main(verbosity=2)
