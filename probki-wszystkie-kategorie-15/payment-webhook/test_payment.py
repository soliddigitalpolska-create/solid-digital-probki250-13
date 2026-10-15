"""Actual localhost HTTP + SQLite integration tests, fictional amounts/key only."""
import concurrent.futures,hashlib,hmac,json,tempfile,time,unittest,urllib.error,urllib.request
from pathlib import Path
try:import payment_demo as app
except ModuleNotFoundError:app=None

KEY=b'demo-only-not-a-real-payment-key'
class PaymentIntegration(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(app,'Local payment demo must be implemented')
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.server=app.start_demo(Path(self.temp.name)/'store.sqlite')
        self.base=self.server.base_url
    def tearDown(self):
        if hasattr(self,'server'):self.server.close();self.temp.cleanup()
    def http(self,path,data=None,headers=None):
        body=None if data is None else json.dumps(data,separators=(',',':')).encode()
        request=urllib.request.Request(self.base+path,data=body,headers={'Content-Type':'application/json',**(headers or {})})
        try:
            with urllib.request.urlopen(request,timeout=10) as response:return response.status,json.loads(response.read())
        except urllib.error.HTTPError as error:return error.code,json.loads(error.read())
    def order(self,amount=34900,currency='PLN'):
        code,data=self.http('/orders',{'amount_minor':amount,'currency':currency,'personalization':{'engraving':'DEMO - not customer data'}})
        self.assertEqual(code,201,data);return data
    def event(self,order,kind='payment.paid',event_id='evt_demo_1',**extra):
        return {'id':event_id,'type':kind,'session_id':order['session_id'],'amount_minor':order['amount_minor'],'currency':order['currency'],**extra}
    def post_event(self,event,timestamp=None,bad_signature=False):
        stamp=str(int(time.time()) if timestamp is None else timestamp)
        raw=json.dumps(event,separators=(',',':')).encode()
        signature=hmac.new(KEY,stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        if bad_signature:signature='0'*64
        return self.http('/webhook',event,{'X-Demo-Timestamp':stamp,'X-Demo-Signature':signature})
    def state(self,order):return self.http('/orders/'+order['order_id'])[1]
    def test_full_flow_paid_dispatches_once_and_callback_repeat_is_idempotent(self):
        order=self.order();self.assertEqual(self.state(order)['payment_status'],'awaiting_payment')
        self.assertEqual(self.http('/dispatch',{})[1]['dispatched'],[])
        event=self.event(order);self.assertEqual(self.post_event(event)[0],200)
        self.assertEqual(self.post_event(event)[1]['duplicate'],True)
        self.assertEqual(self.state(order)['payment_status'],'paid')
        self.assertEqual(self.http('/dispatch',{})[1]['dispatched'],[order['order_id']])
        self.assertEqual(self.http('/dispatch',{})[1]['dispatched'],[])
        self.assertEqual(self.state(order)['fulfillment_rows'],1)
    def test_invalid_signature_cannot_mark_order_paid(self):
        order=self.order();self.assertEqual(self.post_event(self.event(order),bad_signature=True)[0],401)
        self.assertEqual(self.state(order)['payment_status'],'awaiting_payment')
    def test_stale_signed_event_is_rejected(self):
        order=self.order();self.assertEqual(self.post_event(self.event(order),timestamp=int(time.time())-600)[0],401)
        self.assertEqual(self.state(order)['fulfillment_rows'],0)
    def test_wrong_amount_is_rejected_without_fulfillment(self):
        order=self.order();self.assertEqual(self.post_event(self.event(order,amount_minor=1))[0],409)
        self.assertEqual(self.state(order)['fulfillment_rows'],0)
    def test_wrong_currency_is_rejected_without_payment_mutation(self):
        order=self.order();self.assertEqual(self.post_event(self.event(order,currency='EUR'))[0],409)
        self.assertEqual(self.state(order)['payment_status'],'awaiting_payment')
    def test_cancelled_payment_never_reaches_realization(self):
        order=self.order();self.assertEqual(self.post_event(self.event(order,'payment.canceled'))[0],200)
        self.assertEqual(self.state(order)['payment_status'],'canceled')
        self.assertEqual(self.http('/dispatch',{})[1]['dispatched'],[])
    def test_failed_payment_never_reaches_realization(self):
        order=self.order();self.assertEqual(self.post_event(self.event(order,'payment.failed'))[0],200)
        self.assertEqual(self.state(order)['payment_status'],'failed')
        self.assertEqual(self.state(order)['fulfillment_rows'],0)
    def test_refund_before_dispatch_stops_queued_realization(self):
        order=self.order();self.post_event(self.event(order))
        refund=self.event(order,'payment.refunded','evt_refund');self.assertEqual(self.post_event(refund)[0],200)
        self.assertEqual(self.post_event(refund)[1]['duplicate'],True)
        state=self.state(order);self.assertEqual(state['payment_status'],'refunded');self.assertEqual(state['fulfillment_status'],'canceled')
        self.assertEqual(self.http('/dispatch',{})[1]['dispatched'],[]);self.assertEqual(state['refund_rows'],1)
    def test_refund_after_dispatch_records_recall_required_instead_of_fake_undo(self):
        order=self.order();self.post_event(self.event(order));self.http('/dispatch',{})
        self.assertEqual(self.post_event(self.event(order,'payment.refunded','evt_refund'))[0],200)
        state=self.state(order);self.assertEqual(state['fulfillment_status'],'recall_required');self.assertEqual(state['refund_rows'],1)
    def test_event_id_collision_with_changed_payload_is_rejected(self):
        order=self.order();self.post_event(self.event(order))
        self.assertEqual(self.post_event(self.event(order,'payment.refunded'))[0],409)
        self.assertEqual(self.state(order)['payment_status'],'paid')
    def test_twenty_concurrent_retries_create_single_fulfillment_row(self):
        order=self.order();event=self.event(order)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:responses=list(pool.map(lambda _:self.post_event(event),range(20)))
        self.assertTrue(all(status==200 for status,_ in responses),responses)
        self.assertEqual(self.state(order)['fulfillment_rows'],1)
        self.assertEqual(sum(not data['duplicate'] for _,data in responses),1)
    def test_unknown_session_is_rejected(self):
        order=self.order();self.assertEqual(self.post_event(self.event(order,session_id='missing_demo'))[0],404)
        self.assertEqual(self.state(order)['payment_status'],'awaiting_payment')
    def test_invalid_order_amounts_are_rejected(self):
        for value in [0,-1,True,'34900']:
            code,_=self.http('/orders',{'amount_minor':value,'currency':'PLN','personalization':{}})
            self.assertEqual(code,400)
    def test_refund_without_prior_payment_is_rejected(self):
        order=self.order();self.assertEqual(self.post_event(self.event(order,'payment.refunded'))[0],409)
        self.assertEqual(self.state(order)['refund_rows'],0)
    def test_unsigned_browser_return_cannot_mark_order_paid(self):
        order=self.order();code,_=self.http('/return?session_id='+order['session_id']+'&paid=true')
        self.assertEqual(code,200);self.assertEqual(self.state(order)['payment_status'],'awaiting_payment')

if __name__=='__main__':unittest.main(verbosity=2)
