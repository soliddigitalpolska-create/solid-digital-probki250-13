"""Own offline email-flow proof. SQLite outbox only; no provider, SMTP or network.

Run: python flow-source.py --output-dir ./own-fixture-results
The output directory is local and contains fictional test data only.
"""
import argparse, datetime, json, os, pathlib, sqlite3, tempfile, unittest

class Engine:
    def __init__(self, path, contacts, events):
        self.db=sqlite3.connect(path)
        self.contacts=contacts;self.events=events
        self.db.executescript('CREATE TABLE IF NOT EXISTS seen(event_id TEXT PRIMARY KEY); CREATE TABLE IF NOT EXISTS flow(contact TEXT,kind TEXT,start_day INTEGER, PRIMARY KEY(contact,kind)); CREATE TABLE IF NOT EXISTS purchase(contact TEXT PRIMARY KEY,day INTEGER); CREATE TABLE IF NOT EXISTS outbox(delivery_key TEXT PRIMARY KEY,contact TEXT,kind TEXT,step INTEGER,due_day INTEGER,recorded_day INTEGER);')
    def tick(self, day):
        for event in self.events:
            if event['day']>day:continue
            if not self.db.execute('INSERT OR IGNORE INTO seen VALUES(?)',(event['id'],)).rowcount:continue
            cid=event['contact'];kind=event['type']
            if kind=='purchase':self.db.execute('INSERT OR REPLACE INTO purchase VALUES(?,?)',(cid,event['day']))
            elif kind in ('signup','abandoned_cart'):
                self.db.execute('INSERT OR IGNORE INTO flow VALUES(?,?,?)',(cid,'welcome' if kind=='signup' else 'cart',event['day']))
        for cid,kind,start in self.db.execute('SELECT contact,kind,start_day FROM flow').fetchall():
            contact=self.contacts[cid]
            if not contact['marketing_consent'] or contact['unsubscribed']:continue
            if kind=='cart' and self.db.execute('SELECT 1 FROM purchase WHERE contact=? AND day<=?',(cid,day)).fetchone():continue
            delays=[0,2,5] if kind=='welcome' else [0,1,3]
            for step,delay in enumerate(delays,1):
                if start+delay<=day:
                    self.db.execute('INSERT OR IGNORE INTO outbox VALUES(?,?,?,?,?,?)',(f'{cid}:{kind}:{step}',cid,kind,step,start+delay,day))
        self.db.commit()
    def rows(self):
        return [dict(zip(['delivery_key','contact','flow','step','due_day','recorded_day'],row)) for row in self.db.execute('SELECT * FROM outbox ORDER BY contact,kind,step')]
    def close(self):self.db.close()

def fixtures():
    contacts={c:dict(marketing_consent=True,unsubscribed=False) for c in ['A','B','C','D','E']}
    contacts['B']['marketing_consent']=False;contacts['C']['unsubscribed']=True
    events=[dict(id='signup-A',contact='A',type='signup',day=0),dict(id='signup-A',contact='A',type='signup',day=0),dict(id='signup-B',contact='B',type='signup',day=0),dict(id='signup-C',contact='C',type='signup',day=0),dict(id='cart-D',contact='D',type='abandoned_cart',day=0),dict(id='purchase-D',contact='D',type='purchase',day=1),dict(id='cart-E',contact='E',type='abandoned_cart',day=0)]
    return contacts,events

