<?php
/**
 * Создаёт/обновляет 3 новых трёхъязычных кейса: status-page, observability, rag.
 * Идемпотентно. Запуск: wp eval-file scripts/new-cases-content.php
 */

$REPO = 'https://github.com/vasutenko26/portfolio';
$LANGS = array( 'en', 'uk', 'ru' );
$KEYS = array(
  'summary' => 'f_sum', 'result_metric' => 'f_metric', 'stack' => 'f_stack',
  'task' => 'f_task', 'approach' => 'f_appr', 'result' => 'f_res',
);

$CASES = array();

/* ----------------------------- status-page ----------------------------- */
$CASES['status'] = array(
  'menu_order' => 7,
  'repo' => $REPO . '/tree/main/status-page',
  'role' => array( 'en' => 'Monitoring', 'uk' => 'Моніторинг', 'ru' => 'Мониторинг' ),
  'title' => array(
    'en' => 'Public status page & uptime monitoring',
    'uk' => 'Публічна status-page та моніторинг аптайму',
    'ru' => 'Публичная status-page и мониторинг аптайма',
  ),
  'slug' => array( 'en' => 'status', 'uk' => 'status-uk', 'ru' => 'status-ru' ),
  'content' => array(
    'en' => array(
      'summary' => 'A public status page for every self-hosted service — HTTP + TLS-expiry checks, incident history and 24h/7d/30d uptime, with down/up alerts to Telegram. Provisioned from code, exposed via Caddy/TLS.',
      'result_metric' => '6 services green · live',
      'stack' => 'Uptime Kuma, Docker, Caddy, Telegram',
      'task' => "<p>The site promises a green dashboard and high uptime. That claim should be a live link a client can open — not a screenshot. The goal: a public status page for every self-hosted service, with honest incident history, and an alert in Telegram the moment something breaks.</p>",
      'approach' => "<p>I run <strong>Uptime Kuma</strong> in Docker, reachable only through Caddy with TLS on the <code>status.</code> subdomain — no host ports. Monitors hit the <strong>public HTTPS URLs</strong> of every service (site, n8n, Grafana, the RAG assistant, the status page itself), so a green board proves the whole path — DNS → certificate → proxy → app — plus <strong>TLS-expiry</strong> tracking.</p><p>The whole setup — Telegram notification, monitors, the public page — is provisioned <strong>from code</strong> (an idempotent script over Kuma&rsquo;s API), not clicked together in a UI. Down and up alerts go to the same Telegram bot the rest of the infrastructure uses.</p>",
      'result' => "<p>A public page at <a href='https://status.davidvasutenko.fun' target='_blank' rel='noopener'>status.davidvasutenko.fun</a> with per-service uptime over 24h/7d/30d and an incident timeline. I verified the alert path with a real drill: killing a test service delivered a Down message to Telegram and opened an incident; recovery sent an Up. Reproducible from one <code>docker compose up</code>.</p>",
    ),
    'uk' => array(
      'summary' => 'Публічна status-page для кожного self-hosted сервісу — HTTP + перевірка строку TLS, історія інцидентів і аптайм за 24г/7д/30д, алерти down/up у Telegram. Налаштовано кодом, назовні через Caddy/TLS.',
      'result_metric' => '6 сервісів green · live',
      'stack' => 'Uptime Kuma, Docker, Caddy, Telegram',
      'task' => "<p>Сайт обіцяє «зелений дашборд» і високий аптайм. Ця обіцянка має бути живим посиланням, яке клієнт відкриє, а не скріншотом. Мета — публічна status-page для кожного self-hosted сервісу, з чесною історією інцидентів і алертом у Telegram у мить, коли щось падає.</p>",
      'approach' => "<p><strong>Uptime Kuma</strong> у Docker, доступна лише через Caddy з TLS на піддомені <code>status.</code> — без портів на хост. Монітори стукають у <strong>публічні HTTPS-URL</strong> кожного сервісу (сайт, n8n, Grafana, RAG-асистент, сама сторінка), тож зелене табло доводить увесь шлях — DNS → сертифікат → проксі → застосунок — плюс контроль <strong>строку TLS</strong>.</p><p>Уся конфігурація — нотифікація в Telegram, монітори, публічна сторінка — піднімається <strong>з коду</strong> (ідемпотентний скрипт через API Kuma), а не кліками в UI. Алерти down/up ідуть у той самий Telegram-бот, що й решта інфраструктури.</p>",
      'result' => "<p>Публічна сторінка <a href='https://status.davidvasutenko.fun' target='_blank' rel='noopener'>status.davidvasutenko.fun</a> з аптаймом по сервісах за 24г/7д/30д і таймлайном інцидентів. Шлях алерту перевірено реальним навчанням: гасіння тестового сервісу надіслало Down у Telegram і відкрило інцидент; відновлення — Up. Відтворюється однією командою <code>docker compose up</code>.</p>",
    ),
    'ru' => array(
      'summary' => 'Публичная status-page для каждого self-hosted сервиса — HTTP + проверка срока TLS, история инцидентов и аптайм за 24ч/7д/30д, алерты down/up в Telegram. Настроено кодом, наружу через Caddy/TLS.',
      'result_metric' => '6 сервисов green · live',
      'stack' => 'Uptime Kuma, Docker, Caddy, Telegram',
      'task' => "<p>Сайт обещает «зелёный дашборд» и высокий аптайм. Это обещание должно быть живой ссылкой, которую клиент откроет, а не скриншотом. Цель — публичная status-page для каждого self-hosted сервиса, с честной историей инцидентов и алертом в Telegram в момент, когда что-то падает.</p>",
      'approach' => "<p><strong>Uptime Kuma</strong> в Docker, доступна только через Caddy с TLS на поддомене <code>status.</code> — без портов на хост. Мониторы бьют в <strong>публичные HTTPS-URL</strong> каждого сервиса (сайт, n8n, Grafana, RAG-ассистент, сама страница), поэтому зелёное табло доказывает весь путь — DNS → сертификат → прокси → приложение — плюс контроль <strong>срока TLS</strong>.</p><p>Вся конфигурация — уведомление в Telegram, мониторы, публичная страница — поднимается <strong>из кода</strong> (идемпотентный скрипт через API Kuma), а не кликами в UI. Алерты down/up идут в тот же Telegram-бот, что и остальная инфраструктура.</p>",
      'result' => "<p>Публичная страница <a href='https://status.davidvasutenko.fun' target='_blank' rel='noopener'>status.davidvasutenko.fun</a> с аптаймом по сервисам за 24ч/7д/30д и таймлайном инцидентов. Путь алерта проверен реальным учением: гашение тестового сервиса доставило Down в Telegram и открыло инцидент; восстановление — Up. Воспроизводится одной командой <code>docker compose up</code>.</p>",
    ),
  ),
);

