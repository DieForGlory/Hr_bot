
from sqlalchemy.future import select
from sqlalchemy import update
from db.database import async_session
from db.models import User, Request
from db.database import async_session
from sqlalchemy.future import select
from sqlalchemy import insert, update
from db.models import FAQ
from sqlalchemy import select, and_, extract
from db.models import CalendarDay

async def get_request_by_id(req_id: int):
    async with async_session() as session:
        result = await session.execute(select(Request).where(Request.id == req_id))
        return result.scalars().first()


async def create_pending_user(data: dict) -> int:
    async with async_session() as session:
        # Установка системных прав на основе выбранного статуса
        sys_role = "manager" if data['role_text'] == "Руководитель" else "employee"

        new_user = User(
            telegram_id=data['telegram_id'],
            phone=data['phone'],
            full_name=data['full_name'],
            tg_username=data['tg_username'],
            department=data['subdivision'],  # Сохраняем выбранное подразделение
            position=data['role_text'],  # Сохраняем текстовый статус (Сотрудник/Руководитель)
            role=sys_role,  # Устанавливаем системную роль
            birth_date=data['birth_date'],
            car_info=data['car_info'],
            face_id_photo=data['face_id_photo'],
            approval_status="pending",
            is_active=False,
            language=data.get('language', 'ru'),
        )
        session.add(new_user)
        await session.commit()
        return new_user.id

async def update_user_approval(user_id: int, status: str):
    async with async_session() as session:
        is_active = True if status == "approved" else False
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(approval_status=status, is_active=is_active)
        )
        await session.commit()
async def update_request_status(req_id: int, status: str, hr_comment: str = None, manager_comment: str = None):
    from datetime import datetime

    async with async_session() as session:
        result = await session.execute(select(Request).where(Request.id == req_id))
        req = result.scalars().first()
        if not req:
            return
        previous_status = req.status

        values = {"status": status}
        if hr_comment:
            values["hr_comment"] = hr_comment
        if manager_comment:
            values["manager_comment"] = manager_comment

        if status == "manager_approved":
            values["manager_decided_at"] = datetime.now()
        elif status in ("hr_approved", "done"):
            values["hr_decided_at"] = datetime.now()
        elif status == "rejected":
            if previous_status == "pending":
                values["manager_decided_at"] = datetime.now()
            else:
                values["hr_decided_at"] = datetime.now()

        # Списываем баланс ровно один раз, при первом переходе в hr_approved
        if status == "hr_approved" and previous_status != "hr_approved" and req.type == "vacation_paid" and req.days_count:
            await session.execute(
                update(User)
                .where(User.id == req.user_id)
                .values(vacation_days_balance=User.vacation_days_balance - req.days_count)
            )

        await session.execute(update(Request).where(Request.id == req_id).values(**values))
        await session.commit()


async def attach_sick_leave_document(req_id: int, file_id: str):
    async with async_session() as session:
        await session.execute(update(Request).where(Request.id == req_id).values(file_path=file_id))
        await session.commit()


async def get_open_sick_leave_request(user_id: int):
    """Последний больничный сотрудника без прикреплённого документа."""
    async with async_session() as session:
        result = await session.execute(
            select(Request)
            .where(Request.user_id == user_id, Request.type == "sick_leave", Request.file_path.is_(None))
            .order_by(Request.id.desc())
        )
        return result.scalars().first()

async def get_user_by_id(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

async def get_users_by_role(role: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.role == role))
        return result.scalars().all()

async def get_user_by_phone(phone: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.phone.like(f"%{phone[-10:]}%")))
        return result.scalars().first()

async def update_user_telegram_id(user_id: int, telegram_id: int):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == user_id).values(telegram_id=telegram_id))
        await session.commit()

async def get_user_by_telegram_id(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalars().first()

async def create_request(user_id: int, req_type: str, start_date=None, end_date=None, comment=None, days_count=None):
    async with async_session() as session:
        new_req = Request(
            user_id=user_id,
            type=req_type,
            start_date=start_date,
            end_date=end_date,
            comment=comment,
            days_count=days_count
        )
        session.add(new_req)
        await session.commit()
        return new_req.id


async def calculate_actual_vacation_days(start_date, end_date) -> int:
    total_calendar_days = (end_date - start_date).days + 1

    async with async_session() as session:
        result = await session.execute(
            select(CalendarDay).where(
                and_(
                    CalendarDay.date >= start_date,
                    CalendarDay.date <= end_date,
                    CalendarDay.is_workday == False
                )
            )
        )
        holidays_count = len(result.scalars().all())

    # Исключение зафиксированных праздничных дней из общего количества дней отпуска
    return total_calendar_days - holidays_count

async def find_department_head(department: str):
    """Активный руководитель (role='manager') указанного подразделения, если такой уже есть."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.department == department,
                User.role == "manager",
                User.is_active == True,  # noqa: E712
                User.approval_status == "approved",
            ).order_by(User.id)
        )
        return result.scalars().first()


async def set_user_manager(user_id: int, manager_id):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == user_id).values(manager_id=manager_id))
        await session.commit()


async def resolve_manager_id(department: str, role: str):
    """Определяет руководителя сотрудника по оргструктуре (bot/utils/org_hierarchy.py).
    Возвращает id найденного руководителя или None, если подразделение не распознано,
    руководитель этого уровня ещё не зарегистрирован, либо это вершина иерархии."""
    from bot.utils.org_hierarchy import get_manager_department

    if not department:
        return None

    manager_department = get_manager_department(department, role == "manager")
    if not manager_department:
        return None

    head = await find_department_head(manager_department)
    return head.id if head else None


async def get_calendar_days_for_month(year: int, month: int):
    async with async_session() as session:
        result = await session.execute(
            select(CalendarDay)
            .where(
                extract("year", CalendarDay.date) == year,
                extract("month", CalendarDay.date) == month,
            )
            .order_by(CalendarDay.date)
        )
        return result.scalars().all()

async def get_all_faqs():
    async with async_session() as session:
        result = await session.execute(select(FAQ))
        return result.scalars().all()

async def get_faq_by_id(faq_id: int):
    async with async_session() as session:
        result = await session.execute(select(FAQ).where(FAQ.id == faq_id))
        return result.scalars().first()

async def get_user_requests(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Request).where(Request.user_id == user_id))
        return result.scalars().all()