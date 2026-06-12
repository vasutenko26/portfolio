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

<a class="skip-link" href="#main">К содержимому</a>

<header class="site-header" data-header>
	<div class="wrap site-header__inner">
		<a class="brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="На главную">
			<span class="brand__mark" aria-hidden="true">DV</span>
			<span class="brand__text">david<span class="brand__dot">.</span>v</span>
		</a>

		<nav class="nav" aria-label="Основная навигация">
			<a href="<?php echo esc_url( home_url( '/#services' ) ); ?>">Услуги</a>
			<a href="<?php echo esc_url( home_url( '/#work' ) ); ?>">Кейсы</a>
			<a href="<?php echo esc_url( home_url( '/#contact' ) ); ?>">Контакт</a>
		</nav>

		<span class="status-pill" title="Все системы в работе">
			<span class="status-pill__dot" aria-hidden="true"></span>
			<span class="status-pill__txt">operational</span>
		</span>
	</div>
</header>

<main id="main" class="site-main">
