<?php
/**
 * Шаг 2: EN-кейсы + UK/RU переводы (связанные), service_key, ACF-поля.
 * wp eval-file scripts/i18n-content.php
 */
if ( ! function_exists( 'pll_set_post_language' ) ) WP_CLI::error( 'Polylang не готов.' );

$FIELDKEYS = array(
	'role_label' => 'f_role', 'summary' => 'f_sum', 'stack' => 'f_stack',
	'result_metric' => 'f_metric', 'task' => 'f_task', 'approach' => 'f_appr', 'result' => 'f_res',
);

$PH = array(
	'en' => array(
		'task'     => '<p>The original brief: client context, constraints and the goal. Placeholder — filled in as the demo is ready.</p>',
		'approach' => '<p>What was done: solution architecture, tools and the key implementation steps. Placeholder.</p>',
		'result'   => '<p>The outcome and the measurable effect. Placeholder until the demo is published.</p>',
	),
	'uk' => array(
		'task'     => '<p>Опис вихідної задачі: контекст клієнта, обмеження та мета. Плейсхолдер — заповнюється в міру готовності демо.</p>',
		'approach' => '<p>Що було зроблено: архітектура рішення, інструменти та ключові кроки впровадження. Плейсхолдер.</p>',
		'result'   => '<p>Досягнутий результат і вимірюваний ефект. Плейсхолдер до публікації демо.</p>',
	),
	'ru' => array(
		'task'     => '<p>Описание исходной задачи: контекст клиента, ограничения и цель. Плейсхолдер — заполняется по мере готовности демо.</p>',
		'approach' => '<p>Что было сделано: архитектура решения, инструменты и ключевые шаги внедрения. Плейсхолдер.</p>',
		'result'   => '<p>Достигнутый результат и измеримый эффект. Плейсхолдер до публикации демо.</p>',
	),
);

// service_key => order => [lang => [title, role, summary, stack, metric]]
$DATA = array(
	'telephony' => array( 'order' => 1, 'l' => array(
		'en' => array( 'Enterprise telephony on Asterisk/FreePBX', 'Telephony', 'Turn-key PBX: call routing, IVR and call recording.', 'Asterisk, FreePBX, SIP, PJSIP', '<1s call set-up' ),
		'uk' => array( 'Корпоративна телефонія на Asterisk/FreePBX', 'Телефонія', 'АТС під ключ: маршрутизація дзвінків, голосове меню та запис розмов.', 'Asterisk, FreePBX, SIP, PJSIP', "<1с з'єднання" ),
		'ru' => array( 'Корпоративная телефония на Asterisk/FreePBX', 'Телефония', 'АТС, маршрутизация звонков, голосовое меню и запись разговоров под ключ.', 'Asterisk, FreePBX, SIP, PJSIP', '<1с set-up звонка' ),
	) ),
	'linux' => array( 'order' => 2, 'l' => array(
		'en' => array( 'Linux server administration 24/7', 'Linux', 'Maintenance, updates, backups and monitoring of production servers with no downtime.', 'Debian, Ubuntu, systemd, Bash', '99.98% uptime' ),
		'uk' => array( 'Адміністрування Linux-серверів 24/7', 'Linux', 'Підтримка, оновлення, резервні копії та моніторинг бойових серверів без простоїв.', 'Debian, Ubuntu, systemd, Bash', '99.98% uptime' ),
		'ru' => array( 'Администрирование Linux-серверов 24/7', 'Linux', 'Поддержка, обновления, бэкапы и мониторинг боевых серверов без простоев.', 'Debian, Ubuntu, systemd, Bash', '99.98% uptime' ),
	) ),
	'devops' => array( 'order' => 3, 'l' => array(
		'en' => array( 'DevOps pipeline: Docker and CI/CD', 'DevOps', 'Containerization, auto-deploy and observability: from push to prod in minutes.', 'Docker, GitLab CI, Grafana, Prometheus', '2-min deploys' ),
		'uk' => array( 'DevOps-конвеєр: Docker і CI/CD', 'DevOps', 'Контейнеризація, автодеплой і спостережуваність: від пушу до проду за хвилини.', 'Docker, GitLab CI, Grafana, Prometheus', 'деплой за 2 хв' ),
		'ru' => array( 'DevOps-конвейер: Docker и CI/CD', 'DevOps', 'Контейнеризация, автодеплой и наблюдаемость: от пуша до прод за минуты.', 'Docker, GitLab CI, Grafana, Prometheus', 'деплой за 2 мин' ),
	) ),
	'automation' => array( 'order' => 4, 'l' => array(
		'en' => array( 'Process automation with n8n', 'Automation', 'Wired services into one flow: webhooks, integrations and notifications, no routine.', 'n8n, REST, Webhooks, API', '−15h/week of routine' ),
		'uk' => array( 'Автоматизація процесів на n8n', 'Автоматизація', "Зв'язав сервіси в один потік: вебхуки, інтеграції та сповіщення без рутини.", 'n8n, REST, Webhooks, API', '−15год рутини/тижд' ),
		'ru' => array( 'Автоматизация процессов на n8n', 'Автоматизация', 'Связал сервисы в один поток: вебхуки, интеграции и уведомления без рутины.', 'n8n, REST, Webhooks, API', '−15ч рутины/нед' ),
	) ),
	'web' => array( 'order' => 5, 'l' => array(
		'en' => array( 'This site: Caddy + Docker + WordPress', 'Web', 'Custom theme, auto-SSL, caching and Lighthouse 90+ — built in Docker and in git.', 'Caddy, Docker, WordPress, Vite', 'Lighthouse 90+' ),
		'uk' => array( 'Цей сайт: Caddy + Docker + WordPress', 'Web', 'Кастомна тема, авто-SSL, кеш і Lighthouse 90+ — зібрано в Docker і в git.', 'Caddy, Docker, WordPress, Vite', 'Lighthouse 90+' ),
		'ru' => array( 'Этот сайт: Caddy + Docker + WordPress', 'Web', 'Кастомная тема, авто-SSL, кеш и Lighthouse 90+ — собран в Docker и в git.', 'Caddy, Docker, WordPress, Vite', 'Lighthouse 90+' ),
	) ),
);

