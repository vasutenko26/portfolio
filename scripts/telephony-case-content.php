<?php
/** Реальный контент кейса telephony (EN/UK/RU). wp eval-file */
$cases = array( 'en' => 5, 'uk' => 13, 'ru' => 14 );
$REPO = 'https://github.com/vasutenko26/portfolio/tree/main/telephony';

$C = array();
$C['en'] = array(
  'summary' => 'Office IP-PBX on Asterisk/FreePBX: inbound routing, IVR, call queues, recording and remote extensions — on the client\'s own server, no cloud per-seat lock-in. SIP/RTP stay off the public internet by design.',
  'result_metric' => 'Real CDR + recording · SIP off the public net',
  'stack' => 'Asterisk 21, FreePBX 17, PJSIP, Docker, MariaDB',
  'task' => '<p>A growing office needs a real phone system: one number that greets callers, splits Sales from Support, queues calls to a team, records conversations for quality, and gives remote staff internal extensions — without monthly per-seat cloud fees or being locked to one vendor\'s platform.</p>',
  'approach' => '<p><strong>IP-PBX on the client\'s own server:</strong> Asterisk&nbsp;21 + FreePBX&nbsp;17 in Docker. Four PJSIP extensions (reception, sales, support, manager); an <strong>IVR</strong> — «press&nbsp;1 for Sales, 2 for Support»; a <strong>Support queue</strong> (ring strategy + forced call recording); a <strong>Time Condition</strong> for business hours, with an after-hours route. The <code>SIP trunk</code> connects to whatever provider the client already uses, so numbers and rates stay theirs.</p><p><strong>Security first:</strong> SIP (5060) and the RTP media ports listen only on the internal network — <strong>never published to the internet</strong>. An exposed PBX draws toll-fraud and brute-force bots within hours, a direct financial risk; closing it off removes that whole attack surface.</p><p><strong>Proven, not claimed:</strong> a real call was generated locally and walked the whole path — IVR&nbsp;→ «2»&nbsp;→ Support queue&nbsp;→ answered agent — producing a genuine <strong>CDR record and a recording file</strong>, exactly as a customer call would.</p>',
  'result' => '<p>A working office PBX — greeting, Sales/Support routing, queue, recording and business-hours logic — fully <strong>self-hosted</strong> and portable to any SIP provider, scaling from 3 to <strong>200+ extensions</strong> on the same design. The test call landed as a real CDR with a linked recording. The full dialplan, queues, IVR and time conditions are in the repo (secrets replaced with placeholders) so the whole PBX is reproducible from scratch.</p>',
);
$C['ru'] = array(
  'summary' => 'Офисная IP-АТС на Asterisk/FreePBX: входящие, IVR, очереди, запись и внутренние для удалёнки — на своём сервере клиента, без помесячной привязки к облаку. SIP/RTP по умолчанию не торчат в интернет.',
  'result_metric' => 'Реальный CDR + запись · SIP не в публичной сети',
  'stack' => 'Asterisk 21, FreePBX 17, PJSIP, Docker, MariaDB',
  'task' => '<p>Растущему офису нужна нормальная телефония: один номер, который встречает звонящего, разводит продажи и поддержку, ставит звонки в очередь на команду, пишет разговоры для контроля качества и даёт удалёнщикам внутренние номера — без помесячной оплаты за каждое место в облаке и без привязки к платформе одного вендора.</p>',
  'approach' => '<p><strong>IP-АТС на своём сервере клиента:</strong> Asterisk&nbsp;21 + FreePBX&nbsp;17 в Docker. Четыре внутренних номера PJSIP (ресепшен, продажи, поддержка, руководитель); <strong>IVR</strong> — «1 — продажи, 2 — поддержка»; <strong>очередь поддержки</strong> (стратегия дозвона + принудительная запись); <strong>time condition</strong> на рабочие часы с маршрутом для нерабочего времени. <code>SIP-транк</code> подключается под того провайдера, которым клиент уже пользуется, — номера и тарифы остаются его.</p><p><strong>Безопасность в первую очередь:</strong> SIP (5060) и RTP-порты слушают только во внутренней сети — <strong>наружу не публикуются вообще</strong>. Открытая в интернет АТС за часы собирает toll-fraud и брутфорс-ботов — это прямой финансовый риск; закрытие убирает всю эту поверхность атаки.</p><p><strong>Доказано, а не на словах:</strong> локально сгенерирован реальный звонок, прошедший весь путь — IVR&nbsp;→ «2»&nbsp;→ очередь поддержки&nbsp;→ ответ агента — и оставивший настоящую <strong>запись в CDR и файл записи разговора</strong>, ровно как клиентский звонок.</p>',
  'result' => '<p>Рабочая офисная АТС — приветствие, разводка продажи/поддержка, очередь, запись и логика рабочих часов — полностью <strong>на своём сервере</strong> и переносимая на любого SIP-провайдера, масштабируется от 3 до <strong>200+ номеров</strong> на той же схеме. Тест-звонок лёг реальным CDR со связанной записью. Полный dialplan, очереди, IVR и time conditions — в репозитории (секреты заменены плейсхолдерами), так что вся АТС воспроизводится с нуля.</p>',
);
$C['uk'] = array(
  'summary' => 'Офісна IP-АТС на Asterisk/FreePBX: вхідні, IVR, черги, запис і внутрішні для віддаленки — на власному сервері клієнта, без помісячної прив\'язки до хмари. SIP/RTP за замовчуванням не стирчать в інтернет.',
  'result_metric' => 'Реальний CDR + запис · SIP не в публічній мережі',
  'stack' => 'Asterisk 21, FreePBX 17, PJSIP, Docker, MariaDB',
  'task' => '<p>Офісу, що зростає, потрібна нормальна телефонія: один номер, який вітає того, хто телефонує, розводить продажі та підтримку, ставить дзвінки в чергу на команду, пише розмови для контролю якості та дає віддаленим співробітникам внутрішні номери — без помісячної оплати за кожне місце в хмарі й без прив\'язки до платформи одного вендора.</p>',
  'approach' => '<p><strong>IP-АТС на власному сервері клієнта:</strong> Asterisk&nbsp;21 + FreePBX&nbsp;17 у Docker. Чотири внутрішні номери PJSIP (ресепшен, продажі, підтримка, керівник); <strong>IVR</strong> — «1 — продажі, 2 — підтримка»; <strong>черга підтримки</strong> (стратегія додзвону + примусовий запис); <strong>time condition</strong> на робочі години з маршрутом для неробочого часу. <code>SIP-транк</code> підключається під того провайдера, яким клієнт уже користується, — номери й тарифи лишаються його.</p><p><strong>Безпека насамперед:</strong> SIP (5060) і RTP-порти слухають лише у внутрішній мережі — <strong>назовні не публікуються взагалі</strong>. Відкрита в інтернет АТС за години збирає toll-fraud і брутфорс-ботів — це прямий фінансовий ризик; закриття прибирає всю цю поверхню атаки.</p><p><strong>Доведено, а не на словах:</strong> локально згенеровано реальний дзвінок, що пройшов увесь шлях — IVR&nbsp;→ «2»&nbsp;→ черга підтримки&nbsp;→ відповідь агента — і залишив справжній <strong>запис у CDR та файл запису розмови</strong>, рівно як клієнтський дзвінок.</p>',
  'result' => '<p>Робоча офісна АТС — привітання, розведення продажі/підтримка, черга, запис і логіка робочих годин — повністю <strong>на власному сервері</strong> й переносна на будь-якого SIP-провайдера, масштабується від 3 до <strong>200+ номерів</strong> на тій самій схемі. Тест-дзвінок ліг реальним CDR зі зв\'язаним записом. Повний dialplan, черги, IVR і time conditions — у репозиторії (секрети замінено плейсхолдерами), тож уся АТС відтворюється з нуля.</p>',
);

$keys = array( 'summary' => 'f_sum', 'result_metric' => 'f_metric', 'stack' => 'f_stack', 'task' => 'f_task', 'approach' => 'f_appr', 'result' => 'f_res' );
foreach ( $cases as $lang => $id ) {
  foreach ( $C[ $lang ] as $field => $val ) {
    update_post_meta( $id, $field, $val );
    update_post_meta( $id, '_' . $field, $keys[ $field ] );
  }
  update_post_meta( $id, 'repo_url', $REPO );
  update_post_meta( $id, '_repo_url', 'f_repo' );
  echo "обновлён кейс telephony/$lang (#$id)\n";
}