class FlowTests(unittest.TestCase):
    def setUp(self):
        self.contacts,self.events=fixtures();self.engine=Engine(':memory:',self.contacts,self.events)
    def tearDown(self):self.engine.close()
    def run_days(self):
        for day in [0,1,2,3,5]:self.engine.tick(day)
    def test_welcome_full_three_steps(self):
        self.run_days();self.assertEqual([r['step'] for r in self.engine.rows() if r['contact']=='A'],[1,2,3])
    def test_cart_full_three_steps(self):
        self.run_days();self.assertEqual([r['step'] for r in self.engine.rows() if r['contact']=='E'],[1,2,3])
    def test_welcome_timing(self):
        self.run_days();self.assertEqual([r['due_day'] for r in self.engine.rows() if r['contact']=='A'],[0,2,5])
    def test_cart_timing(self):
        self.run_days();self.assertEqual([r['due_day'] for r in self.engine.rows() if r['contact']=='E'],[0,1,3])
    def test_no_early_second_welcome(self):
        self.engine.tick(1);self.assertEqual([r['step'] for r in self.engine.rows() if r['contact']=='A'],[1])
    def test_no_consent(self):
        self.run_days();self.assertFalse(any(r['contact']=='B' for r in self.engine.rows()))
    def test_unsubscribed(self):
        self.run_days();self.assertFalse(any(r['contact']=='C' for r in self.engine.rows()))
    def test_purchase_stops_remaining_cart(self):
        self.run_days();self.assertEqual([r['step'] for r in self.engine.rows() if r['contact']=='D'],[1])
    def test_unsubscribe_between_steps(self):
        self.engine.tick(0);self.contacts['A']['unsubscribed']=True;self.engine.tick(5)
        self.assertEqual([r['step'] for r in self.engine.rows() if r['contact']=='A'],[1])
    def test_consent_revocation_between_steps(self):
        self.engine.tick(0);self.contacts['E']['marketing_consent']=False;self.engine.tick(5)
        self.assertEqual([r['step'] for r in self.engine.rows() if r['contact']=='E'],[1])
    def test_duplicate_event(self):
        self.run_days();self.assertEqual(len(self.engine.rows()),7)
    def test_duplicate_scheduler(self):
        self.run_days();before=self.engine.rows();self.engine.tick(5);self.assertEqual(self.engine.rows(),before)
    def test_two_actual_cohorts(self):
        self.run_days();rows=self.engine.rows();self.assertTrue(any(r['flow']=='welcome' for r in rows) and any(r['flow']=='cart' for r in rows))
    def test_restart_idempotency_with_sqlite(self):
        directory=pathlib.Path(OUTPUT).resolve();directory.mkdir(parents=True,exist_ok=True)
        fd,path=tempfile.mkstemp(prefix='own-flow-',suffix='.sqlite',dir=directory);os.close(fd)
        try:
            original=Engine(path,self.contacts,self.events);original.tick(0);before=original.rows();original.close()
            restarted=Engine(path,self.contacts,self.events)
            try:
                restarted.tick(0);self.assertEqual(restarted.rows(),before)
                restarted.tick(5);self.assertEqual(len(restarted.rows()),7)
            finally:restarted.close()
        finally:
            target=pathlib.Path(path).resolve();assert target.is_relative_to(directory);target.unlink(missing_ok=True)

def main():
    global OUTPUT
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',default='own-fixture-results');args=parser.parse_args();OUTPUT=args.output_dir
    output=pathlib.Path(OUTPUT).resolve();output.mkdir(parents=True,exist_ok=True)
    import io
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FlowTests))
    assert result.wasSuccessful(),stream.getvalue()
    contacts,events=fixtures();engine=Engine(':memory:',contacts,events)
    for day in [0,1,2,3,5]:engine.tick(day)
    outbox=engine.rows();engine.close()
    report=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),own_fictional_data=True,native_GetResponse=False,native_Klaviyo=False,email_sent=False,external_calls=0,test_count=result.testsRun,tests_passed=result.wasSuccessful(),test_output=stream.getvalue(),three_step_welcome_days=[0,2,5],three_step_cart_days=[0,1,3],cohorts=['new_subscribers_with_permission','abandoned_cart_without_purchase'],outbox=outbox,limitations='Local SQLite fixture scheduler and six original HTML emails; not provider configuration, not actual deliverability or a public backend.')
    (output/'flow-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'fixtures.json').write_text(json.dumps(dict(contacts=contacts,events=events),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(test_count=result.testsRun,tests_passed=result.wasSuccessful(),outbox_count=len(outbox),email_sent=False)))
if __name__=='__main__':main()
