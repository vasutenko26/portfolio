<?php if ( ! defined( 'ABSPATH' ) ) exit;
$cur_lang = function_exists( 'pll_current_language' ) ? pll_current_language() : 'en';
?>
</main><!-- /#main -->

<footer class="site-footer" id="contact">
	<div class="wrap site-footer__inner">
		<div class="site-footer__lead">
			<p class="kicker">// <?php esc_html_e( 'available for work', 'davidv' ); ?></p>
			<h2 class="site-footer__title"><?php esc_html_e( 'Need an engineer who keeps your infrastructure running?', 'davidv' ); ?></h2>

			<form class="cform" data-cform
			      action="https://n8n.davidvasutenko.fun/webhook/contact" method="post"
			      data-sending="<?php esc_attr_e( 'Sending…', 'davidv' ); ?>"
			      data-ok="<?php esc_attr_e( 'Thanks! I’ll get back to you shortly.', 'davidv' ); ?>"
			      data-err="<?php esc_attr_e( 'Something went wrong — please email me directly.', 'davidv' ); ?>">
				<div class="cform__row">
					<label class="cform__field">
						<span class="cform__label"><?php esc_html_e( 'Name', 'davidv' ); ?></span>
						<input type="text" name="name" required autocomplete="name" maxlength="120">
					</label>
					<label class="cform__field">
						<span class="cform__label"><?php esc_html_e( 'Email', 'davidv' ); ?></span>
						<input type="email" name="email" required autocomplete="email" maxlength="160">
					</label>
				</div>
				<label class="cform__field">
					<span class="cform__label"><?php esc_html_e( 'Message', 'davidv' ); ?></span>
					<textarea name="message" rows="4" required maxlength="2000"></textarea>
				</label>

				<!-- honeypot: скрыто от людей и AT, заполняют только боты -->
				<div class="cform__hp" aria-hidden="true">
					<label>Company<input type="text" name="company" tabindex="-1" autocomplete="off"></label>
				</div>
				<input type="hidden" name="lang" value="<?php echo esc_attr( $cur_lang ); ?>">

				<div class="cform__foot">
					<button type="submit" class="btn btn--primary">
						<?php esc_html_e( 'Send', 'davidv' ); ?> <?php echo davidv_icon( 'arrow', 'ico ico--sm' ); ?>
					</button>
					<p class="cform__status" data-cform-status role="status" aria-live="polite"></p>
				</div>
			</form>

			<p class="cform__alt">
				<?php esc_html_e( 'or write directly:', 'davidv' ); ?>
				<a href="mailto:vasutenkod@gmail.com">vasutenkod@gmail.com</a> ·
				<a href="https://t.me/" rel="noopener" target="_blank">Telegram</a>
			</p>
		</div>

		<div class="site-footer__meta">
			<div class="fmeta">
				<span class="fmeta__k">stack</span>
				<span class="fmeta__v">Debian · Docker · Caddy · WordPress · n8n</span>
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
