<?php
/** Архив кейсов. */
if ( ! defined( 'ABSPATH' ) ) exit;
get_header(); ?>

<section class="work" style="padding-top:9rem;">
	<div class="wrap">
		<header class="sec-head reveal" data-reveal>
			<p class="kicker">// <?php esc_html_e( 'all disciplines', 'davidv' ); ?></p>
			<h1 class="sec-title"><?php esc_html_e( 'Work', 'davidv' ); ?></h1>
		</header>
		<ul class="work-grid">
			<?php while ( have_posts() ) : the_post(); $pid = get_the_ID();
				$role = davidv_field( 'role_label', $pid, __( 'case', 'davidv' ) );
				$metric = davidv_field( 'result_metric', $pid ); ?>
				<li class="work-card reveal" data-reveal>
					<a class="work-card__link" href="<?php the_permalink(); ?>">
						<div class="work-card__media">
							<?php if ( has_post_thumbnail() ) the_post_thumbnail( 'case_card', array( 'loading' => 'lazy' ) );
							else echo '<span class="work-card__ph" aria-hidden="true">' . davidv_icon( 'pipeline' ) . '</span>'; ?>
							<?php if ( $metric ) : ?><span class="work-card__metric"><?php echo esc_html( $metric ); ?></span><?php endif; ?>
						</div>
						<div class="work-card__body">
							<p class="work-card__role"><?php echo esc_html( $role ); ?></p>
							<h3 class="work-card__title"><?php the_title(); ?></h3>
						</div>
					</a>
				</li>
			<?php endwhile; ?>
		</ul>
	</div>
</section>

<?php get_footer();
