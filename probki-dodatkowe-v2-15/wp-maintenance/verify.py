"""Actual isolated WordPress/Woo restore and narrow-loopback HTTP policy proof.
No connection to WordPress.com, hosting, client accounts or a real payment provider.
"""
import hashlib,json,secrets,shutil,sqlite3,subprocess,threading,zipfile,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
SOURCE=ROOT/'work/useme-plus28-2026-10-15/proof-wp-three/sites/retail'
SITE=HERE/'site/wordpress';PRIVATE=HERE/'private';PUBLIC=HERE/'public'
for p in [PRIVATE,PUBLIC]:p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tracked=['private/wordpress.sqlite','site/wordpress/wp-config.php'];before={p:sha(SOURCE/p) for p in tracked}
db=PRIVATE/('wordpress-retry1.sqlite' if '--retry1' in sys.argv else 'wordpress.sqlite')
if db.exists():raise RuntimeError('Fresh output folder required; refusing to overwrite an existing test clone')
if not SITE.exists():shutil.copytree(SOURCE/'site/wordpress',SITE,ignore=shutil.ignore_patterns('wp-config.php','*.sqlite','*.sqlite-wal','*.sqlite-shm','*.log'))
with sqlite3.connect((SOURCE/'private/wordpress.sqlite').as_uri()+'?mode=ro',uri=True) as r,sqlite3.connect(db) as w:r.backup(w)
r.close();w.close()
cfg={'DB_NAME':'own_v2_maintenance','DB_USER':'unused','DB_PASSWORD':'unused','DB_HOST':'localhost','DB_CHARSET':'utf8mb4','DB_COLLATE':'','DB_ENGINE':'sqlite','DB_PATH':db.as_posix(),'WP_HOME':'http://127.0.0.1:8821','WP_SITEURL':'http://127.0.0.1:8821','WP_ENVIRONMENT_TYPE':'local','WP_DEBUG':False,'WP_DEBUG_DISPLAY':False,'DISALLOW_FILE_EDIT':True,'DISALLOW_FILE_MODS':True,'WP_HTTP_BLOCK_EXTERNAL':True,'AUTOMATIC_UPDATER_DISABLED':True,'DISABLE_WP_CRON':True}
for key in ['AUTH_KEY','SECURE_AUTH_KEY','LOGGED_IN_KEY','NONCE_KEY','AUTH_SALT','SECURE_AUTH_SALT','LOGGED_IN_SALT','NONCE_SALT']:cfg[key]=secrets.token_hex(32)
config='<?php\n'+''.join("define('"+k+"',"+('true' if v is True else 'false' if v is False else "'"+v+"'")+");\n" for k,v in cfg.items())+"$table_prefix='workshop_';if(!defined('ABSPATH'))define('ABSPATH',__DIR__.'/');require_once ABSPATH.'wp-settings.php';\n"
(SITE/'wp-config.php').write_text(config,encoding='utf-8')
with sqlite3.connect(db) as w:w.execute("UPDATE workshop_options SET option_value='http://127.0.0.1:8821' WHERE option_name IN ('home','siteurl')");w.commit()
w.close()
guard=SITE/'wp-content/mu-plugins/v2-maintenance-offline.php'
guard.write_text('''<?php
defined('ABSPATH')||exit;
add_filter('pre_wp_mail',static fn()=>false,PHP_INT_MAX);
add_filter('woocommerce_product_is_in_stock',static fn()=>true,PHP_INT_MAX);
add_action('init',function(){
 remove_all_filters('pre_http_request');
 add_filter('pre_http_request',function($pre,$args,$url){
  if(get_option('v2_fixture_rule','broken')==='fixed' && $url==='http://127.0.0.1:8822/own-wordpress-com-fixture')return false;
  return new WP_Error('v2_offline_firewall_denied','Own controlled fixture: request denied; no external transport');
 },PHP_INT_MAX,3);
},PHP_INT_MAX);
''',encoding='utf-8')
marker=SITE/'wp-content/plugins/own-v2-marker.txt';marker.write_text('OWN BASELINE FILE VERSION1\n',encoding='utf-8')
php=(SOURCE/'private/php-path.txt').read_text(encoding='utf-8').strip();ini=Path(php).parent/'php.ini'
def call(op,**data):
 r=subprocess.run([php,'-c',str(ini),'-d','error_log='+str(PRIVATE/'php-error.log'),str(HERE/'native-check.php')],input=json.dumps({'op':op,**data}),text=True,encoding='utf-8',capture_output=True,timeout=80)
 start=r.stdout.find('{')
 if r.returncode or start<0:raise RuntimeError((r.stderr+r.stdout)[-3000:])
 return json.loads(r.stdout[start:])
class Fixture(BaseHTTPRequestHandler):
 hits=0
 def do_GET(self):
  if self.path!='/own-wordpress-com-fixture':self.send_error(404);return
  type(self).hits+=1;body=b'{"fixture":"own loopback emulator, not WordPress.com","ok":true}'
  self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',8822),Fixture);threading.Thread(target=server.serve_forever,daemon=True).start()
