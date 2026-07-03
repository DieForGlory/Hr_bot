# admin/gateway_auth.py
"""
Авторизация админки через gateway (auth-service).

Собственный логин админки удалён: доступ в закрытый контур даёт auth_request на
шлюзе (только пользователи с ролью в сервисе hr_bot), а шлюз прокидывает личность
в заголовках X-User-*. Здесь мы их читаем и проверяем гранулярные разрешения.

Заголовки от шлюза:
  X-User-Id, X-User-Name, X-User-Full-Name (base64),
  X-User-Service-Roles, X-User-Service-Permissions (csv), X-User-Admin.
"""
import base64
from dataclasses import dataclass, field
from typing import List, Optional

from fastapi import Request, HTTPException


@dataclass
class GatewayUser:
    user_id: str
    username: str
    full_name: str
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    is_admin: bool = False

    def has_permission(self, permission: str) -> bool:
        # Системный админ auth-service — полный доступ.
        if self.is_admin:
            return True
        if permission in self.permissions:
            return True
        # Wildcard: "hr_bot.*" покрывает "hr_bot.users.view".
        for p in self.permissions:
            if p.endswith(".*") and permission.startswith(p[:-1]):
                return True
        return False


def _b64(value: str) -> str:
    try:
        return base64.b64decode(value).decode("utf-8")
    except Exception:
        return value


def get_gateway_user(request: Request) -> Optional[GatewayUser]:
    h = request.headers
    user_id = h.get("X-User-Id")
    username = h.get("X-User-Name")
    if not user_id or not username:
        return None
    return GatewayUser(
        user_id=user_id,
        username=username,
        full_name=_b64(h.get("X-User-Full-Name", "")) or username,
        roles=[r.strip() for r in h.get("X-User-Service-Roles", "").split(",") if r.strip()],
        permissions=[p.strip() for p in h.get("X-User-Service-Permissions", "").split(",") if p.strip()],
        is_admin=h.get("X-User-Admin", "false").lower() == "true",
    )


async def current_user(request: Request) -> GatewayUser:
    """FastAPI-зависимость: пользователь из заголовков шлюза.
    401 если заголовков нет (прямой доступ в обход шлюза)."""
    user = get_gateway_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="not_authenticated")
    return user


def require_permission(permission: str):
    """Фабрика FastAPI-зависимости: требует конкретное разрешение сервиса hr_bot.
    Использование: current_user=Depends(require_permission("hr_bot.users.view"))."""
    async def _dep(request: Request) -> GatewayUser:
        user = get_gateway_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="not_authenticated")
        if not user.has_permission(permission):
            raise HTTPException(status_code=403, detail=f"permission_denied:{permission}")
        return user
    return _dep
