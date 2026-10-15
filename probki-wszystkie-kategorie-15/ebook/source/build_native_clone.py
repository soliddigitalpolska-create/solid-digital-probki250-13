from pathlib import Path
import json,shutil,sqlite3,secrets,hashlib,subprocess,urllib.request,urllib.error,re,socket,time
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
SRC=ROOT/'work/useme-plus28-2026-10-15/proof-wp-three/sites/retail'
dbsrc=SRC/'private/wordpress.sqlite';site=P/'site/wordpress';priv=P/'private';priv.mkdir(exist_ok=True)
before={p:hashlib.sha256((SRC/p).read_bytes()).hexdigest() for p in ['private/wordpress.sqlite','site/wordpress/wp-config.php']}
if not site.exists():shutil.copytree(SRC/'site/wordpress',site,ignore=shutil.ignore_patterns('wp-config.php','*.sqlite','*.sqlite-wal','*.sqlite-shm','debug.log'))
db=priv/'wordpress.sqlite'
if db.exists():raise RuntimeError('Fresh clone required: refuse overwrite existing own DB')
with sqlite3.connect(dbsrc.as_uri()+'?mode=ro',uri=True) as r,sqlite3.connect(db) as w:r.backup(w)
PORT=8807;base=f'http://127.0.0.1:{PORT}'
cfg={'DB_NAME':'own_ebook_demo','DB_USER':'unused','DB_PASSWORD':'unused','DB_HOST':'localhost','DB_CHARSET':'utf8mb4','DB_COLLATE':'','DB_ENGINE':'sqlite','DB_PATH':db.as_posix(),'WP_HOME':base,'WP_SITEURL':base,'WP_ENVIRONMENT_TYPE':'local','WP_DEBUG':False,'WP_DEBUG_DISPLAY':False,'DISALLOW_FILE_EDIT':True,'DISALLOW_FILE_MODS':True,'WP_HTTP_BLOCK_EXTERNAL':True,'AUTOMATIC_UPDATER_DISABLED':True,'DISABLE_WP_CRON':True}
for k in ['AUTH_KEY','SECURE_AUTH_KEY','LOGGED_IN_KEY','NONCE_KEY','AUTH_SALT','SECURE_AUTH_SALT','LOGGED_IN_SALT','NONCE_SALT']:cfg[k]=secrets.token_hex(32)
config='<?php\n'+''.join("define('"+k+"',"+('true' if v is True else 'false' if v is False else "'"+v+"'")+");\n" for k,v in cfg.items())+"$table_prefix='workshop_';if(!defined('ABSPATH'))define('ABSPATH',__DIR__.'/');require_once ABSPATH.'wp-settings.php';\n"
(site/'wp-config.php').write_text(config,encoding='utf-8')
with sqlite3.connect(db) as w:
 w.execute("UPDATE workshop_options SET option_value=? WHERE option_name IN ('home','siteurl')",(base,))
 w.execute('UPDATE workshop_posts SET post_content=replace(post_content,?,?),guid=replace(guid,?,?)',('http://127.0.0.1:8799',base,'http://127.0.0.1:8799',base));w.commit()
for sub in ['woocommerce_uploads','own-ebook-preview']:
 (site/'wp-content/uploads'/sub).mkdir(exist_ok=True)
 shutil.copyfile(P/'public/tydzien-bez-chaosu-demo.pdf',site/'wp-content/uploads'/sub/'tydzien-bez-chaosu-demo.pdf')
