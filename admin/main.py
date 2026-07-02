from fastapi import FastAPI
from sqladmin import Admin, ModelView
from aiogram import Bot

from db.database import engine
from db.models import User, Request as HRRequest, DocumentTemplate, CalendarDay, FAQ
from core.config import BOT_TOKEN
from bot.utils.db_api import get_user_by_id
from core.logging_config import action_logger

# Инициализация FastAPI
app = FastAPI(title="HR Bot Admin")

# Интеграция бота для уведомлений
bot = Bot(token=BOT_TOKEN)

# Инициализация SQLAdmin
admin = Admin(app, engine, title="Управление HR Bot")

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.telegram_id, User.full_name, User.role, User.department, User.position, User.is_active]
    column_searchable_list = [User.full_name, User.telegram_id]
    column_sortable_list = [User.id, User.full_name]
    name = "Сотрудник"
    name_plural = "Сотрудники"
    icon = "fa-solid fa-users"

class RequestAdmin(ModelView, model=HRRequest):
    column_list = [
        HRRequest.id, HRRequest.user_id, HRRequest.type, HRRequest.status,
        HRRequest.created_at, HRRequest.manager_comment, HRRequest.hr_comment,
    ]
    column_searchable_list = [HRRequest.status]
    name = "Заявка"
    name_plural = "Заявки"
    icon = "fa-solid fa-envelope"

    async def on_model_change(self, data, model, is_created, request):
        if not is_created and "status" in data:
            try:
                employee = await get_user_by_id(model.user_id)
                if employee and employee.telegram_id:
                    await bot.send_message(
                        chat_id=employee.telegram_id,
                        text=f"Статус вашей заявки изменен: {data['status']}"
                    )
                action_logger.info(
                    "admin_status_change req_id=%s user_id=%s status=%s",
                    model.id, model.user_id, data['status']
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления: {e}")

class DocumentTemplateAdmin(ModelView, model=DocumentTemplate):
    column_list = [DocumentTemplate.id, DocumentTemplate.name]
    form_columns = [DocumentTemplate.name, DocumentTemplate.content, DocumentTemplate.file_path]
    column_details_list = [DocumentTemplate.id, DocumentTemplate.name, DocumentTemplate.content, DocumentTemplate.file_path]
    name = "Шаблон"
    name_plural = "Шаблоны документов"
    icon = "fa-solid fa-file-word"

class FAQAdmin(ModelView, model=FAQ):
    column_list = [FAQ.id, FAQ.question]
    form_columns = [FAQ.question, FAQ.answer]
    column_details_list = [FAQ.id, FAQ.question, FAQ.answer]
    column_searchable_list = [FAQ.question]
    name = "Вопрос FAQ"
    name_plural = "FAQ"
    icon = "fa-solid fa-circle-question"

class CalendarDayAdmin(ModelView, model=CalendarDay):
    column_list = [CalendarDay.id, CalendarDay.date, CalendarDay.is_workday]
    name = "День календаря"
    name_plural = "Производственный календарь"
    icon = "fa-solid fa-calendar-days"

# Регистрация представлений
admin.add_view(UserAdmin)
admin.add_view(RequestAdmin)
admin.add_view(DocumentTemplateAdmin)
admin.add_view(FAQAdmin)
admin.add_view(CalendarDayAdmin)