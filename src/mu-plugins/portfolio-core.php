<?php
/**
 * Plugin Name: Portfolio Core
 * Description: Тип «Кейс», поля и хардненинг для портфолио. Must-use, версионируется в git.
 * Version: 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

/* ---------------------------------------------------------------------------
 * CPT: case (кейсы)
 * ------------------------------------------------------------------------- */
add_action( 'init', function () {
	register_post_type( 'case', array(
		'labels' => array(
			'name'          => 'Кейсы',
			'singular_name' => 'Кейс',
			'add_new_item'  => 'Добавить кейс',
			'edit_item'     => 'Редактировать кейс',
			'menu_name'     => 'Кейсы',
		),
		'public'       => true,
		'has_archive'  => 'cases',
		'menu_icon'    => 'dashicons-screenoptions',
		'menu_position'=> 5,
		'supports'     => array( 'title', 'editor', 'thumbnail', 'excerpt', 'page-attributes' ),
		'rewrite'      => array( 'slug' => 'case', 'with_front' => false ),
		'show_in_rest' => true,
	) );
} );

/* ---------------------------------------------------------------------------
 * Поля кейса (ACF free). Галерея — через вложения, поэтому здесь её нет.
 * ------------------------------------------------------------------------- */
add_action( 'acf/init', function () {
	if ( ! function_exists( 'acf_add_local_field_group' ) ) return;

	acf_add_local_field_group( array(
		'key'      => 'group_case',
		'title'    => 'Кейс — содержимое',
		'location' => array( array( array( 'param' => 'post_type', 'operator' => '==', 'value' => 'case' ) ) ),
		'position' => 'normal',
		'fields'   => array(
			array( 'key' => 'f_role',   'label' => 'Роль / направление (лейбл)', 'name' => 'role_label',    'type' => 'text', 'placeholder' => 'DevOps' ),
			array( 'key' => 'f_sum',    'label' => 'Краткое описание (для карточек)', 'name' => 'summary', 'type' => 'textarea', 'rows' => 2 ),
			array( 'key' => 'f_stack',  'label' => 'Стек (через запятую)', 'name' => 'stack', 'type' => 'text', 'placeholder' => 'Docker, GitLab CI, Grafana' ),
			array( 'key' => 'f_metric', 'label' => 'Метрика результата', 'name' => 'result_metric', 'type' => 'text', 'placeholder' => '99.98% uptime' ),
			array( 'key' => 'f_task',   'label' => '01 — Задача',     'name' => 'task',     'type' => 'wysiwyg', 'media_upload' => 0, 'toolbar' => 'basic' ),
			array( 'key' => 'f_appr',   'label' => '02 — Что сделал', 'name' => 'approach', 'type' => 'wysiwyg', 'media_upload' => 0, 'toolbar' => 'basic' ),
			array( 'key' => 'f_res',    'label' => '03 — Результат',  'name' => 'result',   'type' => 'wysiwyg', 'media_upload' => 0, 'toolbar' => 'basic' ),
			array( 'key' => 'f_repo',   'label' => 'Ссылка на репозиторий', 'name' => 'repo_url', 'type' => 'url' ),
			array( 'key' => 'f_video',  'label' => 'Видео (URL, опц.)', 'name' => 'video_url', 'type' => 'url' ),
		),
	) );
} );

/* ---------------------------------------------------------------------------
 * Скриншоты кейса = прикреплённые к нему изображения (исключая обложку)
 * ------------------------------------------------------------------------- */
function portfolio_case_gallery( $post_id ) {
	$thumb = get_post_thumbnail_id( $post_id );
	$atts  = get_posts( array(
		'post_type'      => 'attachment',
		'post_mime_type' => 'image',
		'post_parent'    => $post_id,
		'posts_per_page' => -1,
		'orderby'        => 'menu_order date',
		'order'          => 'ASC',
		'exclude'        => $thumb ? array( $thumb ) : array(),
		'post_status'    => 'inherit',
	) );
	return wp_list_pluck( $atts, 'ID' );
}

/* ---------------------------------------------------------------------------
 * Polylang: делаем CPT «Кейс» переводимым (вне зависимости от настроек UI)
 * ------------------------------------------------------------------------- */
add_filter( 'pll_get_post_types', function ( $types, $is_settings ) {
	$types['case'] = 'case';
	return $types;
}, 10, 2 );

/* ---------------------------------------------------------------------------
 * Хардненинг
 * ------------------------------------------------------------------------- */
// XML-RPC полностью выключен
add_filter( 'xmlrpc_enabled', '__return_false' );
add_filter( 'wp_headers', function ( $headers ) {
	unset( $headers['X-Pingback'] );
	return $headers;
} );
// Режем методы pingback
add_filter( 'xmlrpc_methods', function () { return array(); } );

// Прячем перечисление пользователей через REST для неавторизованных
add_filter( 'rest_endpoints', function ( $endpoints ) {
	if ( ! is_user_logged_in() ) {
		unset( $endpoints['/wp/v2/users'] );
		unset( $endpoints['/wp/v2/users/(?P<id>[\d]+)'] );
	}
	return $endpoints;
} );

// Блокируем ?author=N enumeration
add_action( 'template_redirect', function () {
	if ( ! is_admin() && isset( $_GET['author'] ) && ! is_user_logged_in() ) {
		wp_redirect( home_url( '/' ), 301 );
		exit;
	}
} );

// Отключаем комментарии целиком (портфолио)
add_action( 'init', function () {
	remove_post_type_support( 'post', 'comments' );
	remove_post_type_support( 'page', 'comments' );
} );
add_filter( 'comments_open', '__return_false' );
add_filter( 'pings_open', '__return_false' );
