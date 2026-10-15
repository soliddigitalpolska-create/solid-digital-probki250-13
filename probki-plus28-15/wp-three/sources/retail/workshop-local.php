<?php
/** Local workshop: prevent mail and remote tracking; restrict XML-RPC. */
defined('ABSPATH') || exit;
add_filter('pre_wp_mail', '__return_true');
add_filter('xmlrpc_enabled', '__return_false');
add_filter('woocommerce_allow_tracking', '__return_false');
add_filter('woocommerce_admin_disabled', '__return_true');
add_filter('woocommerce_enable_setup_wizard', '__return_false');
add_filter('wp_is_application_passwords_available', '__return_false');
add_filter('should_load_remote_block_patterns', '__return_false');
add_action('woocommerce_single_product_summary', function () {
    echo '<p class="workshop-product-note">Autorska modyfikacja PHP: produkt warsztatowy, zamówienia wyłącznie testowe.</p>';
}, 25);
add_filter('gettext', function ($translated, $text, $domain) {
    if ($domain !== 'woocommerce') return $translated;
    $labels=['Add to cart'=>'Dodaj do koszyka','View cart'=>'Zobacz koszyk','Select options'=>'Wybierz opcje','Sale!'=>'Promocja','Product'=>'Produkt','Price'=>'Cena','Quantity'=>'Ilość','Subtotal'=>'Suma częściowa','Cart totals'=>'Podsumowanie koszyka','Shipping'=>'Dostawa','Total'=>'Razem','Proceed to checkout'=>'Przejdź do zamówienia','Update cart'=>'Aktualizuj koszyk','Apply coupon'=>'Zastosuj kupon','Coupon code'=>'Kod kuponu','Description'=>'Opis','Additional information'=>'Dodatkowe informacje','Reviews'=>'Opinie','Related products'=>'Podobne produkty','Billing details'=>'Dane do zamówienia','Place order'=>'Złóż zamówienie testowe','Your order'=>'Twoje zamówienie','Shop'=>'Sklep'];
    return $labels[$text] ?? $translated;
}, 20, 3);
add_action('wp_head',function(){if(is_singular()){$description=get_post_meta(get_queried_object_id(),'_workshop_seo_description',true);if($description)echo '<meta name="description" content="'.esc_attr($description).'">';}});
