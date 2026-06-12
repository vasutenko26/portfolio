<?php
/** Уникальные slug по языкам: en=key, uk=key-uk, ru=key-ru (надёжная резолюция). */
$suffix = array( 'en' => '', 'uk' => '-uk', 'ru' => '-ru' );

foreach ( array( 'telephony', 'linux', 'devops', 'automation', 'web' ) as $key ) {
	$ids = get_posts( array(
		'post_type' => 'case', 'posts_per_page' => -1, 'fields' => 'ids',
		'meta_key' => 'service_key', 'meta_value' => $key, 'lang' => '',
	) );
	foreach ( $ids as $id ) {
		$lang = pll_get_post_language( $id );
		$want = $key . ( $suffix[ $lang ] ?? '' );
		wp_update_post( array( 'ID' => $id, 'post_name' => $want ) );
		clean_post_cache( $id );
		echo "#$id [$lang] -> " . get_post_field( 'post_name', $id ) . "\n";
	}
}
