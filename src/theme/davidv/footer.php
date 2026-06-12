<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
</main><!-- /#main -->

<footer class="site-footer" id="contact">
	<div class="wrap site-footer__inner">
		<div class="site-footer__lead">
			<p class="kicker">// <?php esc_html_e( 'available for work', 'davidv' ); ?></p>
			<h2 class="site-footer__title"><?php esc_html_e( 'Need an engineer who keeps your infrastructure running?', 'davidv' ); ?></h2>
			<div class="btn-row">
				<a class="btn btn--primary" href="mailto:vasutenkod@gmail.com">
					<?php esc_html_e( 'Get in touch', 'davidv' ); ?> <?php echo davidv_icon( 'arrow', 'ico ico--sm' ); ?>
				</a>
				<a class="btn btn--ghost" href="https://t.me/" rel="noopener" target="_blank">Telegram</a>
			</div>
		</div>

		<div class="site-footer__meta">
			<div class="fmeta">
				<span class="fmeta__k">stack</span>
				<span class="fmeta__v">Debian · Docker · Caddy · WordPress</span>
			</div>
			<div class="fmeta">
				<span class="fmeta__k"><?php esc_html_e( 'profiles', 'davidv' ); ?></span>
				<span class="fmeta__v">
					<a href="https://github.com/" rel="noopener" target="_blank">GitHub</a> ·
					<a href="#" rel="noopener" target="_blank">Upwork</a>
				</span>
			</div>
			<div class="fmeta">
				<span class="fmeta__k">© <?php echo esc_html( date( 'Y' ) ); ?></span>
				<span class="fmeta__v">David Vasutenko</span>
			</div>
		</div>
	</div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