/* ---------------------------- observability ---------------------------- */
$CASES['observability'] = array(
  'menu_order' => 8,
  'repo' => $REPO . '/tree/main/observability',
  'role' => array( 'en' => 'Observability', 'uk' => 'Observability', 'ru' => 'Observability' ),
  'title' => array(
    'en' => 'Observability stack: Prometheus + Grafana',
    'uk' => 'Observability-стек: Prometheus + Grafana',
    'ru' => 'Observability-стек: Prometheus + Grafana',
  ),
  'slug' => array( 'en' => 'observability', 'uk' => 'observability-uk', 'ru' => 'observability-ru' ),
  'content' => array(
    'en' => array(
      'summary' => 'Prometheus + Grafana + Alertmanager + blackbox, all configured as code. Three provisioned dashboards (host, containers, endpoints), alerts to Telegram, Grafana behind a login over TLS.',
      'result_metric' => '3 dashboards · alert → Telegram in ~90s',
      'stack' => 'Prometheus, Grafana, Alertmanager, blackbox, Docker',
      'task' => "<p>Monitoring was buried inside the DevOps case — a couple of panels, easy to miss. It deserved its own, visual case: a real observability stack where the dashboards sell the service on sight, everything configured as code, and alerts that page me in Telegram before a client notices.</p>",
      'approach' => "<p><strong>Prometheus</strong> scrapes three layers — the host (node_exporter), every container, and external endpoints (<strong>blackbox</strong>: HTTP + TLS-expiry). <strong>Grafana</strong> ships three dashboards <strong>provisioned from JSON</strong> in the repo — Host overview, Containers, Endpoints/Uptime — so <code>docker compose up</code> yields a populated Grafana with nothing to click. <strong>Alertmanager</strong> routes alerts (high CPU/mem/disk, container down, endpoint down, TLS expiring) to Telegram.</p><p>Grafana is exposed via Caddy/TLS behind a <strong>login</strong>; internal components publish no host ports. This host runs Docker&rsquo;s containerd image store, where cAdvisor cannot name containers — so I wrote a small Docker-API exporter that reports per-container metrics with real names.</p>",
      'result' => "<p>A login-protected Grafana at <a href='https://grafana.davidvasutenko.fun' target='_blank' rel='noopener'>grafana.davidvasutenko.fun</a> with three live dashboards: 11 scrape targets up, host + 16 containers by name + 5 endpoints with TLS days-left. Alerting verified end-to-end — stopping a container delivered a ContainerDown alert to Telegram within ~90s and resolved on restart. Zero click-ops.</p>",
    ),
    'uk' => array(
      'summary' => 'Prometheus + Grafana + Alertmanager + blackbox, усе налаштовано кодом. Три готових дашборди (хост, контейнери, ендпоінти), алерти в Telegram, Grafana під логіном по TLS.',
      'result_metric' => '3 дашборди · алерт → Telegram за ~90с',
      'stack' => 'Prometheus, Grafana, Alertmanager, blackbox, Docker',
      'task' => "<p>Моніторинг був розчинений усередині DevOps-кейсу — кілька панелей, легко пропустити. Він заслуговував на власний візуальний кейс: справжній observability-стек, де дашборди продають послугу з першого погляду, усе як код, а алерти смикають мене в Telegram раніше за клієнта.</p>",
      'approach' => "<p><strong>Prometheus</strong> скрейпить три шари — хост (node_exporter), кожен контейнер і зовнішні ендпоінти (<strong>blackbox</strong>: HTTP + строк TLS). <strong>Grafana</strong> везе три дашборди, <strong>задані JSON</strong> у репозиторії — Host overview, Containers, Endpoints/Uptime — тож <code>docker compose up</code> дає наповнену Grafana без жодного кліку. <strong>Alertmanager</strong> роутить алерти (CPU/RAM/диск, контейнер впав, ендпоінт впав, TLS спливає) у Telegram.</p><p>Grafana назовні через Caddy/TLS і під <strong>логіном</strong>; внутрішні компоненти не світять портів на хост. Цей хост працює на containerd image store, де cAdvisor не вміє іменувати контейнери — тож я написав маленький Docker-API експортер, що віддає метрики контейнерів зі справжніми іменами.</p>",
      'result' => "<p>Grafana під логіном на <a href='https://grafana.davidvasutenko.fun' target='_blank' rel='noopener'>grafana.davidvasutenko.fun</a> з трьома живими дашбордами: 11 таргетів up, хост + 16 контейнерів за іменами + 5 ендпоінтів зі строком TLS. Алертинг перевірено наскрізь — зупинка контейнера надіслала ContainerDown у Telegram за ~90с і зарезолвилась після старту. Жодного ручного кліку.</p>",
    ),
    'ru' => array(
      'summary' => 'Prometheus + Grafana + Alertmanager + blackbox, всё настроено кодом. Три готовых дашборда (хост, контейнеры, эндпоинты), алерты в Telegram, Grafana под логином по TLS.',
      'result_metric' => '3 дашборда · алерт → Telegram за ~90с',
      'stack' => 'Prometheus, Grafana, Alertmanager, blackbox, Docker',
      'task' => "<p>Мониторинг был растворён внутри DevOps-кейса — пара панелей, легко пропустить. Он заслуживал собственного визуального кейса: настоящий observability-стек, где дашборды продают услугу с первого взгляда, всё как код, а алерты дёргают меня в Telegram раньше клиента.</p>",
      'approach' => "<p><strong>Prometheus</strong> скрейпит три слоя — хост (node_exporter), каждый контейнер и внешние эндпоинты (<strong>blackbox</strong>: HTTP + срок TLS). <strong>Grafana</strong> везёт три дашборда, <strong>заданных JSON</strong> в репозитории — Host overview, Containers, Endpoints/Uptime — поэтому <code>docker compose up</code> даёт наполненную Grafana без единого клика. <strong>Alertmanager</strong> роутит алерты (CPU/RAM/диск, контейнер упал, эндпоинт упал, TLS истекает) в Telegram.</p><p>Grafana наружу через Caddy/TLS и под <strong>логином</strong>; внутренние компоненты не светят портов на хост. Этот хост работает на containerd image store, где cAdvisor не умеет именовать контейнеры — поэтому я написал маленький Docker-API экспортер, отдающий метрики контейнеров с настоящими именами.</p>",
      'result' => "<p>Grafana под логином на <a href='https://grafana.davidvasutenko.fun' target='_blank' rel='noopener'>grafana.davidvasutenko.fun</a> с тремя живыми дашбордами: 11 таргетов up, хост + 16 контейнеров по именам + 5 эндпоинтов со сроком TLS. Алертинг проверен насквозь — остановка контейнера доставила ContainerDown в Telegram за ~90с и зарезолвилась после старта. Ноль ручных кликов.</p>",
    ),
  ),
);

