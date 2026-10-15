<?php
/**
 * Own fictional property sample: WordPress core Classic Editor + native SEO fields.
 * No credentials, theme secrets, remote services or licensed plugins required.
 * Copy into a test site's wp-content/mu-plugins; set cypr_proof_post_id option
 * to the ID of your own fictional demonstration post. Never target client posts.
 */
defined('ABSPATH') || exit;
function cypr_own_proof_id() { return (int)get_option('cypr_proof_post_id'); }
add_filter('use_block_editor_for_post', function($use, $post) {
 return $post && $post->ID===cypr_own_proof_id() ? false : $use;
}, 20, 2);
add_action('add_meta_boxes_post',function($post){
 if($post->ID!==cypr_own_proof_id())return;
 add_meta_box('cypr-native-seo','Własna próbka EN→PL / podstawowe SEO',function($post){
  wp_nonce_field('cypr_own_seo_'.$post->ID,'cypr_own_seo_nonce');
  echo '<p><strong>Własny fikcyjny przykład.</strong> To nie jest realizacja dla klienta. Edytor powyżej to natywny klasyczny edytor WordPressa; treść została pierwotnie zapisana jako 12 bloków Gutenberga.</p>';
  echo '<p><label for="cypr-seo-title">Tytuł SEO</label><br><input id="cypr-seo-title" name="cypr_seo_title" type="text" class="widefat" value="'.esc_attr(get_post_meta($post->ID,'_cypr_seo_title',true)).'"></p>';
  echo '<p><label for="cypr-seo-description">Opis SEO</label><br><textarea id="cypr-seo-description" name="cypr_seo_description" rows="3" class="widefat">'.esc_textarea(get_post_meta($post->ID,'_cypr_seo_description',true)).'</textarea></p>';
  echo '<p>Źródło: EN · tekst oferty: PL. Dane, cena i ilustracje są fikcyjne. Właściwe zdjęcia i ceny zatwierdza autor oferty.</p>';
 },'post','normal','high');
});
add_action('save_post_post',function($id){
 if($id!==cypr_own_proof_id() || wp_is_post_revision($id) || (defined('DOING_AUTOSAVE')&&DOING_AUTOSAVE))return;
 if(!current_user_can('edit_post',$id) || empty($_POST['cypr_own_seo_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['cypr_own_seo_nonce'])),'cypr_own_seo_'.$id))return;
 if(isset($_POST['cypr_seo_title']))update_post_meta($id,'_cypr_seo_title',sanitize_text_field(wp_unslash($_POST['cypr_seo_title'])));
 if(isset($_POST['cypr_seo_description']))update_post_meta($id,'_cypr_seo_description',sanitize_textarea_field(wp_unslash($_POST['cypr_seo_description'])));
});
