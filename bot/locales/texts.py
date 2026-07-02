TEXTS = {
    "ru": {
        # --- Навигация / общее ---
        "main_menu": "Главное меню",
        "vacation": "📄 Отпуск",
        "certificates": "💰 Справки",
        "sick_leave": "🏥 Больничный",
        "faq": "FAQ",
        "my_requests": "Мои заявки",
        "hr_question": "Вопрос HR",
        "contacts": "Полезные контакты",
        "production_calendar": "📅 Календарь",
        "back_button": "◀️ Назад",
        "choose_language": "Выберите язык / Tilni tanlang:",
        "lang_saved": "Язык успешно изменен.",
        "contacts_text": "По вопросам работы бота и HR-процессов обращайтесь:\n\n📞 HR-отдел: +998 90 000-00-00\n✉️ Email: hr@company.uz\n💬 Telegram: @hr_support",
        "back_to_menu": "Главное меню",
        "session_expired": "Сессия устарела. Начните заново из главного меню.",
        "request_not_found": "Заявка не найдена или уже обработана.",
        "only_text_allowed": "Пожалуйста, отправьте текстовое сообщение.",
        "text_too_long": "Текст слишком длинный или пустой. Сократите сообщение и отправьте ещё раз.",
        "choose_from_list": "Пожалуйста, выберите вариант из списка, используя кнопки ниже.",
        "use_calendar": "Пожалуйста, выберите дату через календарь ниже.",

        # --- Регистрация ---
        "send_phone_button": "Отправить номер телефона",
        "send_phone_prompt": "Система HR. Требуется идентификация по номеру телефона.",
        "identification_success": "Идентификация успешна.",
        "contact_not_yours": "Пожалуйста, отправьте свой собственный контакт через кнопку ниже.",
        "registration_start_prompt": "Сотрудник не найден в базе. Начат процесс регистрации.\n\nВведите ФИО (по паспорту на латинице):",
        "invalid_full_name": "ФИО должно содержать минимум два слова (только буквы, 5–100 символов). Попробуйте ещё раз:",
        "department_choose": "Выберите ваше подразделение из списка:",
        "status_choose": "Укажите ваш статус:",
        "role_employee": "Сотрудник",
        "role_manager": "Руководитель",
        "birth_choose": "Выберите дату рождения через календарь:",
        "birth_pick_year": "Сначала выберите год:",
        "invalid_birth_date": "Дата рождения указана некорректно. Выберите дату ещё раз:",
        "car_info_prompt": "Укажите номер и марку автомобиля (или отправьте '-' если нет):",
        "car_info_invalid": "Укажите номер и марку автомобиля текстом (до 100 символов) или отправьте «-».",
        "photo_prompt": "Загрузите фото для Face ID:",
        "photo_required": "Пожалуйста, загрузите фотографию.",
        "registration_submitted": "Анкета отправлена в HR. Ожидайте уведомления о результатах проверки.",
        "registration_pending": "Анкета находится на рассмотрении HR.",
        "registration_rejected_msg": "В регистрации отказано. Обратитесь в отдел кадров.",
        "reg_account_confirmed": "Ваша учетная запись подтверждена. Доступ к системе открыт.",
        "reg_account_rejected": "В регистрации отказано.",

        # --- Отпуск ---
        "vacation_choose_type": "Выберите тип отпуска:",
        "vacation_type_paid": "Ежегодный оплачиваемый отпуск",
        "vacation_type_unpaid": "Отпуск без содержания",
        "vacation_choose_start": "Выберите дату начала отпуска:",
        "vacation_choose_end": "Выберите дату окончания отпуска:",
        "vacation_no_balance": "У вас нет доступных дней для оплачиваемого отпуска.",
        "vacation_balance_info": "Ваш остаток отпускных дней: {balance}",
        "vacation_end_before_start": "Дата окончания не может быть раньше даты начала.",
        "vacation_only_holidays": "Выбранный период содержит только нерабочие дни.",
        "vacation_over_balance": "Запрошено {days} дней. Доступно только {balance}.\nВыберите дату окончания заново:",
        "vacation_confirmation_summary": "Подтверждение:\nПериод: {start} - {end}\nКоличество списываемых дней: {days}",
        "vacation_confirm_submit": "Отправить заявку",
        "vacation_confirm_cancel": "Отмена",
        "vacation_submitted": "Ваша заявка принята и направлена на согласование.",
        "vacation_approved_final": "Ваш отпуск согласован. Ожидайте приглашение в отдел кадрового администрирования для подписания приказа.",
        "vacation_rejected": "Заявка отклонена.",
        "vacation_start_in_past": "Дата начала отпуска не может быть в прошлом. Выберите другую дату:",
        "vacation_first_day": "Желаем вам отличного отпуска! 😊",
        "comment_label": "Комментарий",

        # --- Больничный ---
        "sick_choose_start": "Выберите дату начала больничного:",
        "sick_date_out_of_range": "Дата начала больничного выглядит некорректно. Выберите дату не старше года и не дальше 30 дней вперёд:",
        "sick_attach_reminder": "После завершения больничного не забудьте прикрепить подтверждающий документ.",
        "sick_reminder_3days": "Напоминаем о необходимости прикрепить подтверждающий документ после завершения больничного.",
        "sick_document_received": "Документ получен, спасибо.",
        "sick_waiting_document": "Пожалуйста, приложите фото, PDF или скан документа.",
        "sick_leave_doc_forward_caption": "Подтверждающий документ по больничному от {full_name}",

        # --- Справки ---
        "cert_choose_type": "Выберите тип справки:",
        "cert_income": "Справка о доходах",
        "cert_work": "Справка с места работы",
        "cert_ask_comment": "При необходимости укажите дополнительную информацию.\nНапример: справка для посольства, дата посещения и т.д.",
        "cert_submitted": "Ваша заявка принята в обработку.",
        "cert_ready": "Ваша справка готова.",
        "cert_progress_notice": "Ваша справка взята в работу.",
        "cert_rejected_notice_prefix": "Заявка на справку отклонена.",
        "cert_pickup_location_label": "Место получения",

        # --- FAQ ---
        "faq_empty": "Раздел FAQ в данный момент пуст.",
        "faq_choose": "Выберите интересующий вас вопрос:",
        "faq_back_button": "Назад к списку вопросов",

        # --- Мои заявки ---
        "my_requests_empty": "Список ваших заявок пуст.",
        "my_requests_card_title": "Заявка №{id}",
        "my_requests_card_type": "Тип",
        "my_requests_card_status": "Статус",
        "my_requests_card_submitted": "Подана",
        "my_requests_card_period": "Период",
        "my_requests_card_start_date": "Дата начала",
        "my_requests_card_comment": "Комментарий",
        "my_requests_card_manager_decision": "Руководитель: решение принято",
        "my_requests_card_hr_decision": "HR: решение принято",
        "my_requests_card_reject_reason": "Причина отказа",

        # --- Вопрос HR ---
        "hr_question_prompt": "Введите ваш вопрос для HR-отдела:",
        "hr_question_sent": "Вопрос передан в HR-отдел.",
        "hr_question_header": "❓ Вопрос от {name} ({department}):\n\n{question}",
        "hr_reply_button": "Ответить",
        "hr_reply_prompt": "Введите текст ответа:",
        "hr_answer_prefix": "Ответ от HR:\n\n{reply}",
        "hr_reply_sent_confirm": "Ответ отправлен сотруднику.",
        "hr_reply_error": "Ошибка: сотрудник не найден или не авторизован.",

        # --- Производственный календарь ---
        "calendar_no_special_days": "В этом месяце особых дней не отмечено — обычный рабочий график.",
        "calendar_non_working": "Нерабочие дни:",
        "calendar_working": "Рабочие дни (перенос):",
        "calendar_prev_month": "◀ Пред. месяц",
        "calendar_next_month": "След. месяц ▶",

        # --- Согласование (руководитель/HR) ---
        "approve_button": "Согласовать",
        "reject_button": "Отклонить",
        "comment_button": "Комментарий",
        "approval_comment_prompt": "Введите комментарий к согласованию:",
        "approval_already_processed": "Заявка уже обработана.",
        "approval_manager_done_suffix": "\n\n✅ Согласовано руководителем.",
        "approval_hr_done_suffix": "\n\n✅ Согласовано HR.",
        "approval_reject_prompt": "Отказ требует комментария. Введите причину отклонения:",
        "approval_comment_required": "Комментарий обязателен. Введите причину отклонения:",
        "approval_approved_with_comment": "Заявка согласована с комментарием.",
        "approval_rejected_notified": "Заявка отклонена, сотрудник уведомлен.",
        "vacation_request_notification": "Заявка на отпуск\nФИО: {full_name}\nОтдел: {department}\nТип: {v_type}\nДаты: {start} - {end}\nКоличество дней: {days}",
        "vacation_hr_notification": "Согласовано руководителем. Заявка на отпуск\nФИО: {full_name}\nОтдел: {department}\nТип: {v_type}\nДаты: {start} - {end}\nКомментарий руководителя: {comment}",

        # --- Регистрация: решение HR ---
        "reg_approve_button": "Одобрить",
        "reg_reject_button": "Отклонить",
        "reg_approved_admin_suffix": "\n\n✅ Одобрено",
        "reg_rejected_admin_suffix": "\n\n❌ Отклонено",
        "registration_notification_header": "Новая заявка на регистрацию:\nФИО: {full_name}\nПодразделение: {subdivision}\nСтатус: {role_text}\nТелефон: {phone}\nUsername: @{tg_username}\nДата рождения: {birth_date}\nАвто: {car_info}",

        # --- Справки: решение бухгалтерии/HR ---
        "cert_progress_button": "В работу",
        "cert_done_button": "Готово",
        "cert_progress_suffix": "\n\n🔄 В работе",
        "cert_done_suffix": "\n\n✅ Готово",
        "cert_pickup_prompt": "При необходимости пришлите PDF/фото справки или укажите место получения текстом.\nЕсли это не требуется — отправьте «-».",
        "cert_notified_ready": "Сотрудник уведомлен о готовности справки.",
        "cert_attachment_prompt_invalid": "Пришлите PDF/фото, текст с местом получения или «-».",
        "cert_request_notification": "Новая заявка на справку: {cert_type}\nСотрудник: {full_name}\nОтдел: {department}\nКомментарий: {comment}",
    },
    "uz": {
        # --- Navigatsiya / umumiy ---
        "main_menu": "Bosh menyu",
        "vacation": "📄 Ta'til",
        "certificates": "💰 Ma'lumotnomalar",
        "sick_leave": "🏥 Kasallik varaqasi",
        "faq": "FAQ",
        "my_requests": "Mening arizalarim",
        "hr_question": "HR'ga savol",
        "contacts": "Foydali kontaktlar",
        "production_calendar": "📅 Kalendar",
        "back_button": "◀️ Orqaga",
        "choose_language": "Выберите язык / Tilni tanlang:",
        "lang_saved": "Til muvaffaqiyatli o'zgartirildi.",
        "contacts_text": "Bot ishlashi va HR jarayonlari bo'yicha savollar uchun murojaat qiling:\n\n📞 HR bo'limi: +998 90 000-00-00\n✉️ Email: hr@company.uz\n💬 Telegram: @hr_support",
        "back_to_menu": "Bosh menyu",
        "session_expired": "Sessiya muddati tugagan. Bosh menyudan qaytadan boshlang.",
        "request_not_found": "Ariza topilmadi yoki allaqachon ko'rib chiqilgan.",
        "only_text_allowed": "Iltimos, matnli xabar yuboring.",
        "text_too_long": "Matn juda uzun yoki bo'sh. Xabarni qisqartirib, qaytadan yuboring.",
        "choose_from_list": "Iltimos, quyidagi tugmalar orqali ro'yxatdan variantni tanlang.",
        "use_calendar": "Iltimos, quyidagi kalendar orqali sanani tanlang.",

        # --- Ro'yxatdan o'tish ---
        "send_phone_button": "Telefon raqamini yuborish",
        "send_phone_prompt": "HR tizimi. Telefon raqami orqali identifikatsiya talab qilinadi.",
        "identification_success": "Identifikatsiya muvaffaqiyatli o'tdi.",
        "contact_not_yours": "Iltimos, quyidagi tugma orqali o'zingizning kontaktingizni yuboring.",
        "registration_start_prompt": "Xodim bazada topilmadi. Ro'yxatdan o'tish jarayoni boshlandi.\n\nF.I.Sh.ni kiriting (pasportdagidek, lotin harflarida):",
        "invalid_full_name": "F.I.Sh. kamida ikki so'zdan iborat bo'lishi kerak (faqat harflar, 5–100 belgi). Qaytadan urinib ko'ring:",
        "department_choose": "Ro'yxatdan bo'linmangizni tanlang:",
        "status_choose": "Maqomingizni ko'rsating:",
        "role_employee": "Xodim",
        "role_manager": "Rahbar",
        "birth_choose": "Tug'ilgan sanangizni kalendar orqali tanlang:",
        "birth_pick_year": "Avval yilni tanlang:",
        "invalid_birth_date": "Tug'ilgan sana noto'g'ri kiritildi. Sanani qaytadan tanlang:",
        "car_info_prompt": "Avtomobil raqami va markasini kiriting (agar yo'q bo'lsa, '-' yuboring):",
        "car_info_invalid": "Avtomobil raqami va markasini matn ko'rinishida kiriting (100 belgigacha) yoki «-» yuboring.",
        "photo_prompt": "Face ID uchun fotosurat yuklang:",
        "photo_required": "Iltimos, fotosuratni yuklang.",
        "registration_submitted": "Anketa HR bo'limiga yuborildi. Tekshiruv natijalari haqida xabar kutib turing.",
        "registration_pending": "Anketangiz HR tomonidan ko'rib chiqilmoqda.",
        "registration_rejected_msg": "Ro'yxatdan o'tish rad etildi. Kadrlar bo'limiga murojaat qiling.",
        "reg_account_confirmed": "Hisobingiz tasdiqlandi. Tizimga kirish ochildi.",
        "reg_account_rejected": "Ro'yxatdan o'tish rad etildi.",

        # --- Ta'til ---
        "vacation_choose_type": "Ta'til turini tanlang:",
        "vacation_type_paid": "Yillik haq to'lanadigan ta'til",
        "vacation_type_unpaid": "Ish haqisiz ta'til",
        "vacation_choose_start": "Ta'til boshlanish sanasini tanlang:",
        "vacation_choose_end": "Ta'til tugash sanasini tanlang:",
        "vacation_no_balance": "Sizda haq to'lanadigan ta'til uchun mavjud kunlar yo'q.",
        "vacation_balance_info": "Sizning ta'til kunlaringiz qoldig'i: {balance}",
        "vacation_end_before_start": "Tugash sanasi boshlanish sanasidan oldin bo'lishi mumkin emas.",
        "vacation_only_holidays": "Tanlangan davr faqat dam olish kunlaridan iborat.",
        "vacation_over_balance": "So'ralgan kunlar soni: {days}. Mavjud: {balance}.\nTugash sanasini qaytadan tanlang:",
        "vacation_confirmation_summary": "Tasdiqlash:\nDavr: {start} - {end}\nHisobdan chiqariladigan kunlar soni: {days}",
        "vacation_confirm_submit": "Arizani yuborish",
        "vacation_confirm_cancel": "Bekor qilish",
        "vacation_submitted": "Arizangiz qabul qilindi va tasdiqlash uchun yuborildi.",
        "vacation_approved_final": "Ta'tilingiz tasdiqlandi. Buyruqni imzolash uchun kadrlar bo'limiga taklif qilinishingizni kuting.",
        "vacation_rejected": "Ariza rad etildi.",
        "vacation_start_in_past": "Ta'til boshlanish sanasi o'tmishda bo'lishi mumkin emas. Boshqa sanani tanlang:",
        "vacation_first_day": "Sizga ajoyib ta'til tilaymiz! 😊",
        "comment_label": "Izoh",

        # --- Kasallik varaqasi ---
        "sick_choose_start": "Kasallik varaqasi boshlanish sanasini tanlang:",
        "sick_date_out_of_range": "Kasallik boshlanish sanasi noto'g'ri ko'rinmoqda. Bir yildan oshmagan va 30 kundan uzoq bo'lmagan sanani tanlang:",
        "sick_attach_reminder": "Kasallik davri tugagach, tasdiqlovchi hujjatni biriktirishni unutmang.",
        "sick_reminder_3days": "Kasallik davri tugagach, tasdiqlovchi hujjatni biriktirish zarurligini eslatib o'tamiz.",
        "sick_document_received": "Hujjat qabul qilindi, rahmat.",
        "sick_waiting_document": "Iltimos, hujjatning fotosurati, PDF yoki skanini yuboring.",
        "sick_leave_doc_forward_caption": "{full_name} dan kasallik varag'i uchun tasdiqlovchi hujjat",

        # --- Ma'lumotnomalar ---
        "cert_choose_type": "Ma'lumotnoma turini tanlang:",
        "cert_income": "Daromad to'g'risida ma'lumotnoma",
        "cert_work": "Ish joyidan ma'lumotnoma",
        "cert_ask_comment": "Zarur bo'lsa, qo'shimcha ma'lumot kiriting.\nMasalan: elchixona uchun ma'lumotnoma, tashrif sanasi va h.k.",
        "cert_submitted": "Arizangiz ko'rib chiqish uchun qabul qilindi.",
        "cert_ready": "Ma'lumotnomangiz tayyor.",
        "cert_progress_notice": "Ma'lumotnomangiz ish jarayoniga qabul qilindi.",
        "cert_rejected_notice_prefix": "Ma'lumotnoma uchun ariza rad etildi.",
        "cert_pickup_location_label": "Olish joyi",

        # --- FAQ ---
        "faq_empty": "FAQ bo'limi hozircha bo'sh.",
        "faq_choose": "Sizni qiziqtirgan savolni tanlang:",
        "faq_back_button": "Savollar ro'yxatiga qaytish",

        # --- Mening arizalarim ---
        "my_requests_empty": "Arizalaringiz ro'yxati bo'sh.",
        "my_requests_card_title": "Ariza №{id}",
        "my_requests_card_type": "Turi",
        "my_requests_card_status": "Holati",
        "my_requests_card_submitted": "Topshirilgan",
        "my_requests_card_period": "Davr",
        "my_requests_card_start_date": "Boshlanish sanasi",
        "my_requests_card_comment": "Izoh",
        "my_requests_card_manager_decision": "Rahbar: qaror qabul qilindi",
        "my_requests_card_hr_decision": "HR: qaror qabul qilindi",
        "my_requests_card_reject_reason": "Rad etish sababi",

        # --- HR'ga savol ---
        "hr_question_prompt": "HR bo'limi uchun savolingizni kiriting:",
        "hr_question_sent": "Savolingiz HR bo'limiga yuborildi.",
        "hr_question_header": "❓ {name} ({department}) dan savol:\n\n{question}",
        "hr_reply_button": "Javob berish",
        "hr_reply_prompt": "Javob matnini kiriting:",
        "hr_answer_prefix": "HR javobi:\n\n{reply}",
        "hr_reply_sent_confirm": "Javob xodimga yuborildi.",
        "hr_reply_error": "Xatolik: xodim topilmadi yoki avtorizatsiyadan o'tmagan.",

        # --- Ishlab chiqarish kalendari ---
        "calendar_no_special_days": "Bu oyda maxsus kunlar belgilanmagan — odatdagi ish jadvali.",
        "calendar_non_working": "Dam olish kunlari:",
        "calendar_working": "Ish kunlari (ko'chirilgan):",
        "calendar_prev_month": "◀ Oldingi oy",
        "calendar_next_month": "Keyingi oy ▶",

        # --- Tasdiqlash (rahbar/HR) ---
        "approve_button": "Tasdiqlash",
        "reject_button": "Rad etish",
        "comment_button": "Izoh",
        "approval_comment_prompt": "Tasdiqlash uchun izoh kiriting:",
        "approval_already_processed": "Ariza allaqachon ko'rib chiqilgan.",
        "approval_manager_done_suffix": "\n\n✅ Rahbar tomonidan tasdiqlandi.",
        "approval_hr_done_suffix": "\n\n✅ HR tomonidan tasdiqlandi.",
        "approval_reject_prompt": "Rad etish uchun izoh talab qilinadi. Rad etish sababini kiriting:",
        "approval_comment_required": "Izoh majburiy. Rad etish sababini kiriting:",
        "approval_approved_with_comment": "Ariza izoh bilan tasdiqlandi.",
        "approval_rejected_notified": "Ariza rad etildi, xodimga xabar berildi.",
        "vacation_request_notification": "Ta'til arizasi\nF.I.Sh.: {full_name}\nBo'lim: {department}\nTuri: {v_type}\nSanalar: {start} - {end}\nKunlar soni: {days}",
        "vacation_hr_notification": "Rahbar tomonidan tasdiqlandi. Ta'til arizasi\nF.I.Sh.: {full_name}\nBo'lim: {department}\nTuri: {v_type}\nSanalar: {start} - {end}\nRahbar izohi: {comment}",

        # --- Ro'yxatdan o'tish: HR qarori ---
        "reg_approve_button": "Tasdiqlash",
        "reg_reject_button": "Rad etish",
        "reg_approved_admin_suffix": "\n\n✅ Tasdiqlandi",
        "reg_rejected_admin_suffix": "\n\n❌ Rad etildi",
        "registration_notification_header": "Yangi ro'yxatdan o'tish arizasi:\nF.I.Sh.: {full_name}\nBo'linma: {subdivision}\nMaqomi: {role_text}\nTelefon: {phone}\nUsername: @{tg_username}\nTug'ilgan sana: {birth_date}\nAvtomobil: {car_info}",

        # --- Ma'lumotnomalar: buxgalteriya/HR qarori ---
        "cert_progress_button": "Ishga olish",
        "cert_done_button": "Tayyor",
        "cert_progress_suffix": "\n\n🔄 Jarayonda",
        "cert_done_suffix": "\n\n✅ Tayyor",
        "cert_pickup_prompt": "Zarur bo'lsa, ma'lumotnomaning PDF/fotosuratini yuboring yoki olish joyini matn bilan ko'rsating.\nAgar kerak bo'lmasa — «-» yuboring.",
        "cert_notified_ready": "Xodimga ma'lumotnoma tayyorligi haqida xabar berildi.",
        "cert_attachment_prompt_invalid": "PDF/fotosurat, olish joyi haqida matn yoki «-» yuboring.",
        "cert_request_notification": "Yangi ma'lumotnoma arizasi: {cert_type}\nXodim: {full_name}\nBo'lim: {department}\nIzoh: {comment}",
    },
}


def get_text(key: str, lang: str = "ru") -> str:
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))


def get_text_variants(key: str) -> list:
    """Значения ключа на всех поддерживаемых языках — для языконезависимого
    сопоставления кнопок ReplyKeyboard (F.text.in_(...))."""
    seen = []
    for lang in TEXTS:
        value = TEXTS[lang].get(key)
        if value is not None and value not in seen:
            seen.append(value)
    return seen


def resolve_choice(choice_map: dict, text: str):
    """choice_map: {каноническое_значение: ключ_в_texts}. Возвращает каноническое
    значение, чей локализованный текст (на любом языке) совпал с `text`, иначе None.
    Нужно там, где нажатый текст кнопки определяет бизнес-логику (роль, тип заявки
    и т.п.) — сравнивать с сырым текстом на одном языке нельзя."""
    for canonical, key in choice_map.items():
        if text in (TEXTS.get("ru", {}).get(key), TEXTS.get("uz", {}).get(key)):
            return canonical
    return None
