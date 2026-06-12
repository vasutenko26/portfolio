<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta name="theme-color" content="#0E1116">
	<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<a class="skip-link" href="#main"><?php esc_html_e( 'Skip to content', 'davidv' ); ?></a>

<header class="site-header" data-header>
	<div class="wrap site-header__inner">
		<a class="brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php esc_attr_e( 'Home', 'davidv' ); ?>">
			<span class="brand__mark" aria-hidden="true">DV</span>
			<span class="brand__text">david<span class="brand__dot">.</span>v</span>
		</a>

		<nav class="nav" aria-label="<?php esc_attr_e( 'Primary navigation', 'davidv' ); ?>">
			<a href="<?php echo esc_url( home_url( '/#services' ) ); ?>"><?php esc_html_e( 'Services', 'davidv' ); ?></a>
			<a href="<?php echo esc_url( home_url( '/#work' ) ); ?>"><?php esc_html_e( 'Work', 'davidv' ); ?></a>
			<a href="<?php echo esc_url( home_url( '/#contact' ) ); ?>"><?php esc_html_e( 'Contact', 'davidv' ); ?></a>
		</nav>

		<div class="header__right">
			<?php get_template_part( 'parts/lang-switcher' ); ?>
			<span class="status-pill" title="<?php esc_attr_e( 'All systems operational', 'davidv' ); ?>">
				<span class="status-pill__dot" aria-hidden="true"></span>
				<span class="status-pill__txt">operational</span>
			</span>
		</div>
	</div>
</header>

<main id="main" class="site-main">
