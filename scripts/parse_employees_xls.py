# -*- coding: utf-8 -*-
"""Парсинг кадрового Excel (штатное расписание) -> employees_seed.json
+ отчёт по маппингу подразделений на COMPANY_STRUCTURE.

Использование:
    python scripts/parse_employees_xls.py <путь_к_Шр.xls> [data/employees_seed.json]

ВНИМАНИЕ: и исходный Excel, и результат содержат персональные данные сотрудников
(ФИО, даты рождения, кадровое состояние) — в репозитории они НЕ хранятся.
Результат кладётся в ./data (том рядом с БД, см. seed_employees в db/database.py).
"""
import xlrd, json, re, sys, difflib, io, os

# Копия COMPANY_STRUCTURE (bot/utils/constants.py)
COMPANY_STRUCTURE = [
    "1. Руководство",
    "1.1 Отдел по административным вопросам",
    "1.2 Отдел административного управления",
    "2. Юридический отдел",
    "3. Отдел клиентского обслуживания",
    "4. Управление земельных отношений и разрешительной документации",
    "4.1 Отдел земельных отношений и кадастра",
    "4.2 Отдел разрешительной документации",
    "5. Финансовый департамент",
    "5.1 Управление бухгалтерского учета и отчетности",
    "5.1.1 Отдел взаиморасчетов",
    "5.1.2 Отдел операционного учета",
    "5.1.3 Отдел реализации",
    "5.1.4 Отдел расчета заработной платы",
    "5.2 Планово - экономический отдел",
    "5.2.1 Группа экономической аналитики",
    "5.2.2 Группа казначейства",
    "6. Административный департамент",
    "6.1 Административно – хозяйственный отдел",
    "6.2 Отдел технической поддержки и системного администрирования",
    "7. Коммерческий департамент",
    "7.1 Управление продаж",
    "7.1.1 Отдел продаж",
    "Группа №1",
    "7.1.2 Отдел продаж коммерческой недвижимости",
    "7.1.3 Отдел телефонных продаж",
    "7.2 Отдел ипотеки и специальных программ",
    "7.3 Отдел по работе с дебиторской задолженностью",
    "7.4 Отдел оформления",
    "7.5 Отдел развития стратегических программ",
    "7.6 Отдел аналитики и развития",
    "7.6.1 Группа аналитики",
    "7.7 Управление маркетинга и рекламы",
    "7.7.1 Отдел digital-маркетинга",
    "8. Департамент клиентского сервиса",
    "8.1 Отдел передачи и клиентского сопровождения",
    "8.2 Отдел гарантийного ремонта",
    "9. Департамент технического заказчика",
    "9.1 Управление инженерных сетей",
    "9.2 Отдел охраны труда и техники безопасности",
    "9.3 Отдел технического надзора",
    "9.4 Производственно технический отдел",
    "9.4.1 Сметно - договорная группа",
    "10. Управление проектами",
    "10.1 Отдел планирования и отчетности",
    "10.2 Отдел главных инженеров проектов",
    "10.3 Отдел архитектуры и дизайна",
    "11. Департамент по работе с персоналом и организационному развитию",
    "11.1 Отдел кадрового администрирования",
    "11.2 Отдел по работе с персоналом",
    "12. Департамент по безопасности",
    "12.1 Отдел технических средств охраны по обеспечению защиты имущества",
]

_NUM_PREFIX = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+")

def strip_number(name: str) -> str:
    return _NUM_PREFIX.sub("", name).strip()

def norm(s: str) -> str:
    s = strip_number(s)
    s = s.lower()
    s = s.replace("ё", "е")
    # унифицируем тире/дефисы и пробелы вокруг них
    s = re.sub(r"[\-‐‑‒–—―]", "-", s)
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# индекс нормализованных имён COMPANY_STRUCTURE
CS_NORM = {norm(x): x for x in COMPANY_STRUCTURE}
CS_NORM_KEYS = list(CS_NORM.keys())

def match_department(excel_name: str):
    n = norm(excel_name)
    if n in CS_NORM:
        return CS_NORM[n], "exact"
    # fuzzy
    cand = difflib.get_close_matches(n, CS_NORM_KEYS, n=1, cutoff=0.82)
    if cand:
        return CS_NORM[cand[0]], f"fuzzy({difflib.SequenceMatcher(None,n,cand[0]).ratio():.2f})"
    return None, "NO_MATCH"

