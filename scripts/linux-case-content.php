<?php
/** Реальный контент кейса linux (EN/UK/RU). wp eval-file */
$cases = array( 'en' => 6, 'uk' => 15, 'ru' => 16 );
$REPO = 'https://github.com/vasutenko26/portfolio';

$C = array();
$C['en'] = array(
  'summary' => 'Production server hardened from scratch: SSH key-only, ufw, fail2ban, swap, least-privilege. Backups verified by restore, not trusted on faith. I fix the cause, not the symptom.',
  'result_metric' => 'SSL Labs A+ · restore verified',
  'stack' => 'Debian, ufw, fail2ban, systemd, Docker, Caddy',
  'task' => '<p>A public server running a real business needs to be locked down and recoverable — not «probably fine». Harden the box, prove the backups actually restore, and be ready to diagnose and fix performance incidents at the root, with as little downtime as possible.</p>',
  'approach' => '<p><strong>Hardening (from scratch):</strong> SSH key-only (no passwords, root by key only), ufw (default-deny, only 22/80/443), fail2ban on SSH, 2&nbsp;GB swap, least-privilege (sudo-with-password, a deploy user locked to a single forced command). Caddy gives auto-SSL + security headers; secrets stay in <code>.env</code>, out of git.</p><p><strong>Backups that are verified:</strong> a daily job dumps MariaDB + n8n Postgres + WP uploads + configs with rotation — and a weekly job <strong>restores them into throwaway containers and checks the data</strong>, so a backup only counts once it has been restored.</p><p><strong>Fix the cause, not the symptom:</strong> in a sandbox I reproduce a starved PHP-FPM pool, diagnose it under load and tune the pool; plus a zero-downtime blue→green migration where traffic only moves after the new instance is healthy.</p>',
  'result' => '<p><strong>SSL Labs A+</strong>, security headers validated externally (Mozilla Observatory). The restore test passes — real data (posts, workflows) reloaded into clean containers, not just a tarball that exists. PHP-FPM tuning cut latency under load <strong>~4×</strong>; the migration switched 200 in-flight requests blue→green with <strong>0 dropped</strong>. Hardening configs and backup scripts are in the repo.</p>',
);
$C['ru'] = array(
  'summary' => 'Прод-сервер защищён с нуля: SSH только по ключу, ufw, fail2ban, swap, least-privilege. Бэкапы проверяются восстановлением, а не на веру. Чиню причину, не симптом.',
  'result_metric' => 'SSL Labs A+ · restore проверен',
  'stack' => 'Debian, ufw, fail2ban, systemd, Docker, Caddy',
  'task' => '<p>Публичный сервер с реальным бизнесом нужно закрыть и сделать восстановимым — а не «вроде работает». Захарденить машину, доказать, что бэкапы реально восстанавливаются, и быть готовым диагностировать и чинить инциденты производительности по причине, с минимальным простоем.</p>',
  'approach' => '<p><strong>Хардненинг (с нуля):</strong> SSH только по ключу (без паролей, root по ключу), ufw (default-deny, только 22/80/443), fail2ban на SSH, swap 2&nbsp;ГБ, least-privilege (sudo-с-паролем, деплой-юзер заперт на единственную forced-command). Caddy — авто-SSL + security-заголовки; секреты в <code>.env</code>, вне git.</p><p><strong>Бэкапы, которые проверяются:</strong> ежедневная задача дампит MariaDB + n8n Postgres + WP uploads + конфиги с ротацией, а еженедельная <strong>восстанавливает их в одноразовые контейнеры и проверяет данные</strong> — бэкап считается рабочим только после восстановления.</p><p><strong>Чиню причину, не симптом:</strong> в sandbox воспроизвожу забитый пул PHP-FPM, диагностирую под нагрузкой и тюню пул; плюс zero-downtime миграция blue→green, где трафик переключается только после health-check нового инстанса.</p>',
  'result' => '<p><strong>SSL Labs A+</strong>, security-заголовки подтверждены внешне (Mozilla Observatory). Тест-restore проходит — реальные данные (посты, воркфлоу) восстановлены в чистые контейнеры, а не просто «архив существует». Тюнинг PHP-FPM срезал латентность под нагрузкой <strong>~в 4 раза</strong>; миграция переключила 200 запросов на лету blue→green с <strong>0 потерь</strong>. Конфиги хардненинга и скрипты бэкапа — в репозитории.</p>',
);
$C['uk'] = array(
  'summary' => 'Прод-сервер захищений з нуля: SSH лише по ключу, ufw, fail2ban, swap, least-privilege. Бекапи перевіряються відновленням, а не на віру. Лагоджу причину, не симптом.',
  'result_metric' => 'SSL Labs A+ · restore перевірено',
  'stack' => 'Debian, ufw, fail2ban, systemd, Docker, Caddy',
  'task' => '<p>Публічний сервер із реальним бізнесом треба закрити й зробити відновлюваним — а не «начебто працює». Захарденити машину, довести, що бекапи реально відновлюються, і бути готовим діагностувати та лагодити інциденти продуктивності за причиною, з мінімальним простоєм.</p>',
  'approach' => '<p><strong>Хардненінг (з нуля):</strong> SSH лише по ключу (без паролів, root по ключу), ufw (default-deny, лише 22/80/443), fail2ban на SSH, swap 2&nbsp;ГБ, least-privilege (sudo-з-паролем, деплой-юзер замкнено на єдину forced-command). Caddy — авто-SSL + security-заголовки; секрети в <code>.env</code>, поза git.</p><p><strong>Бекапи, що перевіряються:</strong> щоденна задача дампить MariaDB + n8n Postgres + WP uploads + конфіги з ротацією, а щотижнева <strong>відновлює їх в одноразові контейнери й перевіряє дані</strong> — бекап вважається робочим лише після відновлення.</p><p><strong>Лагоджу причину, не симптом:</strong> у sandbox відтворюю забитий пул PHP-FPM, діагностую під навантаженням і тюню пул; плюс zero-downtime міграція blue→green, де трафік перемикається лише після health-check нового інстансу.</p>',
  'result' => '<p><strong>SSL Labs A+</strong>, security-заголовки підтверджені зовні (Mozilla Observatory). Тест-restore проходить — реальні дані (пости, воркфлоу) відновлені в чисті контейнери, а не просто «архів існує». Тюнінг PHP-FPM зрізав латентність під навантаженням <strong>~у 4 рази</strong>; міграція перемкнула 200 запитів на льоту blue→green з <strong>0 втрат</strong>. Конфіги хардненінгу та скрипти бекапу — в репозиторії.</p>',
);

$keys = array( 'summary' => 'f_sum', 'result_metric' => 'f_metric', 'stack' => 'f_stack', 'task' => 'f_task', 'approach' => 'f_appr', 'result' => 'f_res' );
foreach ( $cases as $lang => $id ) {
  foreach ( $C[ $lang ] as $field => $val ) {
    update_post_meta( $id, $field, $val );
    update_post_meta( $id, '_' . $field, $keys[ $field ] );
  }
  update_post_meta( $id, 'repo_url', $REPO );
  update_post_meta( $id, '_repo_url', 'f_repo' );
  echo "обновлён кейс linux/$lang (#$id)\n";
}