shutil.copyfile(P/'public/cover.png',site/'wp-content/uploads/own-ebook-preview/cover.png')
theme=site/'wp-content/themes/own-ebook-demo';theme.mkdir(exist_ok=True)
(theme/'style.css').write_text('/*\nTheme Name: Own Ebook Demo\nVersion: 1.0\n*/',encoding='utf-8')
sales=(P/'public/index.html').read_text(encoding='utf-8').replace('src="cover.png"','src="/wp-content/uploads/own-ebook-preview/cover.png"').replace('href="tydzien-bez-chaosu-demo.pdf"','href="/wp-content/uploads/own-ebook-preview/tydzien-bez-chaosu-demo.pdf"')
sales=sales.replace('<footer>','<section><h2>Natywny produkt testowy WooCommerce</h2><p>Lokalny produkt cyfrowy za przykładowe 19 zł. Środowisko offline: brak prawdziwej płatności i BLIK.</p><a class="btn" href="/product/tydzien-bez-chaosu-demo/">Zobacz natywny produkt Woo</a></section><footer>')
(theme/'front-page.php').write_text('<?php defined("ABSPATH")||exit; ?>\n'+sales,encoding='utf-8')
(theme/'index.php').write_text('<?php defined("ABSPATH")||exit; get_header();while(have_posts()){the_post();the_content();}get_footer();',encoding='utf-8')
(theme/'functions.php').write_text('<?php\nadd_action("after_setup_theme",function(){add_theme_support("woocommerce");});\n',encoding='utf-8')
(theme/'header.php').write_text('<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><?php wp_head(); ?></head><body><p style="padding:15px;background:#dde8df">Własne demo offline. Bez płatności, BLIK i e-maili. <a href="/">Własna strona e-booka</a></p>',encoding='utf-8')
(theme/'footer.php').write_text('<?php wp_footer(); ?></body></html>',encoding='utf-8')
with sqlite3.connect(db) as w:
 w.execute("UPDATE workshop_options SET option_value='own-ebook-demo' WHERE option_name IN ('template','stylesheet')");w.commit()
mu=site/'wp-content/mu-plugins';mu.mkdir(exist_ok=True)
(mu/'own-ebook-loopback.php').write_text("""<?php
defined('ABSPATH')||exit;
add_filter('pre_wp_mail',static fn()=>false,9999);
add_filter('pre_http_request',static fn()=>new WP_Error('own_ebook_network_blocked','Offline own demo - network disabled'),9999);
add_filter('woocommerce_product_is_in_stock',static fn()=>true,9999);
add_action('init',function(){if(($_SERVER['REMOTE_ADDR']??'')==='127.0.0.1'&&parse_url($_SERVER['REQUEST_URI']??'',PHP_URL_PATH)==='/own-ebook-admin/'){wp_set_current_user(1);wp_set_auth_cookie(1,false,false);wp_safe_redirect(admin_url('edit.php?post_type=product'));exit;}});
""",encoding='utf-8')
(P/'router.php').write_text("""<?php
$root=__DIR__.'/site/wordpress';$path=rawurldecode(parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH));
if(preg_match('~(?:^|/)(?:\\.\\.|\\.git|wp-config\\.php|debug\\.log)(?:/|$)|\\.(?:sqlite|ini|log|bak)$~i',$path)||str_starts_with($path,'/wp-content/uploads/woocommerce_uploads/')){http_response_code(403);exit('Forbidden');}
if($path==='/xmlrpc.php'){http_response_code(403);exit;}
if($path!=='/'&&is_file($root.$path))return false;require $root.'/index.php';
""",encoding='utf-8')
php=(SRC/'private/php-path.txt').read_text(encoding='utf-8').strip();ini=Path(php).parent/'php.ini'
(priv/'php-path.txt').write_text(php,encoding='utf-8')
def op(name):
 r=subprocess.run([php,'-c',str(ini),str(P/'native-ebook.php')],input=json.dumps({'op':name}),text=True,encoding='utf-8',capture_output=True,timeout=80)
 start=r.stdout.find('{')
 if r.returncode or start<0:raise RuntimeError((r.stderr+r.stdout)[-2500:])
 return json.loads(r.stdout[start:])
