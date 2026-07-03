# admin/permissions.py
# Каталог разрешений сервиса hr_bot — единый источник правды.
# Отдаётся auth-service по GET /api/sync/permissions (кнопка «Синхронизировать
# разрешения» в админке auth-service). Имена совпадают с require_permission(...)
# в роутерах.

HR_BOT_PERMISSIONS = [
    {"name": "hr_bot.dashboard.view", "displayName": "Дашборд: просмотр",
     "description": "Доступ к дашборду админки", "category": "dashboard"},

    {"name": "hr_bot.users.view", "displayName": "Сотрудники: просмотр",
     "description": "Просмотр списка и карточек сотрудников", "category": "users"},
    {"name": "hr_bot.users.manage", "displayName": "Сотрудники: изменение",
     "description": "Редактирование, одобрение/отклонение регистраций, роли, руководитель", "category": "users"},

    {"name": "hr_bot.requests.view", "displayName": "Заявки: просмотр",
     "description": "Просмотр заявок сотрудников (отпуска, справки, больничные)", "category": "requests"},
    {"name": "hr_bot.requests.manage", "displayName": "Заявки: обработка",
     "description": "Согласование/отклонение заявок и работа со справками", "category": "requests"},

    {"name": "hr_bot.templates.view", "displayName": "Шаблоны: просмотр",
     "description": "Просмотр шаблонов документов", "category": "templates"},
    {"name": "hr_bot.templates.manage", "displayName": "Шаблоны: изменение",
     "description": "Создание и редактирование шаблонов документов", "category": "templates"},

    {"name": "hr_bot.faq.view", "displayName": "FAQ: просмотр",
     "description": "Просмотр вопросов и ответов FAQ", "category": "faq"},
    {"name": "hr_bot.faq.manage", "displayName": "FAQ: изменение",
     "description": "Создание/редактирование/удаление FAQ", "category": "faq"},

    {"name": "hr_bot.calendar.view", "displayName": "Календарь: просмотр",
     "description": "Просмотр производственного календаря", "category": "calendar"},
    {"name": "hr_bot.calendar.manage", "displayName": "Календарь: изменение",
     "description": "Изменение производственного календаря", "category": "calendar"},
]
