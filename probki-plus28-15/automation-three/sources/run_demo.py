"""Run own fixtures only. --approve-demo explicitly supplies simulated review decisions.
It does not claim that a human reviewed client material or that emails were sent.
"""
from pathlib import Path
import argparse,json,csv,subprocess,sys,datetime
from workflow import Workspace,LocalAPI,Client,BlockedOutbound

p=argparse.ArgumentParser();p.add_argument('--approve-demo',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if not a.approve_demo:raise SystemExit('Use --approve-demo to explicitly simulate review. No approval is inferred.')
a.output.mkdir(parents=True,exist_ok=True);fixtures=a.output/'fixtures';fixtures.mkdir(exist_ok=True)
(fixtures/'contacts.csv').write_text('external_id,name,email\nA1,Ada Demo,ada@example.invalid\nA2,Jan Demo,jan@example.invalid\nA3,Błędny kontakt,nie-email\nFAIL,Awaria kontrolowana,fail@example.invalid\n',encoding='utf-8')
(fixtures/'contacts-valid-only.csv').write_text('external_id,name,email\nA1,Ada Demo,ada@example.invalid\nA2,Jan Demo,jan@example.invalid\n',encoding='utf-8')
(fixtures/'orders.csv').write_text('id,buyer,quantity,unit_net\nZ1,Fikcyjna Pracownia,2,123.45\nZ2,Demo Studio,1,85.00\nZ3,Błędne dane,-1,99\n',encoding='utf-8')
ws=Workspace(a.output);api=LocalAPI(ws).start();client=Client(api.url,ws);result={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'Three actual own Python workflows, real local HTTP API and SQLite persistence','data':'Own fictional fixtures; no customer data','LLM_used':False,'human_decisions':'Explicitly simulated by --approve-demo; not real client approvals','external_email_or_payment':False}
try:
 result['health']=client.request('GET','/health')
 result['crm_first']=ws.csv_to_crm(fixtures/'contacts.csv',client)
 reopened=Workspace(a.output);result['crm_after_process_reopen']=reopened.csv_to_crm(fixtures/'contacts-valid-only.csv',client)
 result['orders_staged']=ws.stage_orders(fixtures/'orders.csv');result['documents_before_explicit_test_review']=len(list((a.output/'documents').glob('*.html')))
 try:client.request('POST','/outbox',{'id':'Z2','document_name':'bypass.html'})
 except ValueError:result['order_review_bypass_blocked']=True
 result['order_approved']=ws.approve_order('Z1','DEMO_TEST_EXPLICIT_REVIEW',client)
 ws.approve_order('Z1','DEMO_TEST_EXPLICIT_REVIEW',client);result['outbox_after_duplicate_approval']=ws.count('outbox')
 tickets=[{'id':'T1','subject':'Błąd płatności','body':'Nie działa płatność za zamówienie — fikcyjne dane'},{'id':'T2','subject':'=1+1','body':'Nieznany temat do ręcznej decyzji'},{'id':'T3','subject':'Błąd strony','body':'Nie działa podgląd — przykład własny'}]
 (fixtures/'tickets.json').write_text(json.dumps(tickets,ensure_ascii=False,indent=2),encoding='utf-8')
 result['webhooks']=[client.request('POST','/webhooks/tickets',t) for t in tickets]
 client.request('POST','/webhooks/tickets',tickets[0]);result['tasks_before_explicit_test_review']=ws.count('tasks')
 try:client.request('POST','/tasks',{'id':'T2','category':'manual'})
 except ValueError:result['task_review_bypass_blocked']=True
 for id,decision in [('T1','approved'),('T2','rejected'),('T3','approved')]:ws.review_ticket(id,decision,'DEMO_TEST_EXPLICIT_REVIEW',client)
 ws.review_ticket('T1','approved','DEMO_TEST_EXPLICIT_REVIEW',client)
 result['tickets_after_duplicate']=ws.count('tickets');result['tasks_after_duplicate']=ws.count('tasks');result['report']=ws.ticket_report()
 result['attempts']=api.attempts
 try:Client('https://example.com',ws)
 except BlockedOutbound:result['outbound_non_fixture_client_blocked']=True
finally:api.close()
# Independent interpreter and fresh SQLite connection: proof is not inferred from API response.
code="import sqlite3,json,sys; c=sqlite3.connect(sys.argv[1]); tables=['contacts','orders','outbox','tickets','tasks','dead_letters','events']; print(json.dumps({t:c.execute('select count(*) from '+t).fetchone()[0] for t in tables})); c.close()"
readback=subprocess.run([sys.executable,'-c',code,str(ws.db)],capture_output=True,text=True,check=True);result['independent_process_SQL_readback']=json.loads(readback.stdout)
assert result['crm_first']=={'workflow':'CSV → CRM fixture','created':2,'skipped':0,'invalid':1,'dead_letter':1}
assert result['crm_after_process_reopen']['skipped']==2 and result['outbox_after_duplicate_approval']==1
assert result['documents_before_explicit_test_review']==0 and result['tasks_before_explicit_test_review']==0
assert result['tickets_after_duplicate']==3 and result['tasks_after_duplicate']==2
assert result['independent_process_SQL_readback']['contacts']==2
result['status']='PASS_THREE_EXECUTED_LOCAL_WORKFLOWS'
for name,data in [('demo-summary.json',result),('database-readback.json',ws.export_evidence())]:
 text=json.dumps(data,ensure_ascii=False,indent=2).replace(str(a.output),'[own-local-demo]')
 (a.output/name).write_text(text,encoding='utf-8')
print(json.dumps({'status':result['status'],'readback':result['independent_process_SQL_readback'],'three_workflows':True,'test_decisions_explicit_simulation':True,'LLM':False,'email_sent':False},ensure_ascii=False))
