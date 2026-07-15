# bot/utils/vacation_balance.py
"""Расчёт остатка отпускных дней по алгоритму кадрового Excel (п.3 ТЗ).

Логика отражает переход в трудовом законодательстве: до 30.04.2023 отпуск
начислялся в РАБОЧИХ днях (1.25 дня за месяц стажа), с 01.05.2023 — в
КАЛЕНДАРНЫХ днях (1.75 дня за месяц). Поэтому остаток состоит из двух «корзин»:

    1-й период (рабочие дни):   начислено = мес1 × 1.25, остаток = начислено − потрачено_раб
    2-й период (календарные):   начислено = мес2 × 1.75, остаток = начислено − потрачено_кал

где мес = DATEDIF(старт, конец, "M") + (1, если остаток дней "MD" > 15).

Также считается доп. надбавка за стаж: +2 дня за каждые полные 5 лет работы
(колонка M: ЦЕЛОЕ(лет_стажа / 5) × 2).
"""
from dataclasses import dataclass
from datetime import date, datetime

PERIOD1_END = date(2023, 4, 30)     # X1 — конец периода начисления в рабочих днях
PERIOD2_START = date(2023, 5, 1)    # Y1 — начало периода начисления в календарных днях
RATE_WORK = 1.25                    # Z1 — рабочих дней за месяц (1-й период)
RATE_CALENDAR = 1.75                # AA1 — календарных дней за месяц (2-й период)


def _datedif_m_md(start: date, end: date) -> tuple[int, int]:
    """Аналог Excel DATEDIF(start,end,"M") и DATEDIF(start,end,"MD")."""
    if end <= start:
        return 0, 0
    # полные месяцы ("M")
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    # остаток дней ("MD") — разница дней без учёта месяцев/лет
    if end.day >= start.day:
        md = end.day - start.day
    else:
        # дни в предыдущем относительно end месяце
        prev_month = end.month - 1 or 12
        prev_year = end.year if end.month > 1 else end.year - 1
        # количество дней в предыдущем месяце
        if prev_month == 12:
            days_in_prev = 31
        else:
            first_next = date(prev_year + (prev_month // 12), (prev_month % 12) + 1, 1)
            days_in_prev = (first_next - date(prev_year, prev_month, 1)).days
        md = end.day + days_in_prev - start.day
    return max(months, 0), max(md, 0)


def _months_rounded(start: date, end: date) -> int:
    """Число месяцев с округлением вверх, если остаток дней > 15 (как в Excel)."""
    months, md = _datedif_m_md(start, end)
    return months + (1 if md > 15 else 0)


def _full_years(start: date, end: date) -> int:
    if end <= start:
        return 0
    years = end.year - start.year
    if (end.month, end.day) < (start.month, start.day):
        years -= 1
    return max(years, 0)


@dataclass
class VacationBalance:
    accrued_work: float        # P — начислено рабочих дней (1-й период)
    used_work: float           # S — потрачено рабочих дней
    remaining_work: float      # U — остаток рабочих дней
    accrued_calendar: float    # R — начислено календарных дней (2-й период)
    used_calendar: float       # T — потрачено календарных дней
    remaining_calendar: float  # V — остаток календарных дней
    tenure_bonus: float        # M — доп. дни за стаж (+2 за каждые 5 лет)
    total_remaining: float     # U + V (суммарный остаток дней)


def compute_vacation_balance(hire_date: date, used_work: float = 0.0,
                             used_calendar: float = 0.0, today: date | None = None) -> VacationBalance:
    """Считает остаток отпускных по алгоритму Excel.

    hire_date — дата приёма; used_work/used_calendar — уже потраченные дни
    (рабочие/календарные); today — точка расчёта (по умолчанию сегодня)."""
    if today is None:
        today = date.today()

    used_work = used_work or 0.0
    used_calendar = used_calendar or 0.0

    # 1-й период: от даты приёма до 30.04.2023 (только если принят до этой даты)
    months1 = _months_rounded(hire_date, PERIOD1_END) if hire_date < PERIOD1_END else 0
    accrued_work = round(months1 * RATE_WORK, 2)

    # 2-й период: от max(приём, 01.05.2023) до сегодня
    period2_start = hire_date if hire_date > PERIOD2_START else PERIOD2_START
    months2 = _months_rounded(period2_start, today)
    accrued_calendar = round(months2 * RATE_CALENDAR, 2)

    remaining_work = round(accrued_work - used_work, 2)
    remaining_calendar = round(accrued_calendar - used_calendar, 2)

    tenure_bonus = (_full_years(hire_date, today) // 5) * 2

    return VacationBalance(
        accrued_work=accrued_work,
        used_work=round(used_work, 2),
        remaining_work=remaining_work,
        accrued_calendar=accrued_calendar,
        used_calendar=round(used_calendar, 2),
        remaining_calendar=remaining_calendar,
        tenure_bonus=float(tenure_bonus),
        total_remaining=round(remaining_work + remaining_calendar, 2),
    )


def parse_hire_date(value) -> date | None:
    """Парсит дату приёма из строки 'dd.mm.yyyy' (или date/datetime)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def balance_for_user(user, today: date | None = None) -> VacationBalance | None:
    """Остаток отпускных для пользователя. None — если не задана дата приёма."""
    hire = parse_hire_date(getattr(user, "hire_date", None))
    if hire is None:
        return None
    return compute_vacation_balance(
        hire,
        used_work=getattr(user, "used_work_days", 0) or 0.0,
        used_calendar=getattr(user, "used_calendar_days", 0) or 0.0,
        today=today,
    )
