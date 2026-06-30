from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.utils.db_api import get_user_by_telegram_id, get_user_requests
from aiogram import Router, F, types
from bot.utils.db_api import get_all_faqs, get_faq_by_id
from bot.keyboards.inline import get_faq_list_kb, get_faq_back_kb
from bot.utils.db_api import get_user_by_telegram_id, get_user_requests
router = Router()


def get_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Отпуск")
    builder.button(text="Справки")
    builder.button(text="Больничный")
    builder.button(text="FAQ")
    builder.button(text="Мои заявки")
    builder.button(text="Вопрос HR")
    builder.button(text="Полезные контакты")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Главное меню", reply_markup=get_main_keyboard())


@router.message(F.text == "FAQ")
async def faq_menu(message: types.Message):
    faqs = await get_all_faqs()
    if not faqs:
        await message.answer("Раздел FAQ в данный момент пуст.")
        return
    await message.answer("Выберите интересующий вас вопрос:", reply_markup=get_faq_list_kb(faqs))

@router.callback_query(F.data.startswith("faq_"))
async def process_faq_item(callback: types.CallbackQuery):
    if callback.data == "faq_back":
        faqs = await get_all_faqs()
        await callback.message.edit_text("Выберите интересующий вас вопрос:", reply_markup=get_faq_list_kb(faqs))
        await callback.answer()
        return

    faq_id = int(callback.data.split("_")[1])
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
        await message.answer("Список ваших заявок пуст.")
        return

    status_map = {
        "pending": "На согласовании у руководителя",
        "manager_approved": "На согласовании у HR",
        "hr_approved": "Одобрено",
        "rejected": "Отклонено",
        "done": "Выполнено"
    }

    type_map = {
        "vacation_paid": "Оплачиваемый отпуск",
        "vacation_unpaid": "Отпуск без содержания",
        "income_cert": "Справка о доходах",
        "work_cert": "Справка с места работы",
        "sick_leave": "Больничный"
    }

    text_blocks = []
    for r in reqs:
        st_name = status_map.get(r.status, r.status)
        type_name = type_map.get(r.type, r.type)

        block = f"📝 **Заявка №{r.id}**\nТип: {type_name}\nСтатус: {st_name}"

        if r.start_date and r.end_date:
            block += f"\nПериод: {r.start_date.strftime('%d.%m.%Y')} - {r.end_date.strftime('%d.%m.%Y')}"
        elif r.start_date:
            block += f"\nДата начала: {r.start_date.strftime('%d.%m.%Y')}"

        if r.status == "rejected" and r.hr_comment:
            block += f"\n❌ Причина отказа: {r.hr_comment}"

        text_blocks.append(block)

    full_text = "\n\n---\n\n".join(text_blocks)
    await message.answer(full_text, parse_mode="Markdown")


@router.message(F.text == "Полезные контакты")
async def contacts_menu(message: types.Message):
    await message.answer("Контакты.")