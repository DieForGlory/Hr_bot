import ssl
import aiohttp
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from db.database import engine
from db.models import User, Request as HRRequest, DocumentTemplate, CalendarDay
from core.config import BOT_TOKEN

# Инициализация FastAPI
app = FastAPI(title="HR Bot Admin")

# Интеграция бота для уведомлений (с обходом SSL)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
connector = aiohttp.TCPConnector(ssl=ssl_context)
session = AiohttpSession()

async def create_client_session():
    return aiohttp.ClientSession(connector=connector)
session._create_client_session = create_client_session

bot = Bot(token=BOT_TOKEN, session=session)

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
    column_list = [HRRequest.id, HRRequest.user_id, HRRequest.status]
    column_searchable_list = [HRRequest.status]
    name = "Заявка"
    name_plural = "Заявки"
    icon = "fa-solid fa-envelope"

    async def on_model_change(self, data, model, is_created, request):
        if not is_created and "status" in data:
            try:
                await bot.send_message(
                    chat_id=model.user_id,
                    text=f"Статус вашей заявки изменен: {data['status']}"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления: {e}")

class DocumentTemplateAdmin(ModelView, model=DocumentTemplate):
    column_list = [DocumentTemplate.id, DocumentTemplate.name, DocumentTemplate.file_path]
    name = "Шаблон"
    name_plural = "Шаблоны документов"
    icon = "fa-solid fa-file-word"

class CalendarDayAdmin(ModelView, model=CalendarDay):
    column_list = [CalendarDay.id, CalendarDay.date, CalendarDay.is_workday]
    name = "День календаря"
    name_plural = "Производственный календарь"
    icon = "fa-solid fa-calendar-days"

# Регистрация представлений
admin.add_view(UserAdmin)
admin.add_view(RequestAdmin)
admin.add_view(DocumentTemplateAdmin)
admin.add_view(CalendarDayAdmin)