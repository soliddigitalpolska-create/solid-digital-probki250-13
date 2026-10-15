<?php
if(PHP_SAPI!=='cli')exit;
$_SERVER['HTTP_HOST']='127.0.0.1:8807';$_SERVER['REQUEST_URI']='/';
require __DIR__.'/site/wordpress/wp-load.php';wp_set_current_user(1);
if(!defined('WC_VERSION'))throw new Exception('Native Woo not active');
$a=json_decode(stream_get_contents(STDIN),true)?:[];$op=$a['op']??'inspect';
$file=__DIR__.'/private/state.json';$state=file_exists($file)?json_decode(file_get_contents($file),true):[];
function out($data){echo wp_json_encode($data,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT),"\n";}
function perms($oid){global $wpdb;return $wpdb->get_results($wpdb->prepare("SELECT permission_id,product_id,order_id,downloads_remaining,download_count,access_expires FROM {$wpdb->prefix}woocommerce_downloadable_product_permissions WHERE order_id=%d",$oid),ARRAY_A);}
function state_view($s){$o=wc_get_order($s['order_id']);$p=wc_get_product($s['product_id']);$items=$o->get_items();$item=reset($items);return ['wordpress'=>get_bloginfo('version'),'woocommerce'=>WC_VERSION,'site'=>home_url('/'),'product_id'=>$p->get_id(),'product_name'=>$p->get_name(),'virtual'=>$p->is_virtual(),'downloadable'=>$p->is_downloadable(),'order_id'=>$o->get_id(),'order_status'=>$o->get_status(),'is_paid'=>$o->is_paid(),'is_download_permitted'=>$o->is_download_permitted(),'downloadable_items'=>count($o->get_downloadable_items()),'permissions'=>perms($o->get_id()),'download_url'=>$item->get_item_download_url('own_ebook_pdf'),'raw_download_url'=>$s['raw_download_url'],'product_url'=>get_permalink($p->get_id())];}
if($op==='create'){
 if($state)throw new Exception('Run in new empty own clone only');
 update_option('woocommerce_downloads_require_login','no');update_option('woocommerce_downloads_grant_access_after_payment','yes');update_option('woocommerce_file_download_method','force');
 update_option('woocommerce_enable_guest_checkout','yes');update_option('blogname','Tydzień bez chaosu / własne demo offline');
 $p=new WC_Product_Simple();$p->set_name('Tydzień bez chaosu - własny e-book demonstracyjny');$p->set_slug('tydzien-bez-chaosu-demo');$p->set_status('publish');$p->set_catalog_visibility('visible');$p->set_regular_price('19.00');$p->set_virtual(true);$p->set_downloadable(true);$p->set_manage_stock(false);$p->set_stock_status('instock');$p->set_download_limit(2);$p->set_download_expiry(7);
 $p->set_description('Własny mini-e-book PDF, 11 stron. Lokalny produkt testowy. Brak prawdziwej płatności, BLIK i wysyłki e-mail.');
 $dl=new WC_Product_Download();$dl->set_id('own_ebook_pdf');$dl->set_name('Tydzień bez chaosu / PDF');$url=home_url('/wp-content/uploads/woocommerce_uploads/tydzien-bez-chaosu-demo.pdf');$dl->set_file($url);$p->set_downloads([$dl]);$pid=$p->save();
 $home=wp_insert_post(['post_title'=>'Tydzień bez chaosu','post_content'=>'Własny materiał demonstracyjny. Lokalny test natywnego WooCommerce.','post_type'=>'page','post_status'=>'publish']);update_option('page_on_front',$home);update_option('show_on_front','page');
 $order=wc_create_order(['status'=>'pending','customer_id'=>0]);$order->set_billing_email('ebook-own-test@example.invalid');$order->set_billing_first_name('Own');$order->set_billing_last_name('Demo');$order->set_payment_method('own_offline_state_fixture');$order->set_payment_method_title('Offline own state fixture - no actual payment');$order->add_product($p,1);$order->calculate_totals();$order->save();
 $state=['product_id'=>$pid,'order_id'=>$order->get_id(),'raw_download_url'=>$url];file_put_contents($file,wp_json_encode($state));out(state_view($state));exit;
}
if(!$state)throw new Exception('Missing own state');
$o=wc_get_order($state['order_id']);
if($op==='presentation'){
 $cover=__DIR__.'/site/wordpress/wp-content/uploads/own-ebook-preview/cover.png';
 $id=wp_insert_attachment(['post_mime_type'=>'image/png','post_title'=>'Tydzień bez chaosu / własna okładka','post_status'=>'inherit'],$cover);
 require_once ABSPATH.'wp-admin/includes/image.php';wp_update_attachment_metadata($id,wp_generate_attachment_metadata($id,$cover));
 $p=wc_get_product($state['product_id']);$p->set_image_id($id);$p->save();out(['own_cover_attached'=>true,'product_id'=>$p->get_id(),'attachment_id'=>$id]);exit;
}
if($op==='offline_payment_complete'){$o->payment_complete('OWN_OFFLINE_FIXTURE_NO_CHARGE');$o->save();}
if($op==='repeat_payment_complete'){$o->payment_complete('OWN_OFFLINE_FIXTURE_NO_CHARGE');$o->save();}
if($op==='refund_state'){$o->update_status('refunded','Own offline state-only test. No payment gateway.');$o->save();}
if($op==='environment'){
 $mail=wp_mail('nobody@example.invalid','Own blocked test','No transport allowed');$http=wp_remote_get('https://example.invalid/own-no-network');out(['mail_shortcircuited'=>$mail===false,'http_blocked'=>is_wp_error($http),'http_code'=>is_wp_error($http)?$http->get_error_code():null,'native_WP'=>get_bloginfo('version'),'native_Woo'=>WC_VERSION]);exit;
}
out(state_view($state));