tests=[]
def check(name,condition,**details):
 tests.append(dict(test=name,passed=bool(condition),**details))
 if not condition:raise AssertionError((name,details))
try:
 baseline=call('inspect');check('real_WordPress_and_Woo_loaded',baseline['wordpress']=='7.1.3' and bool(baseline['woocommerce']),wordpress=baseline['wordpress'],woocommerce=baseline['woocommerce'])
 blocked=call('http',url='http://127.0.0.1:8822/own-wordpress-com-fixture');check('before_fix_native_WP_HTTP_blocked',blocked.get('error')=='v2_offline_firewall_denied' and Fixture.hits==0)
 check('mail_transport_blocked',call('mail')['wp_mail_result'] is False)
 backup=PRIVATE/'snapshot.zip'
 with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
  for path,name in [(db,'wordpress.sqlite'),(marker,'marker.txt'),(guard,'offline-guard.php')]:z.write(path,name)
 check('real_backup_zip_integrity',zipfile.ZipFile(backup).testzip() is None)
 with zipfile.ZipFile(backup) as z:dbbytes=z.read('wordpress.sqlite');markerbytes=z.read('marker.txt');guardbytes=z.read('offline-guard.php')
 call('break');marker.write_text('INTENTIONALLY MODIFIED OWN FILE\n',encoding='utf-8')
 check('fresh_native_read_sees_deliberate_damage',call('inspect')['blogname']=='INTENTIONAL OWN RESTORE TEST' and marker.read_bytes()!=markerbytes)
 # All PHP processes have exited. Restore ONLY this new owned clone.
 assert db.resolve().is_relative_to(HERE.resolve()) and marker.resolve().is_relative_to(HERE.resolve())
 db.write_bytes(dbbytes);marker.write_bytes(markerbytes);guard.write_bytes(guardbytes)
 restored=call('inspect');check('native_database_and_file_restore_verified',restored['blogname']==baseline['blogname'] and marker.read_bytes()==markerbytes)
 check('restored_guard_matches_backup',guard.read_bytes()==guardbytes)
 call('rule',value='fixed');fixed=call('http',url='http://127.0.0.1:8822/own-wordpress-com-fixture')
 check('narrow_fix_native_WP_HTTP_reaches_actual_loopback_server',fixed.get('status')==200 and Fixture.hits==1,fixture_hits=Fixture.hits,response=fixed)
 for url in ['https://public-api.wordpress.com/','https://example.invalid/','http://127.0.0.1:8822/unapproved-path']:
  denial=call('http',url=url);check('unapproved_URL_still_blocked_'+url,denial.get('error')=='v2_offline_firewall_denied' and Fixture.hits==1)
 order=call('order');check('native_cart_accepts_physical_and_virtual',order.get('added_physical') and order.get('added_virtual'),readback=order)
 check('native_shipping_rate_available',bool(order.get('rates')) and any(float(r['cost'])==12 for r in order['rates'].values()),rates=order.get('rates'))
 check('native_BACS_test_order_created',order.get('native_payment_result')=='success' and order.get('status')=='on-hold' and order.get('order_items')==2,real_charge=False)
 readback=call('read_order',id=order['order_id']);check('fresh_process_order_shipping_payment_readback',readback['items']==2 and readback['payment']=='bacs' and readback['shipping_total']==order['shipping_total'] and readback['status']=='on-hold',readback=readback)
 check('source_database_and_configuration_unchanged',all(sha(SOURCE/p)==digest for p,digest in before.items()))
 result=dict(status='PASS_NATIVE_WP_WOO_ISOLATED',checked_at=datetime.now(timezone.utc).isoformat(),test_count=len(tests),tests=tests,scope='Own fixture: backup/restore, narrow local HTTP firewall rule, native cart/shipping/BACS order regression',wordpress=baseline['wordpress'],woocommerce=baseline['woocommerce'],old_published_sources_unchanged=True,real_wordpress_com_contact=False,real_client_firewall_repaired=False,real_payment=False,email_sent=False,external_network_calls=0,local_fixture_http_requests=Fixture.hits,client_case=False,version_updates_tested=False,performance_improvement_claimed=False,browser_checkout_tested=False,limits='Controlled fault in own mu-plugin and own loopback endpoint; no claim of diagnosing an actual Jetpack/WordPress.com hosting failure. Native API checkout test; root/client browser regression still required.')
 (PUBLIC/'qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 (PUBLIC/'native-check.php').write_bytes((HERE/'native-check.php').read_bytes());(PUBLIC/'offline-guard.php').write_bytes(guard.read_bytes());(PUBLIC/'verify.py').write_bytes(Path(__file__).read_bytes())
 with zipfile.ZipFile(PUBLIC/'wp-maintenance-own-source.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in ['native-check.php','offline-guard.php','verify.py','qa.json']:z.write(PUBLIC/p,p)
 print(json.dumps(dict(status=result['status'],tests=len(tests),wordpress=result['wordpress'],woocommerce=result['woocommerce'],source_unchanged=True,real_charge=False,network_external=0)))
finally:server.shutdown();server.server_close()
