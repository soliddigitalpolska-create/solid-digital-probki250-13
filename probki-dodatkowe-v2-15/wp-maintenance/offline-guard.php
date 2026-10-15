<?php
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
