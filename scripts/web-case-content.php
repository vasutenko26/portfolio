<?php
/** Реальный контент кейса web (EN/UK/RU). Доказательство = сам этот сайт. wp eval-file */
$cases = array( 'en' => 9, 'uk' => 21, 'ru' => 22 );
$REPO  = 'https://github.com/vasutenko26/portfolio/tree/main/src/theme/davidv';

$C = array();
$C['en'] = array(
  'summary' => 'This very site: a trilingual portfolio on WordPress with a hand-built block theme — no page builder. GSAP/Lenis motion that respects reduced-motion, self-hosted fonts, Polylang EN/UK/RU + hreflang, shipped in Docker behind Caddy with auto-SSL on my own hardened server.',
  'result_metric' => 'Lighthouse 100 / 96 / 100 / 92 · custom theme',
  'stack' => 'WordPress, custom block theme, GSAP, Lenis, Polylang, Docker, Caddy',
  'task' => '<p>The site that sells engineering work has to <em>be</em> the proof. Not a drag-and-drop template that loads three megabytes of someone else\'s framework — a fast, accessible, multilingual site I built and run end to end, so a prospective client sees the standard before reading a word.</p>',
  'approach' => '<p><strong>A custom theme, not a builder:</strong> a hand-written WordPress <strong>block theme</strong> (<code>davidv</code>) — my own templates, blocks and CSS, zero Elementor/Divi bloat. Motion is <strong>GSAP + Lenis</strong> smooth-scroll that fully backs off under <code>prefers-reduced-motion</code>; the live hero status panel is real markup, not a video.</p><p><strong>Built for three languages:</strong> <strong>Polylang</strong> drives EN/UK/RU with correct <code>hreflang</code>, and <strong>self-hosted fonts</strong> ship a Cyrillic fallback so UK/RU never flash a wrong glyph or pull from a third party.</p><p><strong>Same hands run the box:</strong> the site is in <strong>Docker behind Caddy</strong> (automatic Let\'s Encrypt SSL, security headers) on the same self-managed, hardened server as everything else in this portfolio — design, build, deploy and operations in one pair of hands.</p>',
  'result' => '<p><strong>Lighthouse (desktop): Performance 100, Accessibility 96, Best Practices 100, SEO 92</strong> — FCP/LCP ~0.4&nbsp;s, CLS 0.02. Keyboard focus, reduced-motion and the responsive layout all hold up. The whole thing — theme, three languages, container stack and the server under it — is <strong>one engagement, not a website agency plus a separate DevOps contractor</strong>. The theme source is in the repo.</p>',
);
$C['ru'] = array(
  'summary' => 'Этот самый сайт: трёхъязычное портфолио на WordPress с написанной вручную блочной темой — без конструктора. Анимации GSAP/Lenis с уважением к reduced-motion, self-hosted шрифты, Polylang EN/UK/RU + hreflang, в Docker за Caddy с авто-SSL на своём захардненном сервере.',
  'result_metric' => 'Lighthouse 100 / 96 / 100 / 92 · кастомная тема',
  'stack' => 'WordPress, кастомная блочная тема, GSAP, Lenis, Polylang, Docker, Caddy',
  'task' => '<p>Сайт, который продаёт инженерную работу, должен <em>быть</em> доказательством. Не шаблон с конструктора, тянущий три мегабайта чужого фреймворка, — а быстрый, доступный, многоязычный сайт, который я собрал и обслуживаю сам, чтобы клиент увидел уровень ещё до первого слова.</p>',
  'approach' => '<p><strong>Кастомная тема, а не конструктор:</strong> написанная вручную <strong>блочная тема</strong> WordPress (<code>davidv</code>) — свои шаблоны, блоки и CSS, без балласта Elementor/Divi. Анимации — <strong>GSAP + Lenis</strong> (плавный скролл), полностью отключаются при <code>prefers-reduced-motion</code>; живая status-панель в герое — настоящая вёрстка, а не видео.</p><p><strong>Сделано под три языка:</strong> <strong>Polylang</strong> ведёт EN/UK/RU с корректным <code>hreflang</code>, а <strong>self-hosted шрифты</strong> идут с кириллическим фолбэком — UK/RU не мигают чужой глифой и ничего не тянут со стороны.</p><p><strong>Сервер — в тех же руках:</strong> сайт в <strong>Docker за Caddy</strong> (авто-SSL Let\'s Encrypt, security-заголовки) на том же своём захардненном сервере, что и всё остальное в этом портфолио — дизайн, сборка, деплой и эксплуатация в одних руках.</p>',
  'result' => '<p><strong>Lighthouse (desktop): Performance 100, Accessibility 96, Best Practices 100, SEO 92</strong> — FCP/LCP ~0,4&nbsp;с, CLS 0,02. Фокус с клавиатуры, reduced-motion и адаптив — целы. Всё вместе — тема, три языка, контейнерный стек и сервер под ним — это <strong>один подряд, а не веб-студия плюс отдельный DevOps-подрядчик</strong>. Исходник темы — в репозитории.</p>',
);
$C['uk'] = array(
  'summary' => 'Цей самий сайт: трёхмовне портфоліо на WordPress із написаною вручну блоковою темою — без конструктора. Анімації GSAP/Lenis з повагою до reduced-motion, self-hosted шрифти, Polylang EN/UK/RU + hreflang, у Docker за Caddy з авто-SSL на власному захардненому сервері.',
  'result_metric' => 'Lighthouse 100 / 96 / 100 / 92 · кастомна тема',
  'stack' => 'WordPress, кастомна блокова тема, GSAP, Lenis, Polylang, Docker, Caddy',
  'task' => '<p>Сайт, що продає інженерну роботу, мусить <em>бути</em> доказом. Не шаблон із конструктора, що тягне три мегабайти чужого фреймворку, — а швидкий, доступний, багатомовний сайт, який я зібрав і обслуговую сам, щоб клієнт побачив рівень ще до першого слова.</p>',
  'approach' => '<p><strong>Кастомна тема, а не конструктор:</strong> написана вручну <strong>блокова тема</strong> WordPress (<code>davidv</code>) — власні шаблони, блоки й CSS, без баласту Elementor/Divi. Анімації — <strong>GSAP + Lenis</strong> (плавний скрол), повністю вимикаються за <code>prefers-reduced-motion</code>; жива status-панель у герої — справжня верстка, а не відео.</p><p><strong>Зроблено під три мови:</strong> <strong>Polylang</strong> веде EN/UK/RU з коректним <code>hreflang</code>, а <strong>self-hosted шрифти</strong> йдуть із кириличним фолбеком — UK/RU не блимають чужою гліфою й нічого не тягнуть зі сторони.</p><p><strong>Сервер — у тих самих руках:</strong> сайт у <strong>Docker за Caddy</strong> (авто-SSL Let\'s Encrypt, security-заголовки) на тому ж власному захардненому сервері, що й усе інше в цьому портфоліо — дизайн, збірка, деплой та експлуатація в одних руках.</p>',
  'result' => '<p><strong>Lighthouse (desktop): Performance 100, Accessibility 96, Best Practices 100, SEO 92</strong> — FCP/LCP ~0,4&nbsp;с, CLS 0,02. Фокус із клавіатури, reduced-motion та адаптив — цілі. Усе разом — тема, три мови, контейнерний стек і сервер під ним — це <strong>один підряд, а не вебстудія плюс окремий DevOps-підрядник</strong>. Вихідник теми — у репозиторії.</p>',
);

$keys = array( 'summary' => 'f_sum', 'result_metric' => 'f_metric', 'stack' => 'f_stack', 'task' => 'f_task', 'approach' => 'f_appr', 'result' => 'f_res' );
foreach ( $cases as $lang => $id ) {
  foreach ( $C[ $lang ] as $field => $val ) {
    update_post_meta( $id, $field, $val );
    update_post_meta( $id, '_' . $field, $keys[ $field ] );
  }
  update_post_meta( $id, 'repo_url', $REPO );
  update_post_meta( $id, '_repo_url', 'f_repo' );
  echo "обновлён кейс web/$lang (#$id)\n";
}