function setf( $id, $name, $val, $key ) { update_post_meta( $id, $name, $val ); update_post_meta( $id, '_' . $name, $key ); }

function apply_fields( $id, $key, $lang, $row, $PH, $FIELDKEYS ) {
	list( $title, $role, $summary, $stack, $metric ) = $row;
	setf( $id, 'role_label', $role, $FIELDKEYS['role_label'] );
	setf( $id, 'summary', $summary, $FIELDKEYS['summary'] );
	setf( $id, 'stack', $stack, $FIELDKEYS['stack'] );
	setf( $id, 'result_metric', $metric, $FIELDKEYS['result_metric'] );
	setf( $id, 'task', $PH[ $lang ]['task'], $FIELDKEYS['task'] );
	setf( $id, 'approach', $PH[ $lang ]['approach'], $FIELDKEYS['approach'] );
	setf( $id, 'result', $PH[ $lang ]['result'], $FIELDKEYS['result'] );
	update_post_meta( $id, 'service_key', $key );
}

foreach ( $DATA as $key => $info ) {
	// найти существующий EN-кейс по slug
	$en = get_page_by_path( $key, OBJECT, 'case' );
	if ( ! $en ) { echo "! нет базового кейса '$key'\n"; continue; }
	$en_id = $en->ID;

	// EN: английский контент + язык
	wp_update_post( array( 'ID' => $en_id, 'post_title' => $DATA[ $key ]['l']['en'][0], 'menu_order' => $info['order'] ) );
	apply_fields( $en_id, $key, 'en', $DATA[ $key ]['l']['en'], $PH, $FIELDKEYS );
	pll_set_post_language( $en_id, 'en' );

	$group = array( 'en' => $en_id );

	foreach ( array( 'uk', 'ru' ) as $lang ) {
		$existing = pll_get_post( $en_id, $lang );
		if ( $existing ) { $group[ $lang ] = $existing; echo "= $key/$lang уже есть (#$existing)\n"; continue; }

		$new_id = wp_insert_post( array(
			'post_type'   => 'case',
			'post_status' => 'publish',
			'post_title'  => $DATA[ $key ]['l'][ $lang ][0],
			'menu_order'  => $info['order'],
		) );
		if ( is_wp_error( $new_id ) ) { echo "! $key/$lang: " . $new_id->get_error_message() . "\n"; continue; }

		pll_set_post_language( $new_id, $lang );
		// чистый slug в нужном языке (Polylang разрешает одинаковые slug в разных языках)
		wp_update_post( array( 'ID' => $new_id, 'post_name' => $key ) );
		apply_fields( $new_id, $key, $lang, $DATA[ $key ]['l'][ $lang ], $PH, $FIELDKEYS );
		$group[ $lang ] = $new_id;
		echo "+ $key/$lang (#$new_id)\n";
	}

	pll_save_post_translations( $group );
}

echo "Готово. Всего кейсов: " . wp_count_posts( 'case' )->publish . "\n";
