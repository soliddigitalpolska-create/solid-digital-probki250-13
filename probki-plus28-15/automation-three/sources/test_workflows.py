import unittest,tempfile,json,csv,sqlite3
from pathlib import Path
from workflow import Workspace,LocalAPI,Client,BlockedOutbound

class RealWorkflows(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.ws=Workspace(self.root);self.api=LocalAPI(self.ws);self.api.start();self.client=Client(self.api.url,self.ws)
 def tearDown(self):self.api.close();self.temp.cleanup()
 def test_network_boundary_rejects_non_fixture_target(self):
  for url in ['https://example.com','http://localhost:80','http://127.0.0.1:1','file:///etc/passwd']:
   with self.assertRaises(BlockedOutbound):Client(url,self.ws)
 def test_csv_crm_retries_429_and_503_then_persists_without_duplicate_after_restart(self):
  p=self.root/'contacts.csv';p.write_text('external_id,name,email\nA1,Ada Demo,ada@example.invalid\nA2,Jan Demo,jan@example.invalid\nA3,Błąd,not-email\n',encoding='utf-8')
  result=self.ws.csv_to_crm(p,self.client)
  self.assertEqual((result['created'],result['invalid'],result['dead_letter']),(2,1,0))
  self.assertEqual(self.api.attempts['POST:/contacts:A1'],3)
  reopened=Workspace(self.root);result=reopened.csv_to_crm(p,self.client)
  self.assertEqual(result['created'],0);self.assertEqual(result['skipped'],2)
  self.assertEqual(reopened.count('contacts'),2)
 def test_retry_exhaustion_creates_dead_letter_without_false_success(self):
  p=self.root/'contacts.csv';p.write_text('external_id,name,email\nFAIL,Nieudany,fail@example.invalid\n',encoding='utf-8')
  result=self.ws.csv_to_crm(p,self.client)
  self.assertEqual(result['dead_letter'],1);self.assertEqual(self.ws.count('contacts'),0)
  self.assertEqual(self.ws.count('dead_letters'),1)
 def test_order_approval_prevents_document_until_human_and_stops_duplicate(self):
  p=self.root/'orders.csv';p.write_text('id,buyer,quantity,unit_net\nZ1,Fikcyjna Pracownia,2,123.45\nZ2,Błędne dane,-1,99\n',encoding='utf-8')
  result=self.ws.stage_orders(p);self.assertEqual(result['pending'],1);self.assertEqual(result['invalid'],1)
  self.assertEqual(len(list((self.root/'documents').glob('*.html'))),0)
  with self.assertRaises(ValueError):self.ws.approve_order('Z1','',self.client)
  result=self.ws.approve_order('Z1','Własny tester',self.client)
  self.assertTrue(Path(result['document']).is_file());self.assertEqual(result['net_total'],'246.90')
  self.assertEqual(self.ws.count('outbox'),1);self.assertFalse(result['email_sent'])
  self.ws.approve_order('Z1','Własny tester',self.client);self.assertEqual(self.ws.count('outbox'),1)
 def test_webhook_duplicate_classification_human_gate_report_csv(self):
  result=self.client.request('POST','/webhooks/tickets',{'id':'T1','subject':'Błąd płatności','body':'Nie działa płatność za zamówienie'});self.assertEqual(result['category'],'billing')
  self.client.request('POST','/webhooks/tickets',{'id':'T1','subject':'Błąd płatności','body':'Nie działa płatność za zamówienie'})
  self.assertEqual(self.ws.count('tickets'),1);self.assertEqual(self.ws.count('tasks'),0)
  self.ws.review_ticket('T1','approved','Własny tester',self.client)
  self.ws.review_ticket('T1','approved','Własny tester',self.client)
  self.assertEqual(self.ws.count('tasks'),1)
  self.client.request('POST','/webhooks/tickets',{'id':'T2','subject':'Inne','body':'Prośba nietypowa'})
  self.ws.review_ticket('T2','rejected','Własny tester',self.client)
  report=self.ws.ticket_report()
  with Path(report).open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
  self.assertEqual(len(rows),2);self.assertEqual({r['review_status'] for r in rows},{'approved','rejected'})
 def test_api_validation_and_fixed_schema_reject_bad_payload(self):
  with self.assertRaises(ValueError):self.client.request('POST','/webhooks/tickets',{'id':'T0','subject':'','body':''})
  self.assertEqual(self.ws.count('tickets'),0)
 def test_fixture_cannot_bypass_review_with_direct_task_request(self):
  self.client.request('POST','/webhooks/tickets',{'id':'T1','subject':'Test','body':'Własne dane'})
  with self.assertRaises(ValueError):self.client.request('POST','/tasks',{'id':'T1','category':'manual'})
  self.assertEqual(self.ws.count('tasks'),0)
 def test_csv_report_neutralizes_spreadsheet_formula_input(self):
  self.client.request('POST','/webhooks/tickets',{'id':'T1','subject':'=1+1','body':'Własne dane'})
  with Path(self.ws.ticket_report()).open(encoding='utf-8') as f:row=list(csv.DictReader(f))[0]
  self.assertTrue(row['subject'].startswith("'="))

if __name__=='__main__':unittest.main(verbosity=2)
