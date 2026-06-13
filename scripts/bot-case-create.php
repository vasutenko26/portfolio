<?php
/** Создаёт/обновляет трёхъязычный кейс «Telegram-ассистент». Идемпотентно. wp eval-file */
$titles = [
    'en' => 'Telegram task assistant — self-hosted, AI-powered',
    'uk' => 'Telegram-асистент задач — self-hosted, з AI',
    'ru' => 'Telegram-ассистент задач — self-hosted, с AI',
];
$slugs = ['en' => 'bot', 'uk' => 'bot-uk', 'ru' => 'bot-ru'];
$roles = ['en' => 'AI assistant', 'uk' => 'AI-асистент', 'ru' => 'AI-ассистент'];

$ids = [];
foreach (['en', 'uk', 'ru'] as $l) {
    $ex = get_page_by_path($slugs[$l], OBJECT, 'case');
    if ($ex) {
        $id = $ex->ID;
        wp_update_post(['ID' => $id, 'post_title' => $titles[$l], 'menu_order' => 6, 'post_status' => 'publish']);
    } else {
        $id = wp_insert_post([
            'post_type' => 'case', 'post_status' => 'publish',
            'post_title' => $titles[$l], 'post_name' => $slugs[$l], 'menu_order' => 6,
        ]);
    }
    if (function_exists('pll_set_post_language')) pll_set_post_language($id, $l);
    update_post_meta($id, 'service_key', 'bot');
    update_post_meta($id, 'role_label', $roles[$l]);
    update_post_meta($id, '_role_label', 'f_role');
    $ids[$l] = $id;
}
if (function_exists('pll_save_post_translations')) pll_save_post_translations($ids);
echo json_encode($ids) . "\n";
