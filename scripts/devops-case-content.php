<?php
/** Реальный контент кейса devops (EN/UK/RU). wp eval-file */
$cases = array( 'en' => 7, 'uk' => 17, 'ru' => 18 );
$WF = 'https://github.com/vasutenko26/portfolio/blob/main/.github/workflows/deploy.yml';
$REPO = 'https://github.com/vasutenko26/portfolio';

$C = array();
$C['en'] = array(
  'summary' => 'Push to main → GitHub Actions lints, tests, builds the image, pushes to GHCR and auto-deploys to this server over SSH. Prometheus + Grafana watch host & app; Telegram alert on failure.',
  'result_metric' => 'push → live in ~2 min',
  'stack' => 'GitHub Actions, Docker, GHCR, Prometheus, Grafana',
  'task' => '<p>Manual deploys are where half the incidents come from — a missed step, the wrong tag, a forgotten restart. The goal: remove the manual step entirely. Every push to <code>main</code> should test itself, build, and ship to production on its own — and monitoring should catch problems before a client does.</p>',
  'approach' => '<p>A small Node service exposes <code>/health</code> and <code>/metrics</code> (Prometheus). On every push to <code>main</code>, <strong>GitHub Actions</strong> runs lint + tests, builds a Docker image, pushes it to <strong>GHCR</strong>, then deploys over SSH. The deploy key is locked to a <strong>forced command</strong> — it can only redeploy the app, nothing else; host/user/key live in GitHub Secrets.</p><p>On the box, <strong>Prometheus</strong> scrapes the host (node_exporter) and the app; <strong>Grafana</strong> shows load, health and latency on a public read-only dashboard and fires a <strong>Telegram</strong> alert when the service drops.</p>',
  'result' => '<p>A push goes from commit to a new version live on the subdomain in <strong>~2 minutes</strong>, with no manual step — the deployed build reports its own commit SHA. If the app falls over, Grafana pings Telegram before anyone refreshes the page. Pipeline and monitoring config live in the repo: <a href="' . $WF . '">.github/workflows/deploy.yml</a>.</p>',
);
$C['uk'] = array(
  'summary' => 'Push у main → GitHub Actions лінтить, тестить, збирає образ, пушить у GHCR і сам деплоїть на цей сервер по SSH. Prometheus + Grafana стежать за хостом і застосунком; при падінні — алерт у Telegram.',
  'result_metric' => 'push → прод за ~2 хв',
  'stack' => 'GitHub Actions, Docker, GHCR, Prometheus, Grafana',
  'task' => '<p>Ручні деплої — джерело половини інцидентів: пропущений крок, не той тег, забутий рестарт. Мета — прибрати ручний крок повністю. Кожен push у <code>main</code> має сам себе протестувати, зібрати й викотити в прод, а моніторинг — ловити проблему раніше за клієнта.</p>',
  'approach' => '<p>Невеликий Node-сервіс віддає <code>/health</code> і <code>/metrics</code> (Prometheus). На кожен push у <code>main</code> <strong>GitHub Actions</strong> ганяє lint + тести, збирає Docker-образ, пушить у <strong>GHCR</strong>, потім деплоїть по SSH. Деплой-ключ замкнено <strong>forced-command</strong> — ним можна лише передеплоїти app і нічого більше; хост/юзер/ключ — у GitHub Secrets.</p><p>На сервері <strong>Prometheus</strong> скрейпить хост (node_exporter) і застосунок; <strong>Grafana</strong> показує навантаження, здоровʼя та латентність на публічному read-only дашборді й шле <strong>алерт у Telegram</strong> при падінні сервісу.</p>',
  'result' => '<p>Push доїжджає від коміту до нової версії на піддомені за <strong>~2 хвилини</strong> без ручного кроку — задеплоєна збірка повідомляє свій commit SHA. Якщо застосунок впаде, Grafana смикне Telegram раніше, ніж хтось оновить сторінку. Конфіг пайплайна й моніторингу — у репозиторії: <a href="' . $WF . '">.github/workflows/deploy.yml</a>.</p>',
);
$C['ru'] = array(
  'summary' => 'Push в main → GitHub Actions линтит, тестит, собирает образ, пушит в GHCR и сам деплоит на этот сервер по SSH. Prometheus + Grafana следят за хостом и приложением; при падении — алерт в Telegram.',
  'result_metric' => 'push → прод за ~2 мин',
  'stack' => 'GitHub Actions, Docker, GHCR, Prometheus, Grafana',
  'task' => '<p>Ручные деплои — источник половины инцидентов: пропущенный шаг, не тот тег, забытый рестарт. Цель — убрать ручной шаг полностью. Каждый push в <code>main</code> должен сам себя протестировать, собрать и выкатить в прод, а мониторинг — ловить проблему раньше клиента.</p>',
  'approach' => '<p>Небольшой Node-сервис отдаёт <code>/health</code> и <code>/metrics</code> (Prometheus). На каждый push в <code>main</code> <strong>GitHub Actions</strong> гоняет lint + тесты, собирает Docker-образ, пушит в <strong>GHCR</strong>, затем деплоит по SSH. Деплой-ключ заперт <strong>forced-command</strong> — им можно только передеплоить app и ничего больше; хост/юзер/ключ — в GitHub Secrets.</p><p>На сервере <strong>Prometheus</strong> скрейпит хост (node_exporter) и приложение; <strong>Grafana</strong> показывает нагрузку, здоровье и латентность на публичном read-only дашборде и шлёт <strong>алерт в Telegram</strong> при падении сервиса.</p>',
  'result' => '<p>Push доезжает от коммита до новой версии на поддомене за <strong>~2 минуты</strong> без ручного шага — задеплоенная сборка сообщает свой commit SHA. Если приложение упадёт, Grafana дёрнет Telegram раньше, чем кто-то обновит страницу. Конфиг пайплайна и мониторинга — в репозитории: <a href="' . $WF . '">.github/workflows/deploy.yml</a>.</p>',
);

$keys = array( 'summary' => 'f_sum', 'result_metric' => 'f_metric', 'stack' => 'f_stack', 'task' => 'f_task', 'approach' => 'f_appr', 'result' => 'f_res' );
foreach ( $cases as $lang => $id ) {
  foreach ( $C[ $lang ] as $field => $val ) {
    update_post_meta( $id, $field, $val );
    update_post_meta( $id, '_' . $field, $keys[ $field ] );
  }
  update_post_meta( $id, 'repo_url', $REPO );
  update_post_meta( $id, '_repo_url', 'f_repo' );
  echo "обновлён кейс devops/$lang (#$id)\n";
}
