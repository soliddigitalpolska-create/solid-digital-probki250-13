<?php
/** Own offline sample only. Never sends email or makes external WordPress HTTP requests. */
defined('ABSPATH')||exit;
add_filter('pre_wp_mail',static fn()=>false,999);
add_filter('pre_http_request',static fn()=>new WP_Error('own_demo_offline','External requests disabled in this own demonstration.'),999);