STATUS_VALUES = {"Руководитель", "Сотрудник"}

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    xls_path = sys.argv[1]
    if not os.path.exists(xls_path):
        print(f"Файл не найден: {xls_path}")
        sys.exit(1)

    wb = xlrd.open_workbook(xls_path)
    sh = wb.sheet_by_index(0)

    rows = []
    for r in range(sh.nrows):
        rows.append([sh.cell_value(r, c) for c in range(sh.ncols)])

    # строка 0 — заголовок таблицы
    header = rows[0]
    data = rows[1:]

    employees = []
    current_dept_raw = None
    for raw in data:
        a, b, c, d, e, f, g = (list(raw) + [""] * 7)[:7]
        # a может быть float (номер сотрудника) или str (заголовок подразделения)
        is_number = isinstance(a, float) or (isinstance(a, str) and re.match(r"^\d+(\.\d+)?$", a.strip()))
        name = (c or "").strip() if isinstance(c, str) else str(c).strip()
        if not is_number:
            # заголовок подразделения (в колонке A текст)
            dept = (a or "").strip() if isinstance(a, str) else ""
            if dept:
                current_dept_raw = dept
            continue
        # строка сотрудника
        if not name:
            # пустое ФИО — пропускаем (ошибочная строка)
            continue
        position = (b or "").strip() if isinstance(b, str) else str(b).strip()
        manager = (d or "").strip() if isinstance(d, str) else str(d).strip()
        status = (e or "").strip() if isinstance(e, str) else str(e).strip()
        birth = f
        if isinstance(birth, float):
            # иногда даты как числа Excel — приведём
            try:
                y, m, dd, *_ = xlrd.xldate_as_tuple(birth, wb.datemode)
                birth = f"{dd:02d}.{m:02d}.{y:04d}"
            except Exception:
                birth = ""
        birth = (birth or "").strip() if isinstance(birth, str) else str(birth).strip()
        state = (g or "").strip() if isinstance(g, str) else str(g).strip()

        employees.append({
            "full_name": name,
            "position": position,
            "manager_name": manager,
            "status_raw": status,
            "birth_date": birth,
            "work_state": state,
            "department_raw": current_dept_raw,
        })

    # множество всех ФИО (для определения кто является руководителем и валидации manager)
    all_names = {e["full_name"] for e in employees}
    manager_names = {e["manager_name"] for e in employees if e["manager_name"]}

    # маппинг подразделений
    dept_raws = sorted({e["department_raw"] for e in employees if e["department_raw"]})
    dept_map = {}
    unmatched = []
    for draw in dept_raws:
        matched, how = match_department(draw)
        dept_map[draw] = matched
        if matched is None:
            unmatched.append(draw)
        # печать отчёта
        print(f"[{how:12}] {draw!r:70} -> {matched!r}")

    print("\n=== UNMATCHED DEPARTMENTS ===")
    for u in unmatched:
        print("  ", repr(u))

    # роль
    def role_of(e):
        if e["status_raw"] == "Руководитель":
            return "manager"
        if e["status_raw"] == "Сотрудник":
            return "employee"
        # грязная ячейка статуса: если человек кому-то руководитель -> manager
        return "manager" if e["full_name"] in manager_names else "employee"

    # менеджеры, которых нет среди сотрудников (ФИО из колонки D не совпало)
    missing_managers = sorted({m for m in manager_names if m not in all_names})

    out = []
    for e in employees:
        dep_full = dept_map.get(e["department_raw"])
        out.append({
            "full_name": e["full_name"],
            "position": e["position"],
            "department": dep_full,           # полное имя из COMPANY_STRUCTURE (с номером) или null
            "department_raw": e["department_raw"],
            "manager_name": e["manager_name"] or None,
            "role": role_of(e),
            "birth_date": e["birth_date"] or None,
            "work_state": e["work_state"] or None,
        })

    print(f"\nВсего сотрудников: {len(out)}")
    print(f"Уникальных ФИО: {len(all_names)}")
    print(f"Строк без сопоставленного подразделения: {sum(1 for x in out if not x['department'])}")
    print(f"\n=== MANAGER NAMES НЕ НАЙДЕННЫЕ СРЕДИ СОТРУДНИКОВ ({len(missing_managers)}) ===")
    for m in missing_managers:
        print("  ", repr(m))

    # дубликаты ФИО
    from collections import Counter
    dups = [n for n, cnt in Counter(e["full_name"] for e in out).items() if cnt > 1]
    print(f"\n=== ДУБЛИКАТЫ ФИО ({len(dups)}) ===")
    for dname in dups:
        print("  ", repr(dname))

    outpath = sys.argv[2] if len(sys.argv) > 2 else os.path.join("data", "employees_seed.json")
    os.makedirs(os.path.dirname(outpath) or ".", exist_ok=True)
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"\nЗаписано: {outpath}")

if __name__ == "__main__":
    # UTF-8 stdout
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
