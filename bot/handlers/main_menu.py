from datetime import date
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.utils.db_api import (
    get_all_faqs, get_faq_by_id, get_user_by_telegram_id, get_user_requests,
    get_calendar_days_for_month,
)
from bot.utils.status_labels import get_status_label, get_type_label
from bot.utils.validators import parse_callback_id
from bot.keyboards.inline import get_faq_list_kb, get_faq_back_kb, get_calendar_nav_kb
from bot.locales.texts import get_text, get_text_variants

router = Router()

# Подпись специально одинакова на всех языках — не требует перевода/языконезависимого матчинга
LANGUAGE_SWITCH_BUTTON = "🌐 Язык / Til"

MONTH_NAMES = {
    "ru": {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
        7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
    },
    "uz": {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
        7: "Iyul", 8: "Avgust", 9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr",
    },
}


def get_main_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=get_text("vacation", lang))
    builder.button(text=get_text("certificates", lang))
    builder.button(text=get_text("sick_leave", lang))
    builder.button(text=get_text("faq", lang))
    builder.button(text=get_text("my_requests", lang))
    builder.button(text=get_text("hr_question", lang))
    builder.button(text=get_text("contacts", lang))
    builder.button(text=get_text("production_calendar", lang))
    builder.button(text=LANGUAGE_SWITCH_BUTTON)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def _format_calendar_month(year: int, month: int, days, lang: str = "ru") -> str:
    month_names = MONTH_NAMES.get(lang, MONTH_NAMES["ru"])
    title = f"{get_text('production_calendar', lang)} — {month_names[month]} {year}"

    non_working = [d for d in days if not d.is_workday]
    working = [d for d in days if d.is_workday]

    if not days:
        return f"{title}\n\n{get_text('calendar_no_special_days', lang)}"

    lines = [title, ""]
    if non_working:
        lines.append(get_text("calendar_non_working", lang))
        for d in non_working:
            entry = d.date.strftime('%d.%m.%Y')
            if d.description:
                entry += f" — {d.description}"
            lines.append(f"• {entry}")
        lines.append("")
    if working:
        lines.append(get_text("calendar_working", lang))
        for d in working:
            entry = d.date.strftime('%d.%m.%Y')
            if d.description:
                entry += f" — {d.description}"
            lines.append(f"• {entry}")

    return "\n".join(lines).strip()


@router.message(F.text.in_(get_text_variants("production_calendar")))
async def calendar_menu(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    today = date.today()
    days = await get_calendar_days_for_month(today.year, today.month)
    text = _format_calendar_month(today.year, today.month, days, lang)
    await message.answer(text, reply_markup=get_calendar_nav_kb(today.year, today.month, lang))


@router.callback_query(F.data.startswith("cal_"))
async def process_calendar_nav(callback: types.CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.language if user else "ru"

    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer()
        return
    try:
        year, month = int(parts[1]), int(parts[2])
    except ValueError:
        await callback.answer()
        return

    days = await get_calendar_days_for_month(year, month)
    text = _format_calendar_month(year, month, days, lang)
    await callback.message.edit_text(text, reply_markup=get_calendar_nav_kb(year, month, lang))
    await callback.answer()


@router.message(F.text.in_(get_text_variants("back_button")))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Универсальная кнопка «Назад» — сбрасывает текущий сценарий и возвращает в главное меню."""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await state.clear()
    await message.answer(get_text("back_to_menu", lang), reply_markup=get_main_keyboard(lang))


@router.message(F.text.in_(get_text_variants("faq")))
async def faq_menu(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    faqs = await get_all_faqs()
    if not faqs:
        await message.answer(get_text("faq_empty", lang))
        return
    await message.answer(get_text("faq_choose", lang), reply_markup=get_faq_list_kb(faqs))

@router.callback_query(F.data.startswith("faq_"))
async def process_faq_item(callback: types.CallbackQuery):
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.language if user else "ru"
    if callback.data == "faq_back":
        faqs = await get_all_faqs()
        await callback.message.edit_text(get_text("faq_choose", lang), reply_markup=get_faq_list_kb(faqs))
        await callback.answer()
        return

    faq_id = parse_callback_id(callback.data)
    if faq_id is None:
        await callback.answer()
        return

    faq = await get_faq_by_id(faq_id)
    if faq:
        text = f"**{faq.question}**\n\n{faq.answer}"
        await callback.message.edit_text(text, reply_markup=get_faq_back_kb(lang), parse_mode="Markdown")
    await callback.answer()


@router.message(F.text.in_(get_text_variants("my_requests")))
async def my_requests(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return
    lang = user.language

    reqs = await get_user_requests(user.id)
    if not reqs:
        await message.answer(get_text("my_requests_empty", lang))
        return

    text_blocks = []
    for r in reqs:
        st_name = get_status_label(r.type, r.status, lang)
        type_name = get_type_label(r.type, lang)

        title = get_text("my_requests_card_title", lang).format(id=r.id)
        block = f"📝 **{title}**\n{get_text('my_requests_card_type', lang)}: {type_name}\n{get_text('my_requests_card_status', lang)}: {st_name}"
        block += f"\n{get_text('my_requests_card_submitted', lang)}: {r.created_at.strftime('%d.%m.%Y %H:%M')}"

        if r.start_date and r.end_date:
            block += f"\n{get_text('my_requests_card_period', lang)}: {r.start_date.strftime('%d.%m.%Y')} - {r.end_date.strftime('%d.%m.%Y')}"
        elif r.start_date:
            block += f"\n{get_text('my_requests_card_start_date', lang)}: {r.start_date.strftime('%d.%m.%Y')}"

        if r.comment:
            block += f"\n💬 {get_text('my_requests_card_comment', lang)}: {r.comment}"

        if r.type.startswith("vacation"):
            if r.manager_decided_at:
                block += f"\n👤 {get_text('my_requests_card_manager_decision', lang)} {r.manager_decided_at.strftime('%d.%m.%Y %H:%M')}"
                if r.manager_comment:
                    block += f" — «{r.manager_comment}»"

            if r.hr_decided_at:
                block += f"\n🧑‍💼 {get_text('my_requests_card_hr_decision', lang)} {r.hr_decided_at.strftime('%d.%m.%Y %H:%M')}"

        if r.status == "rejected" and r.hr_comment:
            block += f"\n❌ {get_text('my_requests_card_reject_reason', lang)}: {r.hr_comment}"

        text_blocks.append(block)

    full_text = "\n\n---\n\n".join(text_blocks)
    await message.answer(full_text, parse_mode="Markdown")


@router.message(F.text.in_(get_text_variants("contacts")))
async def contacts_menu(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("contacts_text", lang))
