# Design Backup v1 (DigiStore / shadcn-style)

Это резервная копия исходного дизайна сайта на момент перехода к новому
оформлению в стиле Steam + Epic Games.

## Что лежит здесь

- `main.css` — основная таблица стилей старого дизайна.
- `dashboard.css` — стили личного кабинета.
- `support_widget.css` — стили виджета поддержки.

## Шаблоны

Резервные копии HTML-шаблонов находятся в:
`backend/templates/design_backup_v1/` (`base.html`, `home.html`).

## Как откатить старый дизайн

1. Скопируйте файлы из этой папки обратно в `backend/static/css/`.
2. Скопируйте `base.html` и `home.html` из
   `backend/templates/design_backup_v1/` обратно в `backend/templates/`.
3. Перезапустите сервер (или обновите страницу с очисткой кэша).
