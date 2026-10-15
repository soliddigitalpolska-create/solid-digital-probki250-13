<?php
if(PHP_SAPI!=='cli')exit;
$_SERVER['HTTP_HOST']='127.0.0.1:8821';$_SERVER['REQUEST_URI']='/';
require __DIR__.'/site/wordpress/wp-load.php';
$input=json_decode(stream_get_contents(STDIN),true)?:[];$op=$input['op']??'inspect';
wp_set_current_user(1);
function out($data){echo wp_json_encode($data,JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES),"\n";exit;}
function httpcheck($url){$r=wp_remote_get($url,['timeout'=>5]);return is_wp_error($r)?['error'=>$r->get_error_code()]:['status'=>wp_remote_retrieve_response_code($r),'body'=>wp_remote_retrieve_body($r)];}
if($op==='inspect')out(['wordpress'=>get_bloginfo('version'),'woocommerce'=>defined('WC_VERSION')?WC_VERSION:null,'blogname'=>get_option('blogname'),'rule'=>get_option('v2_fixture_rule','broken'),'products'=>array_map(static function($id){$p=wc_get_product($id);return ['id'=>$id,'name'=>$p->get_name(),'price'=>$p->get_price(),'virtual'=>$p->is_virtual()];},[15,18])]);
if($op==='break'){update_option('blogname','INTENTIONAL OWN RESTORE TEST');out(['modified'=>get_option('blogname')]);}
if($op==='rule'){update_option('v2_fixture_rule',$input['value']);out(['rule'=>get_option('v2_fixture_rule')]);}
if($op==='http')out(httpcheck($input['url']));
if($op==='mail')out(['wp_mail_result'=>wp_mail('nobody@example.invalid','Own offline test','No real transport permitted')]);
if($op==='order'){
 WC()->frontend_includes();
 WC()->session=new WC_Session_Handler();WC()->session->init();
 WC()->customer=new WC_Customer(0,true);
 WC()->customer->set_billing_country('PL');WC()->customer->set_billing_postcode('60-001');WC()->customer->set_billing_city('Poznań');
 WC()->customer->set_shipping_country('PL');WC()->customer->set_shipping_postcode('60-001');WC()->customer->set_shipping_city('Poznań');WC()->customer->set_calculated_shipping(true);
 $zone=new WC_Shipping_Zone();$zone->set_zone_name('Own V2 PL test zone');$zone->set_zone_order(0);$zone->save();$zone->add_location('PL','country');
 $instance=$zone->add_shipping_method('flat_rate');
 $method=$zone->get_shipping_methods(true)[$instance];$method->update_option('enabled','yes');$method->update_option('cost','12');
 WC_Cache_Helper::get_transient_version('shipping',true);
 WC()->cart=new WC_Cart();
 $a=WC()->cart->add_to_cart(15,1);$b=WC()->cart->add_to_cart(18,1);
 $packages=WC()->cart->get_shipping_packages();$shipping=WC()->shipping()->calculate_shipping($packages);$rates=[];
 foreach($shipping as $pack)foreach($pack['rates'] as $key=>$rate)$rates[$key]=['cost'=>$rate->get_cost(),'label'=>$rate->get_label()];
 $chosen=array_key_first($rates);WC()->session->set('chosen_shipping_methods',[$chosen]);WC()->cart->calculate_totals();
 $gateways=WC()->payment_gateways()->get_available_payment_gateways();
 $data=['billing_first_name'=>'Own','billing_last_name'=>'Fixture','billing_email'=>'own-fixture@example.invalid','billing_address_1'=>'Testowa 1','billing_city'=>'Poznań','billing_postcode'=>'60-001','billing_country'=>'PL','shipping_first_name'=>'Own','shipping_last_name'=>'Fixture','shipping_address_1'=>'Testowa 1','shipping_city'=>'Poznań','shipping_postcode'=>'60-001','shipping_country'=>'PL','payment_method'=>'bacs'];
 $id=WC()->checkout()->create_order($data);if(is_wp_error($id))out(['error'=>$id->get_error_message(),'rates'=>$rates]);
 $order=wc_get_order($id);$order->set_payment_method('bacs');$order->save();
 $native_result=$gateways['bacs']->process_payment($id);$order=wc_get_order($id);
 out(['order_id'=>$id,'cart_items'=>count(WC()->cart->get_cart()),'added_physical'=>(bool)$a,'added_virtual'=>(bool)$b,'rates'=>$rates,'chosen'=>$chosen,'gateways'=>array_keys($gateways),'native_payment_result'=>$native_result['result']??null,'status'=>$order->get_status(),'total'=>$order->get_total(),'shipping_total'=>$order->get_shipping_total(),'order_items'=>count($order->get_items()),'real_charge'=>false]);
}
if($op==='read_order'){$o=wc_get_order((int)$input['id']);out(['id'=>$o->get_id(),'status'=>$o->get_status(),'total'=>$o->get_total(),'shipping_total'=>$o->get_shipping_total(),'items'=>count($o->get_items()),'payment'=>$o->get_payment_method()]);}
out(['error'=>'Unknown operation']);
