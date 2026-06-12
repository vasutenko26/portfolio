<?php
/**
 * David V — Infrastructure theme
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'DAVIDV_VERSION', '1.0.0' );
define( 'DAVIDV_DIR', get_template_directory() );
define( 'DAVIDV_URI', get_template_directory_uri() );

/* ---------------------------------------------------------------------------
 * Theme setup
 * ------------------------------------------------------------------------- */
add_action( 'after_setup_theme', function () {
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script' ) );
	add_theme_support( 'responsive-embeds' );

	register_nav_menus( array(
		'primary' => 'Главное меню',
	) );

	add_image_size( 'case_card', 900, 600, true );
	add_image_size( 'case_wide', 1600, 900, true );
} );

/* ---------------------------------------------------------------------------
 * Assets — читаем манифест Vite и подключаем хешированный бандл
 * ------------------------------------------------------------------------- */
function davidv_vite_manifest() {
	static $manifest = null;
	if ( $manifest !== null ) return $manifest;
	$path = DAVIDV_DIR . '/assets/build/.vite/manifest.json';
	$manifest = file_exists( $path ) ? json_decode( file_get_contents( $path ), true ) : array();
	return $manifest;
}

add_action( 'wp_enqueue_scripts', function () {
	$manifest = davidv_vite_manifest();
	$entry    = 'assets/src/main.js';
	$base     = DAVIDV_URI . '/assets/build/';

	if ( isset( $manifest[ $entry ] ) ) {
		$item = $manifest[ $entry ];

		// CSS
		if ( ! empty( $item['css'] ) ) {
			foreach ( $item['css'] as $i => $css ) {
				wp_enqueue_style( 'davidv-' . $i, $base . $css, array(), null );
			}
		}
		// JS (как модуль)
		wp_enqueue_script( 'davidv-main', $base . $item['file'], array(), null, true );
	} else {
		// fallback на dev/без сборки
		wp_enqueue_style( 'davidv-fallback', DAVIDV_URI . '/style.css', array(), DAVIDV_VERSION );
	}

	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}
}, 20 );

// Грузим main.js как ES-модуль
add_filter( 'script_loader_tag', function ( $tag, $handle, $src ) {
	if ( 'davidv-main' === $handle ) {
		return '<script type="module" src="' . esc_url( $src ) . '" id="davidv-main-js"></script>' . "\n";
	}
	return $tag;
}, 10, 3 );

/* ---------------------------------------------------------------------------
 * Helpers
 * ------------------------------------------------------------------------- */

/** Достаём ACF-поле с фолбэком, если плагин выключен. */
function davidv_field( $name, $id = null, $default = '' ) {
	$id = $id ?: get_the_ID();
	if ( function_exists( 'get_field' ) ) {
		$v = get_field( $name, $id );
		if ( $v !== null && $v !== false && $v !== '' ) return $v;
	}
	$v = get_post_meta( $id, $name, true );
	return ( $v === '' || $v === null ) ? $default : $v;
}

/** 5 услуг проекта — единый источник правды (иконки = inline SVG в parts/icons). */
function davidv_services() {
	return array(
		'telephony'  => array( 'label' => 'Телефония',     'tag' => 'Asterisk · FreePBX',        'glyph' => 'wave' ),
		'linux'      => array( 'label' => 'Linux-серверы', 'tag' => 'Администрирование · 24/7',   'glyph' => 'server' ),
		'devops'     => array( 'label' => 'DevOps',        'tag' => 'Docker · CI/CD · мониторинг', 'glyph' => 'pipeline' ),
		'automation' => array( 'label' => 'Автоматизация', 'tag' => 'n8n · интеграции',           'glyph' => 'node' ),
		'web'        => array( 'label' => 'Web',           'tag' => 'Сайты · API · хостинг',       'glyph' => 'globe' ),
	);
}

/** Инлайн SVG-иконка по ключу (моno-stroke, наследует currentColor). */
function davidv_icon( $key, $cls = 'ico' ) {
	$icons = array(
		'wave'     => '<path d="M2 12h3l2-7 3 14 3-10 2 5 1-2h3"/>',
		'server'   => '<rect x="3" y="4" width="18" height="6" rx="1"/><rect x="3" y="14" width="18" height="6" rx="1"/><circle cx="7" cy="7" r=".6" fill="currentColor"/><circle cx="7" cy="17" r=".6" fill="currentColor"/>',
		'pipeline' => '<circle cx="5" cy="6" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="12" r="2"/><path d="M7 6h6a4 4 0 0 1 4 4M7 18h6a4 4 0 0 0 4-4"/>',
		'node'     => '<circle cx="12" cy="12" r="3"/><circle cx="4" cy="6" r="1.6"/><circle cx="4" cy="18" r="1.6"/><circle cx="20" cy="12" r="1.6"/><path d="M5.4 6.8 9.6 10M5.4 17.2 9.6 14M15 12h3.4"/>',
		'globe'    => '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 2.5 15.4 0 18M12 3c-2.5 2.6-2.5 15.4 0 18"/>',
		'arrow'    => '<path d="M5 12h14M13 6l6 6-6 6"/>',
		'github'   => '<path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.1-1.47-1.1-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/>',
	);
	$body = $icons[ $key ] ?? '';
	return '<svg class="' . esc_attr( $cls ) . '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $body . '</svg>';
}

/* ---------------------------------------------------------------------------
 * Чистим лишнее из <head> (перф + безопасность)
 * ------------------------------------------------------------------------- */
remove_action( 'wp_head', 'wp_generator' );
remove_action( 'wp_head', 'rsd_link' );
remove_action( 'wp_head', 'wlwmanifest_link' );
remove_action( 'wp_head', 'wp_shortlink_wp_head' );
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );
add_filter( 'the_generator', '__return_empty_string' );