/* -------------------------------- rag --------------------------------- */
$CASES['rag'] = array(
  'menu_order' => 9,
  'repo' => $REPO . '/tree/main/rag-assistant',
  'role' => array( 'en' => 'AI assistant', 'uk' => 'AI-асистент', 'ru' => 'AI-ассистент' ),
  'title' => array(
    'en' => 'RAG assistant: chat with your documents',
    'uk' => 'RAG-асистент: чат з документами',
    'ru' => 'RAG-ассистент: чат с документами',
  ),
  'slug' => array( 'en' => 'rag', 'uk' => 'rag-uk', 'ru' => 'rag-ru' ),
  'content' => array(
    'en' => array(
      'summary' => 'Upload PDFs → ask → get an answer with citations to the source document and page. Embeddings run locally; the LLM is pluggable (Ollama = fully on-prem). Out-of-corpus questions are refused, not hallucinated.',
      'result_metric' => 'answers cite the source · embeddings 100% local',
      'stack' => 'FastAPI, Qdrant, sentence-transformers, Docker',
      'task' => "<p>Businesses and factories sit on internal documents — equipment manuals, policies, contracts — that nobody wants to paste into a public chatbot. The brief: a self-hosted &laquo;chat with your documents&raquo; assistant. Upload PDFs, ask in plain language, get an answer that links back to the source — and keep the data on the client&rsquo;s own server.</p>",
      'approach' => "<p>A <strong>FastAPI</strong> backend runs the full <strong>RAG</strong> pipeline: ingest → chunk with overlap → embed → store in <strong>Qdrant</strong> with per-chunk metadata (filename, page) → retrieve top-k → grounded answer with mandatory <code>[n]</code> citations. Embeddings are <strong>self-hosted</strong> (sentence-transformers) — indexing text never leaves the box. The generation LLM is pluggable via env (Gemini / OpenAI / <strong>Ollama</strong> for fully on-prem).</p><p>A clean web chat shows answers with clickable citations that expand to the exact source fragment. If the answer is not in the documents, it says so instead of inventing — and dependency failures surface as clear errors, never a silent crash.</p>",
      'result' => "<p>Live at <a href='https://rag.davidvasutenko.fun' target='_blank' rel='noopener'>rag.davidvasutenko.fun</a>. Tested with two PDFs: &laquo;max operating pressure of the X200 boiler?&raquo; → &laquo;6 bar&raquo; citing <code>manual.pdf — p.2</code>; an out-of-corpus question (&laquo;capital of France?&raquo;) is refused with a not-found message rather than answered from world knowledge. With <code>LLM_PROVIDER=ollama</code> the deployment makes no external calls at all.</p>",
    ),
    'uk' => array(
      'summary' => 'Завантажуєш PDF → питаєш → отримуєш відповідь із посиланнями на документ і сторінку. Ембединги локальні; LLM змінна (Ollama = повністю on-prem). На питання поза документами — чесне «не знайшов», без вигадок.',
      'result_metric' => 'відповіді з посиланням на джерело · ембединги локально',
      'stack' => 'FastAPI, Qdrant, sentence-transformers, Docker',
      'task' => "<p>Бізнес і заводи сидять на внутрішніх документах — мануали обладнання, політики, договори — які ніхто не хоче вставляти в публічний чатбот. Завдання: self-hosted асистент «чат з документами». Завантажуєш PDF, питаєш звичайною мовою, отримуєш відповідь із посиланням на джерело — і дані лишаються на сервері клієнта.</p>",
      'approach' => "<p>Бекенд на <strong>FastAPI</strong> крутить повний <strong>RAG</strong>-пайплайн: інжест → чанкінг з overlap → ембединг → запис у <strong>Qdrant</strong> з метаданими (імʼя файлу, сторінка) → пошук top-k → відповідь строго за контекстом з обовʼязковими цитатами <code>[n]</code>. Ембединги <strong>self-hosted</strong> (sentence-transformers) — текст для індексації не покидає сервер. LLM генерації змінна через env (Gemini / OpenAI / <strong>Ollama</strong> для повного on-prem).</p><p>Чистий веб-чат показує відповіді з клікабельними цитатами, що розкривають точний фрагмент-джерело. Якщо відповіді в документах немає — так і каже, а не вигадує; збої залежностей віддаються зрозумілою помилкою, не мовчазним падінням.</p>",
      'result' => "<p>Працює на <a href='https://rag.davidvasutenko.fun' target='_blank' rel='noopener'>rag.davidvasutenko.fun</a>. Перевірено на двох PDF: «макс. робочий тиск котла X200?» → «6 бар» з посиланням на <code>manual.pdf — p.2</code>; питання поза корпусом («столиця Франції?») відхиляється повідомленням «не знайшов», а не відповіддю зі світових знань. З <code>LLM_PROVIDER=ollama</code> деплой не робить жодних зовнішніх викликів.</p>",
    ),
    'ru' => array(
      'summary' => 'Загружаешь PDF → спрашиваешь → получаешь ответ со ссылками на документ и страницу. Эмбеддинги локальные; LLM сменная (Ollama = полностью on-prem). На вопрос вне документов — честное «не нашёл», без выдумок.',
      'result_metric' => 'ответы со ссылкой на источник · эмбеддинги локально',
      'stack' => 'FastAPI, Qdrant, sentence-transformers, Docker',
      'task' => "<p>Бизнес и заводы сидят на внутренних документах — мануалы оборудования, политики, договоры — которые никто не хочет вставлять в публичный чат-бот. Задача: self-hosted ассистент «чат с документами». Загружаешь PDF, спрашиваешь обычным языком, получаешь ответ со ссылкой на источник — и данные остаются на сервере клиента.</p>",
      'approach' => "<p>Бэкенд на <strong>FastAPI</strong> крутит полный <strong>RAG</strong>-пайплайн: инжест → чанкинг с overlap → эмбеддинг → запись в <strong>Qdrant</strong> с метаданными (имя файла, страница) → поиск top-k → ответ строго по контексту с обязательными цитатами <code>[n]</code>. Эмбеддинги <strong>self-hosted</strong> (sentence-transformers) — текст для индексации не покидает сервер. LLM генерации сменная через env (Gemini / OpenAI / <strong>Ollama</strong> для полного on-prem).</p><p>Чистый веб-чат показывает ответы с кликабельными цитатами, раскрывающими точный фрагмент-источник. Если ответа в документах нет — так и говорит, а не выдумывает; сбои зависимостей отдаются внятной ошибкой, не молчаливым падением.</p>",
      'result' => "<p>Работает на <a href='https://rag.davidvasutenko.fun' target='_blank' rel='noopener'>rag.davidvasutenko.fun</a>. Проверено на двух PDF: «макс. рабочее давление котла X200?» → «6 бар» со ссылкой на <code>manual.pdf — p.2</code>; вопрос вне корпуса («столица Франции?») отклоняется сообщением «не нашёл», а не ответом из мировых знаний. С <code>LLM_PROVIDER=ollama</code> деплой не делает никаких внешних вызовов.</p>",
    ),
  ),
);

