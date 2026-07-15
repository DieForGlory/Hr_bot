# bot/utils/notify_window.py
"""Окно отправки уведомлений админам/согласующим лицам (п.5 ТЗ).

Все уведомления руководителям / HR / бухгалтерии отправляются только в рабочее
окно 08:00–19:00 с понедельника по пятницу. Если действие пользователя произошло
вне окна — уведомление кладётся в очередь (таблица notification_queue) с
scheduled_at = начало следующего рабочего окна и отправляется планировщиком
(flush_due_notifications), когда окно открывается.

Уведомления самому сотруднику (согласовано/отклонено/справка готова) НЕ проходят
через это окно — они отправляются сразу.
"""
from datetime import datetime, timedelta

from sqlalchemy import update
from sqlalchemy.future import select

from db.database import async_session
from db.models import NotificationQueue
from bot.utils.notify import safe_notify
from core.logging_config import action_logger

WORK_START_HOUR = 8   # с 08:00 включительно
WORK_END_HOUR = 19    # до 19:00 (19:00 ровно — уже вне окна)


def is_within_work_window(dt: datetime) -> bool:
    return dt.weekday() < 5 and WORK_START_HOUR <= dt.hour < WORK_END_HOUR


def next_window_start(dt: datetime) -> datetime:
    """Ближайший момент внутри рабочего окна, не раньше dt."""
    if dt.hour < WORK_START_HOUR:
        candidate = dt.replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
    elif dt.hour >= WORK_END_HOUR:
        candidate = (dt + timedelta(days=1)).replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
    else:
        # то же время суток внутри рабочих часов, но день нерабочий (сб/вс) — сдвинем на 08:00
        candidate = dt.replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
    while candidate.weekday() >= 5:  # суббота/воскресенье
        candidate = (candidate + timedelta(days=1)).replace(hour=WORK_START_HOUR, minute=0, second=0, microsecond=0)
    return candidate


def build_keyboard(kb_kind: str | None, kb_ref_id: int | None, lang: str):
    if not kb_kind or kb_ref_id is None:
        return None
    from bot.keyboards.inline import get_approval_keyboard, get_cert_status_keyboard
    if kb_kind == "approval":
        return get_approval_keyboard(kb_ref_id, lang)
    if kb_kind == "cert":
        return get_cert_status_keyboard(kb_ref_id, lang)
    if kb_kind == "registration":
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from bot.locales.texts import get_text
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("reg_approve_button", lang), callback_data=f"reg_approve_{kb_ref_id}")],
            [InlineKeyboardButton(text=get_text("reg_reject_button", lang), callback_data=f"reg_reject_{kb_ref_id}")],
        ])
    if kb_kind == "hr_reply":
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from bot.locales.texts import get_text
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("hr_reply_button", lang), callback_data=f"hr_reply_{kb_ref_id}")],
        ])
    return None


async def _send_now(bot, chat_id, text, lang, kb_kind, kb_ref_id, attachment, context):
    kb = build_keyboard(kb_kind, kb_ref_id, lang)
    kind = (attachment or {}).get("kind")
    file_id = (attachment or {}).get("file_id")

    if kind == "photo" and file_id:
        await safe_notify(bot.send_photo(chat_id, file_id, caption=text, reply_markup=kb), context=context)
        return
    if kind == "document" and file_id:
        # документ отдельным сообщением, затем текст с клавиатурой согласования
        await safe_notify(bot.send_document(chat_id, file_id), context=context + " doc")
    await safe_notify(bot.send_message(chat_id, text, reply_markup=kb), context=context)


async def _enqueue(chat_id, text, lang, kb_kind, kb_ref_id, attachment, when: datetime):
    async with async_session() as session:
        session.add(NotificationQueue(
            chat_id=chat_id,
            text=text,
            attachment_kind=(attachment or {}).get("kind"),
            attachment_file_id=(attachment or {}).get("file_id"),
            kb_kind=kb_kind,
            kb_ref_id=kb_ref_id,
            lang=lang,
            scheduled_at=when,
            sent=False,
        ))
        await session.commit()


async def dispatch_notification(bot, chat_id, text, lang="ru", kb_kind=None, kb_ref_id=None,
                                attachment=None, context=""):
    """Отправить уведомление согласующему/админу сразу (если в рабочем окне) либо
    поставить в очередь до начала следующего рабочего окна (п.5 ТЗ)."""
    if not chat_id:
        return
    now = datetime.now()
    if is_within_work_window(now):
        await _send_now(bot, chat_id, text, lang, kb_kind, kb_ref_id, attachment, context)
    else:
        when = next_window_start(now)
        await _enqueue(chat_id, text, lang, kb_kind, kb_ref_id, attachment, when)
        action_logger.info("notification_queued chat_id=%s scheduled_at=%s context=%s", chat_id, when, context)


async def flush_due_notifications(bot):
    """Отправляет накопленные уведомления, у которых наступило время (scheduled_at <= now).
    Запускается планировщиком раз в несколько минут."""
    now = datetime.now()
    async with async_session() as session:
        due = (await session.execute(
            select(NotificationQueue).where(
                NotificationQueue.sent == False,  # noqa: E712
                NotificationQueue.scheduled_at <= now,
            ).order_by(NotificationQueue.id)
        )).scalars().all()

    for item in due:
        attachment = None
        if item.attachment_kind and item.attachment_file_id:
            attachment = {"kind": item.attachment_kind, "file_id": item.attachment_file_id}
        await _send_now(
            bot, item.chat_id, item.text, item.lang, item.kb_kind, item.kb_ref_id,
            attachment, context=f"flush_notification id={item.id}"
        )
        async with async_session() as session:
            await session.execute(
                update(NotificationQueue).where(NotificationQueue.id == item.id).values(sent=True)
            )
            await session.commit()

    if due:
        action_logger.info("notifications_flushed count=%s", len(due))