pending=op('create');assert pending['order_status']=='pending' and len(pending['permissions'])==0
sock=socket.socket();assert sock.connect_ex(('127.0.0.1',PORT))!=0;sock.close()
log=(priv/'server.log').open('ab')
proc=subprocess.Popen([php,'-c',str(ini),'-d','error_log='+str(priv/'php-error.log'),'-S',f'127.0.0.1:{PORT}','-t',str(site),str(P/'router.php')],cwd=P,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
(priv/'server.json').write_text(json.dumps({'pid':proc.pid,'port':PORT}),encoding='utf-8')
def get(url):
 assert url.startswith(base+'/')
 try:
  with urllib.request.urlopen(url,timeout=30) as r:return r.status,r.read(),r.headers.get('Content-Type','')
 except urllib.error.HTTPError as e:return e.code,e.read(),e.headers.get('Content-Type','')
for n in range(40):
 try:
  status,body,ct=get(base+'/')
  if status==200:break
 except Exception:time.sleep(.2)
assert status==200 and 'Tydzień'.encode() in body
tests=[]
def test(name,cond,**extra):
 assert cond,(name,extra);tests.append({'test':name,'passed':True,**extra})
test('native_Woo_loaded',bool(pending['woocommerce']),woocommerce=pending['woocommerce'],wordpress=pending['wordpress'])
test('product_virtual_downloadable',pending['virtual'] and pending['downloadable'])
test('pending_has_no_permissions',pending['permissions']==[])
code,raw,ct=get(pending['download_url']);test('pending_download_denied',code>=400,http=code)
code,raw,ct=get(pending['raw_download_url']);test('direct_protected_file_denied',code==403,http=code)
env=op('environment');test('mail_transport_blocked',env['mail_shortcircuited']);test('WP_external_HTTP_blocked',env['http_blocked'])
paid=op('offline_payment_complete');test('native_offline_payment_state',paid['is_paid'] and paid['order_status']=='completed',status=paid['order_status'],real_charge=False)
test('automatic_native_download_permission',len(paid['permissions'])==1 and paid['downloadable_items']==1)
badkey=re.sub(r'([?&]key=)[^&]+',r'\1wrong',paid['download_url'])
code,raw,ct=get(badkey);test('wrong_key_denied',code>=400,http=code)
bademail=re.sub(r'([?&]email=)[^&]+',r'\1wrong%40example.invalid',paid['download_url'])
code,raw,ct=get(bademail);test('wrong_email_denied',code>=400,http=code)
code,pdfbody,ct=get(paid['download_url']);digest=hashlib.sha256(pdfbody).hexdigest();expected=hashlib.sha256((P/'public/tydzien-bez-chaosu-demo.pdf').read_bytes()).hexdigest();test('native_download_returns_exact_PDF',code==200 and digest==expected,http=code,bytes=len(pdfbody),sha256=digest)
after=op('inspect');test('download_count_persisted',int(after['permissions'][0]['download_count'])==1 and str(after['permissions'][0]['downloads_remaining'])=='1',count=after['permissions'][0]['download_count'],remaining=after['permissions'][0]['downloads_remaining'])
again=op('repeat_payment_complete');test('payment_complete_repeated_no_permission_duplicate',len(again['permissions'])==1)
refund=op('refund_state');test('refunded_state_disallows_download',refund['order_status']=='refunded' and not refund['is_download_permitted'])
code,raw,ct=get(paid['download_url']);test('refunded_endpoint_denied_with_remaining_allowance',code>=400,http=code,remaining_before_refund=after['permissions'][0]['downloads_remaining'])
test('source_DB_unchanged',hashlib.sha256(dbsrc.read_bytes()).hexdigest()==before['private/wordpress.sqlite'])
test('source_config_unchanged',hashlib.sha256((SRC/'site/wordpress/wp-config.php').read_bytes()).hexdigest()==before['site/wordpress/wp-config.php'])
public={k:v for k,v in after.items() if k not in ['download_url','raw_download_url']}
result={'status':'PASS_NATIVE_WOO_EBOOK_OFFLINE','test_count':len(tests),'tests':tests,'native_readback':public,'server':base+'/','native_product':pending['product_url'],'native_admin':base+'/own-ebook-admin/','separate_owned_clone':True,'source_unchanged':True,'real_payment':False,'BLIK_integration':False,'Naffy_or_Easycart':False,'email_sent':False,'external_network_blocked':True,'payment_confirmation_mode':'Explicit offline WC_Order::payment_complete fixture; no gateway charge','root_browser_visual_QA':'PENDING','public_customer_data':False}
(P/'native-woo-proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'public/native-woo-proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'tests':len(tests),'server':result['server'],'native_product':result['native_product'],'real_payment':False,'mail_sent':False,'source_unchanged':True},ensure_ascii=False))
