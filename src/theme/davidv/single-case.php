<?php
/**
 * Единый шаблон кейса.
 */
if ( ! defined( 'ABSPATH' ) ) exit;
get_header();

while ( have_posts() ) : the_post();
	$pid      = get_the_ID();
	$role     = davidv_field( 'role_label', $pid, __( 'case', 'davidv' ) );
	$metric   = davidv_field( 'result_metric', $pid );
	$task     = davidv_field( 'task', $pid );
	$approach = davidv_field( 'approach', $pid );
	$result   = davidv_field( 'result', $pid );
	$repo     = davidv_field( 'repo_url', $pid );
	$video    = davidv_field( 'video_url', $pid );
	$gallery  = function_exists( 'portfolio_case_gallery' ) ? portfolio_case_gallery( $pid ) : array();
	$stack    = davidv_field( 'stack', $pid );
?>

<article class="case">
	<header class="case-hero">
		<div class="wrap">
			<a class="back" href="<?php echo esc_url( home_url( '/#work' ) ); ?>"><?php echo davidv_icon( 'arrow', 'ico ico--sm flip' ); ?> <?php esc_html_e( 'all work', 'davidv' ); ?></a>
			<p class="kicker reveal" data-reveal>// <?php echo esc_html( $role ); ?></p>
			<h1 class="case-hero__title reveal" data-reveal><?php the_title(); ?></h1>
			<?php if ( $stack ) : ?>
				<ul class="chips reveal" data-reveal>
					<?php foreach ( array_filter( array_map( 'trim', explode( ',', $stack ) ) ) as $chip ) : ?>
						<li class="chip"><?php echo esc_html( $chip ); ?></li>
					<?php endforeach; ?>
				</ul>
			<?php endif; ?>
		</div>
	</header>

	<div class="wrap case-body">

		<div class="case-cols">
			<section class="case-block reveal" data-reveal>
				<p class="case-block__k">01 — <?php esc_html_e( 'Brief', 'davidv' ); ?></p>
				<div class="prose"><?php echo $task ? wp_kses_post( wpautop( $task ) ) : '<p class="muted">' . esc_html__( 'Brief coming soon.', 'davidv' ) . '</p>'; ?></div>
			</section>
			<section class="case-block reveal" data-reveal>
				<p class="case-block__k">02 — <?php esc_html_e( 'What I did', 'davidv' ); ?></p>
				<div class="prose"><?php echo $approach ? wp_kses_post( wpautop( $approach ) ) : '<p class="muted">' . esc_html__( 'Details coming soon.', 'davidv' ) . '</p>'; ?></div>
			</section>
			<section class="case-block reveal" data-reveal>
				<p class="case-block__k">03 — <?php esc_html_e( 'Outcome', 'davidv' ); ?></p>
				<div class="prose"><?php echo $result ? wp_kses_post( wpautop( $result ) ) : '<p class="muted">' . esc_html__( 'Results coming soon.', 'davidv' ) . '</p>'; ?></div>
				<?php if ( $metric ) : ?><p class="case-metric"><?php echo esc_html( $metric ); ?></p><?php endif; ?>
			</section>
		</div>

		<section class="case-gallery reveal" data-reveal id="gallery">
			<p class="kicker">// <?php esc_html_e( 'gallery', 'davidv' ); ?></p>
			<?php if ( ! empty( $gallery ) && is_array( $gallery ) ) : ?>
				<div class="gallery-grid" data-gallery>
					<?php foreach ( $gallery as $img ) :
						$src  = is_array( $img ) ? ( $img['sizes']['case_wide'] ?? $img['url'] ) : wp_get_attachment_image_url( $img, 'case_wide' );
						$full = is_array( $img ) ? $img['url'] : wp_get_attachment_image_url( $img, 'full' );
						$alt  = is_array( $img ) ? ( $img['alt'] ?? '' ) : get_post_meta( $img, '_wp_attachment_image_alt', true );
						if ( ! $src ) continue;
					?>
						<a class="shot" href="<?php echo esc_url( $full ); ?>" target="_blank" rel="noopener">
							<img src="<?php echo esc_url( $src ); ?>" alt="<?php echo esc_attr( $alt ); ?>" loading="lazy">
						</a>
					<?php endforeach; ?>
				</div>
			<?php else : ?>
				<div class="gallery-grid gallery-grid--empty">
					<?php for ( $i = 0; $i < 3; $i++ ) : ?>
						<span class="shot shot--ph" aria-hidden="true"><?php echo davidv_icon( 'server' ); ?><em><?php esc_html_e( 'demo screenshot', 'davidv' ); ?></em></span>
					<?php endfor; ?>
				</div>
			<?php endif; ?>
		</section>

		<?php if ( $video ) : ?>
		<section class="case-video reveal" data-reveal>
			<p class="kicker">// <?php esc_html_e( 'video', 'davidv' ); ?></p>
			<div class="video-embed"><?php echo wp_oembed_get( esc_url( $video ) ) ?: '<a href="' . esc_url( $video ) . '">' . esc_html( $video ) . '</a>'; ?></div>
		</section>
		<?php endif; ?>

		<footer class="case-foot reveal" data-reveal>
			<?php if ( $repo ) : ?>
				<a class="btn btn--ghost" href="<?php echo esc_url( $repo ); ?>" target="_blank" rel="noopener">
					<?php echo davidv_icon( 'github', 'ico ico--sm' ); ?> <?php esc_html_e( 'Repository', 'davidv' ); ?>
				</a>
			<?php endif; ?>
			<a class="btn btn--primary" href="<?php echo esc_url( home_url( '/#contact' ) ); ?>"><?php esc_html_e( 'Discuss a project', 'davidv' ); ?> <?php echo davidv_icon( 'arrow', 'ico ico--sm' ); ?></a>
		</footer>

	</div>
</article>

<?php endwhile; get_footer();
