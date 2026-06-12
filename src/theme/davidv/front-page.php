<?php
/**
 * Главная.
 */
if ( ! defined( 'ABSPATH' ) ) exit;
get_header();

$services = davidv_services();

// карта slug услуги -> кейс (если кейс с таким slug существует)
$case_by_service = array();
$cases_q = new WP_Query( array( 'post_type' => 'case', 'posts_per_page' => -1, 'orderby' => 'menu_order', 'order' => 'ASC' ) );
if ( $cases_q->have_posts() ) {
	foreach ( $cases_q->posts as $p ) {
		$case_by_service[ $p->post_name ] = $p;
	}
}
?>

<!-- ===================== HERO ===================== -->
<section class="hero" data-hero>
	<div class="wrap hero__grid">

		<div class="hero__intro">
			<p class="kicker reveal" data-reveal>// инженер инфраструктуры</p>
			<h1 class="hero__title">
				<span class="line"><span data-word>Держу</span> <span data-word>в</span> <span data-word>работе</span></span>
				<span class="line"><span data-word>инфраструктуру,</span></span>
				<span class="line"><span data-word>на</span> <span data-word>которой</span> <span data-word class="accent">крутится</span></span>
				<span class="line"><span data-word>ваш</span> <span data-word>бизнес.</span></span>
			</h1>
			<p class="hero__sub reveal" data-reveal>
				Телефония, Linux-серверы, DevOps и автоматизация — собираю, поднимаю
				и не даю упасть. От первого звонка до зелёного дашборда.
			</p>
			<div class="btn-row reveal" data-reveal>
				<a class="btn btn--primary" href="#work">Смотреть кейсы <?php echo davidv_icon( 'arrow', 'ico ico--sm' ); ?></a>
				<a class="btn btn--ghost" href="#services">5 направлений</a>
			</div>
		</div>

		<!-- СИГНАТУРА: живая status/uptime панель -->
		<aside class="monitor" data-monitor aria-label="Статус сервисов" role="img"
		       aria-description="Анимированная панель мониторинга: все пять сервисов в состоянии active (running), аптайм 99.98%.">
			<div class="monitor__bar">
				<span class="monitor__dots"><i></i><i></i><i></i></span>
				<span class="monitor__name">monitor — david.v</span>
				<span class="monitor__rt" data-clock>--:--:--</span>
			</div>
			<div class="monitor__body">
				<p class="monitor__cmd"><span class="prompt">$</span> <span data-typed data-text="systemctl status portfolio.service">systemctl status portfolio.service</span><span class="caret" data-caret>&nbsp;</span></p>

				<ul class="svclist" data-svclist>
					<?php $i = 1; foreach ( $services as $slug => $s ) : ?>
						<li class="svc" data-svc style="--n: <?php echo $i; ?>">
							<span class="svc__dot" aria-hidden="true"></span>
							<span class="svc__name"><?php echo davidv_icon( $s['glyph'], 'ico ico--sm' ); ?><?php echo esc_html( $s['label'] ); ?></span>
							<span class="svc__state">active (running)</span>
						</li>
					<?php $i++; endforeach; ?>
				</ul>

				<div class="monitor__foot">
					<div class="uptime">
						<span class="uptime__k">uptime</span>
						<span class="uptime__v" data-uptime>99.98<span class="pct">%</span></span>
					</div>
					<svg class="spark" viewBox="0 0 120 32" preserveAspectRatio="none" aria-hidden="true">
						<path data-spark d="M0,24 L12,20 L24,26 L36,14 L48,18 L60,8 L72,16 L84,6 L96,12 L108,4 L120,10" />
					</svg>
				</div>
			</div>
		</aside>

	</div>
	<div class="hero__scroll" aria-hidden="true"><span>scroll</span></div>
</section>

<!-- ===================== ПОЗИЦИОНИРОВАНИЕ ===================== -->
<section class="strip">
	<div class="wrap strip__inner reveal" data-reveal>
		<p class="strip__text">
			Не «настрою и забуду», а <span class="accent">владею системой целиком</span>:
			проектирую, разворачиваю в Docker, закрываю мониторингом и автоматизирую рутину —
			чтобы оно работало без вас.
		</p>
	</div>
</section>

<!-- ===================== УСЛУГИ ===================== -->
<section class="services" id="services">
	<div class="wrap">
		<header class="sec-head reveal" data-reveal>
			<p class="kicker">// 5 направлений</p>
			<h2 class="sec-title">Что я делаю</h2>
		</header>

		<ul class="svc-grid">
			<?php $i = 1; foreach ( $services as $slug => $s ) :
				$case = $case_by_service[ $slug ] ?? null;
				$href = $case ? get_permalink( $case ) : '#work';
			?>
			<li class="svc-card reveal" data-reveal style="--d: <?php echo $i * 0.05; ?>s">
				<a class="svc-card__link" href="<?php echo esc_url( $href ); ?>">
					<span class="svc-card__idx"><?php printf( '%02d', $i ); ?></span>
					<span class="svc-card__ico"><?php echo davidv_icon( $s['glyph'] ); ?></span>
					<h3 class="svc-card__title"><?php echo esc_html( $s['label'] ); ?></h3>
					<p class="svc-card__tag"><?php echo esc_html( $s['tag'] ); ?></p>
					<span class="svc-card__go"><?php echo $case ? 'Кейс' : 'Скоро'; ?> <?php echo davidv_icon( 'arrow', 'ico ico--sm' ); ?></span>
				</a>
			</li>
			<?php $i++; endforeach; ?>
		</ul>
	</div>
</section>

<!-- ===================== КЕЙСЫ ===================== -->
<section class="work" id="work">
	<div class="wrap">
		<header class="sec-head reveal" data-reveal>
			<p class="kicker">// избранное</p>
			<h2 class="sec-title">Кейсы</h2>
		</header>

		<?php if ( $cases_q->have_posts() ) : ?>
		<ul class="work-grid">
			<?php foreach ( $cases_q->posts as $idx => $p ) :
				$pid    = $p->ID;
				$metric = davidv_field( 'result_metric', $pid );
				$role   = davidv_field( 'role_label', $pid, 'кейс' );
				$summary = davidv_field( 'summary', $pid, get_the_excerpt( $pid ) );
			?>
			<li class="work-card reveal" data-reveal>
				<a class="work-card__link" href="<?php echo esc_url( get_permalink( $pid ) ); ?>">
					<div class="work-card__media">
						<?php if ( has_post_thumbnail( $pid ) ) : ?>
							<?php echo get_the_post_thumbnail( $pid, 'case_card', array( 'loading' => 'lazy', 'alt' => esc_attr( get_the_title( $pid ) ) ) ); ?>
						<?php else : ?>
							<span class="work-card__ph" aria-hidden="true"><?php echo davidv_icon( 'pipeline' ); ?></span>
						<?php endif; ?>
						<?php if ( $metric ) : ?><span class="work-card__metric"><?php echo esc_html( $metric ); ?></span><?php endif; ?>
					</div>
					<div class="work-card__body">
						<p class="work-card__role"><?php echo esc_html( $role ); ?></p>
						<h3 class="work-card__title"><?php echo esc_html( get_the_title( $pid ) ); ?></h3>
						<p class="work-card__sum"><?php echo esc_html( wp_trim_words( $summary, 16 ) ); ?></p>
					</div>
				</a>
			</li>
			<?php endforeach; ?>
		</ul>
		<?php else : ?>
			<p class="muted">Кейсы скоро появятся.</p>
		<?php endif; wp_reset_postdata(); ?>
	</div>
</section>

<?php get_footer();
