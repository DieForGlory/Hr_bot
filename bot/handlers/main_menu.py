from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.utils.db_api import get_all_faqs, get_faq_by_id, get_user_by_telegram_id, get_user_requests
from bot.utils.status_labels import get_status_label, get_type_label
from bot.utils.validators import parse_callback_id
from bot.keyboards.inline import get_faq_list_kb, get_faq_back_kb
from bot.locales.texts import get_text

router = Router()


def get_main_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=get_text("vacation", lang))
    builder.button(text=get_text("certificates", lang))
    builder.button(text=get_text("sick_leave", lang))
    builder.button(text=get_text("faq", lang))
    builder.button(text=get_text("my_requests", lang))
    builder.button(text=get_text("hr_question", lang))
    builder.button(text=get_text("contacts", lang))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


@router.message(F.text == "Назад")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Универсальная кнопка «Назад» — сбрасывает текущий сценарий и возвращает в главное меню."""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await state.clear()
    await message.answer(get_text("back_to_menu", lang), reply_markup=get_main_keyboard(lang))


@router.message(F.text == "FAQ")
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
        await callback.message.edit_text(text, reply_markup=get_faq_back_kb(), parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == "Мои заявки")
async def my_requests(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    reqs = await get_user_requests(user.id)
    if not reqs:
        await message.answer(get_text("my_requests_empty", user.language))
        return

    text_blocks = []
    for r in reqs:
        st_name = get_status_label(r.type, r.status)
        type_name = get_type_label(r.type)

        block = f"📝 **Заявка №{r.id}**\nТип: {type_name}\nСтатус: {st_name}"
        block += f"\nПодана: {r.created_at.strftime('%d.%m.%Y %H:%M')}"

        if r.start_date and r.end_date:
            block += f"\nПериод: {r.start_date.strftime('%d.%m.%Y')} - {r.end_date.strftime('%d.%m.%Y')}"
        elif r.start_date:
            block += f"\nДата начала: {r.start_date.strftime('%d.%m.%Y')}"

        if r.comment:
            block += f"\n💬 Комментарий: {r.comment}"

        if r.type.startswith("vacation"):
            if r.manager_decided_at:
                block += f"\n👤 Руководитель: решение принято {r.manager_decided_at.strftime('%d.%m.%Y %H:%M')}"
                if r.manager_comment:
                    block += f" — «{r.manager_comment}»"

            if r.hr_decided_at:
                block += f"\n🧑‍💼 HR: решение принято {r.hr_decided_at.strftime('%d.%m.%Y %H:%M')}"

        if r.status == "rejected" and r.hr_comment:
            block += f"\n❌ Причина отказа: {r.hr_comment}"

        text_blocks.append(block)

    full_text = "\n\n---\n\n".join(text_blocks)
    await message.answer(full_text, parse_mode="Markdown")


@router.message(F.text == "Полезные контакты")
async def contacts_menu(message: types.Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(get_text("contacts_text", lang))