/* ------------------------------- запись -------------------------------- */
foreach ( $CASES as $key => $c ) {
  $ids = array();
  foreach ( $LANGS as $l ) {
    $slug = $c['slug'][ $l ];
    $ex = get_page_by_path( $slug, OBJECT, 'case' );
    if ( $ex ) {
      $id = $ex->ID;
      wp_update_post( array( 'ID' => $id, 'post_title' => $c['title'][ $l ], 'menu_order' => $c['menu_order'], 'post_status' => 'publish' ) );
    } else {
      $id = wp_insert_post( array(
        'post_type' => 'case', 'post_status' => 'publish',
        'post_title' => $c['title'][ $l ], 'post_name' => $slug, 'menu_order' => $c['menu_order'],
      ) );
    }
    if ( function_exists( 'pll_set_post_language' ) ) pll_set_post_language( $id, $l );

    update_post_meta( $id, 'service_key', $key );
    update_post_meta( $id, 'role_label', $c['role'][ $l ] );
    update_post_meta( $id, '_role_label', 'f_role' );
    foreach ( $c['content'][ $l ] as $field => $val ) {
      update_post_meta( $id, $field, $val );
      update_post_meta( $id, '_' . $field, $KEYS[ $field ] );
    }
    update_post_meta( $id, 'repo_url', $c['repo'] );
    update_post_meta( $id, '_repo_url', 'f_repo' );

    $ids[ $l ] = $id;
    echo "кейс $key/$l (#$id) — ok\n";
  }
  if ( function_exists( 'pll_save_post_translations' ) ) pll_save_post_translations( $ids );
  echo "  переводы связаны: " . json_encode( $ids ) . "\n";
}
echo "Готово.\n";
