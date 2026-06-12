<?php
/** Реальный контент кейса automation (EN/UK/RU). wp eval-file */
$cases = array( 'en' => 8, 'uk' => 19, 'ru' => 20 );

$C = array();

$C['en'] = array(
  'summary' => 'Self-hosted n8n on my own server: 3 error-handled workflows — site form → Telegram in ~2s, daily health report, AI triage. No subscription, full data control.',
  'result_metric' => '~2s form → Telegram',
  'stack' => 'n8n, Docker, Postgres, Caddy, Gemini',
  'task' => '<p>This portfolio needs to turn visitors into conversations without paying for a SaaS form service or handing leads to a third party — and without anything failing silently. Capture form submissions, deliver them to Telegram instantly, keep a durable log, and add an unattended daily health report. All on infrastructure I control.</p>',
  'approach' => '<p>Self-hosted <strong>n8n + Postgres</strong> in Docker behind Caddy (auto-SSL). Only the webhook endpoint is public; the editor sits behind HTTP auth. Three workflows, each with error handling:</p><ul><li><strong>Contact form → Telegram + log:</strong> the site form POSTs to an n8n webhook → honeypot + per-IP rate limit → durable CSV log → Telegram message.</li><li><strong>Daily health report:</strong> a cron pings the site, measures latency and sends a 09:00 digest.</li><li><strong>AI intake (Gemini):</strong> classifies incoming messages and escalates the urgent ones.</li></ul><p>A shared Error Trigger turns any failed step into a Telegram alert, so nothing fails silently. Secrets live in environment variables, never in the workflow JSON — so the exported workflows are safe to commit.</p>',
  'result' => '<p>Leads reach Telegram in <strong>~2 seconds</strong> and are never lost — every submission is written to the log before the Telegram call. Bots are filtered by the honeypot and rate limit. The daily report runs unattended at 09:00 Kyiv. No monthly fees, full data ownership, and the workflows are exported to this project’s git repository.</p>',
);

$C['uk'] = array(
  'summary' => 'Self-hosted n8n на власному сервері: 3 сценарії з обробкою помилок — форма → Telegram за ~2с, добовий звіт, AI-тріаж. Без абонплати, повний контроль над даними.',
  'result_metric' => '~2с форма → Telegram',
  'stack' => 'n8n, Docker, Postgres, Caddy, Gemini',
  'task' => '<p>Цьому портфоліо потрібно перетворювати відвідувачів на діалоги без оплати SaaS-форми й без передавання заявок третій стороні — і щоб ніщо не падало мовчки. Приймати заявки, миттєво доставляти їх у Telegram, вести надійний лог і додати автоматичний добовий звіт про стан. Усе на інфраструктурі, якою керую сам.</p>',
  'approach' => '<p>Self-hosted <strong>n8n + Postgres</strong> у Docker за Caddy (авто-SSL). Назовні відкритий лише webhook; редактор — за HTTP-автентифікацією. Три сценарії, кожен з обробкою помилок:</p><ul><li><strong>Форма → Telegram + лог:</strong> форма сайту шле POST на webhook n8n → honeypot + рейт-ліміт за IP → надійний CSV-лог → повідомлення в Telegram.</li><li><strong>Добовий звіт:</strong> cron пінгує сайт, міряє затримку і шле зведення о 09:00.</li><li><strong>AI-приймальня (Gemini):</strong> класифікує вхідні повідомлення й ескалює термінові.</li></ul><p>Спільний Error Trigger перетворює будь-який збій на алерт у Telegram, тож ніщо не падає мовчки. Секрети — в env, ніколи в JSON воркфлоу, тому експорт безпечно комітити.</p>',
  'result' => '<p>Заявки долітають у Telegram за <strong>~2 секунди</strong> і не губляться — кожна спершу пишеться в лог, потім іде в Telegram. Боти відсіюються honeypot і рейт-лімітом. Добовий звіт працює сам о 09:00 за Києвом. Без абонплати, дані лишаються на сервері, а воркфлоу експортовані в git-репозиторій проєкту.</p>',
);

$C['ru'] = array(
  'summary' => 'Self-hosted n8n на своём сервере: 3 сценария с обработкой ошибок — форма → Telegram за ~2с, суточный отчёт, AI-триаж. Без абонплаты, полный контроль над данными.',
  'result_metric' => '~2с форма → Telegram',
  'stack' => 'n8n, Docker, Postgres, Caddy, Gemini',
  'task' => '<p>Этому портфолио нужно превращать посетителей в диалоги без оплаты SaaS-формы и без передачи заявок третьей стороне — и чтобы ничто не падало молча. Принимать заявки, мгновенно доставлять их в Telegram, вести надёжный лог и добавить автоматический суточный отчёт о состоянии. Всё на инфраструктуре, которой управляю сам.</p>',
  'approach' => '<p>Self-hosted <strong>n8n + Postgres</strong> в Docker за Caddy (авто-SSL). Наружу открыт только webhook; редактор — за HTTP-аутентификацией. Три сценария, каждый с обработкой ошибок:</p><ul><li><strong>Форма → Telegram + лог:</strong> форма сайта шлёт POST на webhook n8n → honeypot + рейт-лимит по IP → надёжный CSV-лог → сообщение в Telegram.</li><li><strong>Суточный отчёт:</strong> cron пингует сайт, меряет задержку и шлёт сводку в 09:00.</li><li><strong>AI-приёмная (Gemini):</strong> классифицирует входящие и эскалирует срочные.</li></ul><p>Общий Error Trigger превращает любой сбой в алерт в Telegram, поэтому ничто не падает молча. Секреты — в env, никогда в JSON воркфлоу, поэтому экспорт безопасно коммитить.</p>',
  'result' => '<p>Заявки долетают в Telegram за <strong>~2 секунды</strong> и не теряются — каждая сначала пишется в лог, потом идёт в Telegram. Боты отсеиваются honeypot и рейт-лимитом. Суточный отчёт работает сам в 09:00 по Киеву. Без абонплаты, данные остаются на сервере, а воркфлоу экспортированы в git-репозиторий проекта.</p>',
);

$keys = array( 'summary' => 'f_sum', 'result_metric' => 'f_metric', 'stack' => 'f_stack', 'task' => 'f_task', 'approach' => 'f_appr', 'result' => 'f_res' );

foreach ( $cases as $lang => $id ) {
  foreach ( $C[ $lang ] as $field => $val ) {
    update_post_meta( $id, $field, $val );
    update_post_meta( $id, '_' . $field, $keys[ $field ] );
  }
  echo "обновлён кейс automation/$lang (#$id)\n";
}
