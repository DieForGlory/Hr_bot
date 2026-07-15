# bot/utils/status_labels.py
VACATION_STATUS_LABELS = {
    "ru": {
        "pending": "На согласовании у руководителя",
        "manager_approved": "На согласовании у HR",
        "hr_approved": "Одобрено",
        "rejected": "Отклонено",
        "done": "Выполнено",
    },
    "uz": {
        "pending": "Rahbar tasdig'ini kutmoqda",
        "manager_approved": "HR tasdig'ini kutmoqda",
        "hr_approved": "Tasdiqlandi",
        "rejected": "Rad etildi",
        "done": "Bajarildi",
    },
}

SICK_LEAVE_STATUS_LABELS = {
    "ru": {
        "pending": "Больничный оформлен",
        "rejected": "Отклонено",
        "done": "Документ получен",
    },
    "uz": {
        "pending": "Kasallik varaqasi rasmiylashtirildi",
        "rejected": "Rad etildi",
        "done": "Hujjat qabul qilindi",
    },
}

CERT_STATUS_LABELS = {
    "ru": {
        "pending": "Принято",
        "in_progress": "В работе",
        "done": "Готово",
        "rejected": "Отклонено",
    },
    "uz": {
        "pending": "Qabul qilindi",
        "in_progress": "Jarayonda",
        "done": "Tayyor",
        "rejected": "Rad etildi",
    },
}

TYPE_LABELS = {
    "ru": {
        "vacation_paid": "Оплачиваемый отпуск",
        "vacation_unpaid": "Отпуск без содержания",
        "vacation_marriage": "Отпуск в связи с бракосочетанием",
        "vacation_childbirth": "Отпуск в связи с рождением ребенка",
        "income_cert": "Справка о доходах",
        "work_cert": "Справка с места работы",
        "sick_leave": "Больничный",
    },
    "uz": {
        "vacation_paid": "Haq to'lanadigan ta'til",
        "vacation_unpaid": "Ish haqisiz ta'til",
        "vacation_marriage": "Nikoh munosabati bilan ta'til",
        "vacation_childbirth": "Bola tug'ilishi munosabati bilan ta'til",
        "income_cert": "Daromad to'g'risida ma'lumotnoma",
        "work_cert": "Ish joyidan ma'lumotnoma",
        "sick_leave": "Kasallik varaqasi",
    },
}


def get_status_label(req_type: str, status: str, lang: str = "ru") -> str:
    if req_type.startswith("vacation"):
        labels = VACATION_STATUS_LABELS
    elif req_type == "sick_leave":
        labels = SICK_LEAVE_STATUS_LABELS
    elif req_type in ("income_cert", "work_cert"):
        labels = CERT_STATUS_LABELS
    else:
        return status
    return labels.get(lang, labels["ru"]).get(status, status)


def get_type_label(req_type: str, lang: str = "ru") -> str:
    return TYPE_LABELS.get(lang, TYPE_LABELS["ru"]).get(req_type, req_type)
