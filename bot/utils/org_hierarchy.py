# bot/utils/org_hierarchy.py
"""
Разбор оргструктуры (bot/utils/constants.py::COMPANY_STRUCTURE) в дерево подразделений,
чтобы автоматически определять руководителя сотрудника по месту работы.

Правила (согласовано с пользователем):
- Рядовой сотрудник отдела -> руководитель = руководитель ЭТОГО ЖЕ подразделения.
- Руководитель подразделения -> руководитель = руководитель РОДИТЕЛЬСКОГО подразделения
  (вычисляется по номеру пункта: "5.1.4" -> родитель "5.1" -> родитель "5").
- Руководитель подразделения верхнего уровня (без номера-родителя, например
  "5. Финансовый департамент") -> руководитель = руководитель CEO_DEPARTMENT.
- Руководитель самого CEO_DEPARTMENT ("1. Руководство") -> руководителя нет (вершина иерархии).
- Пункты без номера (например "Группа №1" в списке) считаются дочерними по отношению
  к ближайшему предыдущему пункту в списке.
"""
import re
from bot.utils.constants import COMPANY_STRUCTURE

CEO_DEPARTMENT = "1. Руководство"

_NUMBER_PREFIX_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+")


def _department_depth(name: str) -> int:
    match = _NUMBER_PREFIX_RE.match(name)
    if not match:
        return 0
    return len(match.group(1).split("."))


def _build_parent_map() -> dict:
    parent_map = {}
    stack = []  # stack[i] = название подразделения на глубине i+1
    prev_depth = 0

    for name in COMPANY_STRUCTURE:
        depth = _department_depth(name)
        if depth == 0:
            # Пункт без номера (например "Группа №1") — считаем дочерним предыдущему
            depth = prev_depth + 1

        parent_map[name] = stack[depth - 2] if depth >= 2 and len(stack) >= depth - 1 else None

        stack = stack[:depth - 1]
        stack.append(name)
        prev_depth = depth

    return parent_map


_PARENT_MAP = _build_parent_map()


def get_parent_department(department: str) -> str | None:
    return _PARENT_MAP.get(department)


def get_manager_department(department: str, is_manager_role: bool) -> str | None:
    """Возвращает название подразделения, в котором нужно искать руководителя
    для сотрудника с данным местом работы и ролью. None — руководителя нет
    (вершина иерархии, например сам CEO_DEPARTMENT)."""
    if department not in _PARENT_MAP:
        return None

    if not is_manager_role:
        return department

    if department == CEO_DEPARTMENT:
        return None

    parent = get_parent_department(department)
    return parent if parent is not None else CEO_DEPARTMENT
