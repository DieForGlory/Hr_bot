TEXTS = {
    "ru": {
        "main_menu": "Главное меню",
        "vacation": "Отпуск",
        "certificates": "Справки",
        "sick_leave": "Больничный",
        "faq": "FAQ",
        "my_requests": "Мои заявки",
        "contacts": "Полезные контакты",
        "choose_language": "Выберите язык / Tilni tanlang:",
        "lang_saved": "Язык успешно изменен."
    },
    "uz": {
        "main_menu": "Asosiy menyu",
        "vacation": "Ta'til",
        "certificates": "Ma'lumotnomalar",
        "sick_leave": "Kasalik varaqasi",
        "faq": "Ko'p so'raladigan savollar",
        "my_requests": "Mening arizalarim",
        "contacts": "Foydali kontaktlar",
        "choose_language": "Выберите язык / Tilni tanlang:",
        "lang_saved": "Til muvaffaqiyatli o'zgartirildi."
    }
}

def get_text(key: str, lang: str = "ru") -> str:
    return TEXTS.get(lang, TEXTS["ru"]).get(key, key)