<?php
/** Local proof theme functions. No configuration, messaging or remote endpoints. */
defined( 'ABSPATH' ) || exit;

function own_native_workshop_setup() {
    add_theme_support( 'wp-block-styles' );
    add_theme_support( 'editor-styles' );
    add_theme_support( 'responsive-embeds' );
    add_editor_style( 'style.css' );
}
add_action( 'after_setup_theme', 'own_native_workshop_setup' );

function own_native_workshop_styles() {
    wp_enqueue_style(
        'own-native-workshop',
        get_stylesheet_uri(),
        array(),
        wp_get_theme()->get( 'Version' )
    );
}
add_action( 'wp_enqueue_scripts', 'own_native_workshop_styles' );

function own_native_workshop_pattern_category() {
    register_block_pattern_category(
        'own-native-workshop',
        array(
            'label'       => __( 'Własne koncepcje warsztatu', 'own-native-workshop' ),
            'description' => __( 'Trzy kompletne, autorskie strony z edytowalnych bloków podstawowych.', 'own-native-workshop' ),
        )
    );
}
add_action( 'init', 'own_native_workshop_pattern_category' );
add_filter( 'should_load_remote_block_patterns', '__return_false' );

/** Local dataLayer proof; no Google container, remote tags, or personal data. */
function own_native_workshop_data_layer() {
    wp_enqueue_script('workshop-data-layer', get_theme_file_uri('assets/workshop-data-layer.js'), array(), '1.0.0', true);
}
add_action('wp_enqueue_scripts', 'own_native_workshop_data_layer');
