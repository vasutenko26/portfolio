<?php
/** Фолбэк-шаблон. */
if ( ! defined( 'ABSPATH' ) ) exit;
get_header(); ?>

<section class="wrap" style="padding:8rem 0; min-height:50vh;">
	<?php if ( have_posts() ) : ?>
		<header class="sec-head"><h1 class="sec-title"><?php echo esc_html( get_the_archive_title() ?: get_bloginfo( 'name' ) ); ?></h1></header>
		<ul class="work-grid">
			<?php while ( have_posts() ) : the_post(); ?>
				<li class="work-card">
					<a class="work-card__link" href="<?php the_permalink(); ?>">
						<div class="work-card__body">
							<h3 class="work-card__title"><?php the_title(); ?></h3>
							<p class="work-card__sum"><?php echo esc_html( wp_trim_words( get_the_excerpt(), 18 ) ); ?></p>
						</div>
					</a>
				</li>
			<?php endwhile; ?>
		</ul>
	<?php else : ?>
		<h1 class="sec-title">Ничего не найдено</h1>
		<p class="muted">Страница пуста или не существует.</p>
		<p><a class="btn btn--ghost" href="<?php echo esc_url( home_url( '/' ) ); ?>">На главную</a></p>
	<?php endif; ?>
</section>

<?php get_footer();
