<?php
/**
 * Переключатель языков — кастомный, под дизайн. Работает на сырых данных Polylang.
 */
if ( ! defined( 'ABSPATH' ) ) exit;
if ( ! function_exists( 'pll_the_languages' ) ) return;

$langs = pll_the_languages( array( 'raw' => 1, 'hide_if_empty' => 0 ) );
if ( empty( $langs ) ) return;

// порядок: en, uk, ru
$order = array( 'en' => 1, 'uk' => 2, 'ru' => 3 );
usort( $langs, function ( $a, $b ) use ( $order ) {
	return ( $order[ $a['slug'] ] ?? 9 ) <=> ( $order[ $b['slug'] ] ?? 9 );
} );
?>
<nav class="lang" aria-label="<?php esc_attr_e( 'Language', 'davidv' ); ?>">
	<?php foreach ( $langs as $l ) :
		$code = strtoupper( $l['slug'] );
		$cur  = ! empty( $l['current_lang'] );
		// если перевода нет — ведём на главную языка, чтобы не терять пользователя
		$url  = ! empty( $l['no_translation'] ) ? home_url( '/' ) : $l['url'];
		$cls  = 'lang__item' . ( $cur ? ' is-current' : '' );
	?>
		<?php if ( $cur ) : ?>
			<span class="<?php echo esc_attr( $cls ); ?>" aria-current="true"><?php echo esc_html( $code ); ?></span>
		<?php else : ?>
			<a class="<?php echo esc_attr( $cls ); ?>" href="<?php echo esc_url( $url ); ?>" lang="<?php echo esc_attr( $l['slug'] ); ?>" hreflang="<?php echo esc_attr( $l['slug'] ); ?>"><?php echo esc_html( $code ); ?></a>
		<?php endif; ?>
	<?php endforeach; ?>
</nav>
