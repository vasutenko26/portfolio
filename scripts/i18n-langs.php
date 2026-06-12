<?php
/**
 * Шаг 1: языки + URL-схема Polylang (API 3.8).
 * wp eval-file scripts/i18n-langs.php
 */
$pll = function_exists( 'PLL' ) ? PLL() : null;
if ( ! $pll || ! isset( $pll->model->languages ) ) {
	WP_CLI::error( 'Polylang не готов.' );
}

$want = array(
	array( 'name' => 'English',    'slug' => 'en', 'locale' => 'en_US', 'flag' => 'us', 'term_group' => 0 ),
	array( 'name' => 'Українська', 'slug' => 'uk', 'locale' => 'uk',    'flag' => 'ua', 'term_group' => 1 ),
	array( 'name' => 'Русский',    'slug' => 'ru', 'locale' => 'ru_RU', 'flag' => 'ru', 'term_group' => 2 ),
);

$have = array();
foreach ( $pll->model->languages->get_list() as $L ) $have[] = $L->slug;

foreach ( $want as $l ) {
	if ( in_array( $l['slug'], $have, true ) ) { echo "= {$l['slug']} уже есть\n"; continue; }
	$res = $pll->model->languages->add( array(
		'name' => $l['name'], 'slug' => $l['slug'], 'locale' => $l['locale'],
		'rtl' => 0, 'flag' => $l['flag'], 'term_group' => $l['term_group'],
	) );
	echo is_wp_error( $res ) ? "! {$l['slug']}: " . $res->get_error_message() . "\n" : "+ язык {$l['slug']}\n";
}

// URL-схема: EN дефолт без префикса, /uk/ /ru/ каталогами
$err = $pll->options->merge( array(
	'default_lang'  => 'en',
	'force_lang'    => 1, // язык в каталоге
	'hide_default'  => 1, // дефолт без префикса
	'rewrite'       => 1, // без /language/ в URL
	'redirect_lang' => 1,
) );
$pll->options->save();
echo is_wp_error( $err ) && $err->has_errors() ? '! options: ' . $err->get_error_message() . "\n" : "options: default=en, directory, hide_default\n";

echo "Языков: " . count( $pll->model->languages->get_list() ) . "\n";
