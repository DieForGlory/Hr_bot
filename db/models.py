from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, Date, Float, ForeignKey, DateTime, func
from db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    phone = Column(String)
    full_name = Column(String)
    role = Column(String, default="employee")
    manager_id = Column(Integer, nullable=True)
    vacation_days_balance = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    language = Column(String, default="ru")
    # Новые поля анкеты
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    tg_username = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    car_info = Column(String, nullable=True)
    face_id_photo = Column(String, nullable=True)
    approval_status = Column(String, default="approved")
    # Кадровое состояние из справочника (Excel): "Работа", "Отпуск основной",
    # "Отпуск по уходу за ребенком", "Болезнь" и т.д. Для directory-записей
    # (импортированных сотрудников, ещё не привязавших Telegram).
    work_state = Column(String, nullable=True)
    # Расчёт остатка отпускных по алгоритму Excel (п.3). Дата приёма — строкой
    # "dd.mm.yyyy" (как birth_date). used_* — уже потраченные дни (рабочие/календарные,
    # колонки S/T). Остаток вычисляется на лету в bot/utils/vacation_balance.py.
    hire_date = Column(String, nullable=True)
    used_work_days = Column(Float, default=0)
    used_calendar_days = Column(Float, default=0)
    # Доступ в веб-админку теперь даёт gateway (auth-service, роли/разрешения сервиса
    # hr_bot). Собственная авторизация админки удалена — поля login/password_hash больше
    # не нужны.


class CalendarDay(Base):
    __tablename__ = "calendar"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    is_workday = Column(Boolean, default=False)
    description = Column(String, nullable=True)

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String) # vacation_paid, vacation_unpaid, income_cert, work_cert, sick_leave
    status = Column(String, default="pending") # pending, manager_approved, hr_approved, rejected, done / in_progress (cert)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    days_count = Column(Integer, nullable=True)
    comment = Column(String, nullable=True)
    hr_comment = Column(String, nullable=True)
    manager_comment = Column(String, nullable=True)
    manager_decided_at = Column(DateTime, nullable=True)
    hr_decided_at = Column(DateTime, nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class DocumentTemplate(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # Текст шаблона редактируется прямо в админке; file_path — запасной вариант (файл на диске)
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)

class FAQ(Base):
    __tablename__ = "faq"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String)
    answer = Column(Text)


class NotificationQueue(Base):
    """Очередь отложенных уведомлений админам/согласующим лицам (п.5 ТЗ).

    Уведомления, сгенерированные вне рабочего окна (08:00–19:00 пн–пт),
    сохраняются здесь с scheduled_at = начало следующего рабочего окна и
    отправляются планировщиком, когда окно открывается. Клавиатура не
    сериализуется целиком — вместо этого храним её тип (kb_kind) и id заявки
    (kb_ref_id), чтобы пересобрать её при отправке (callback_data не протухает).
    """
    __tablename__ = "notification_queue"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    text = Column(Text, nullable=False)
    attachment_kind = Column(String, nullable=True)   # 'photo' | 'document' | None
    attachment_file_id = Column(String, nullable=True)
    kb_kind = Column(String, nullable=True)           # 'approval' | 'cert' | 'registration' | None
    kb_ref_id = Column(Integer, nullable=True)        # request_id или user_id (для registration)
    lang = Column(String, default="ru")
    scheduled_at = Column(DateTime, nullable=False)   # когда уведомление можно отправить
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())