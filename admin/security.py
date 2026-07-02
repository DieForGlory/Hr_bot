# admin/security.py
import hashlib
import hmac
import os

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from bot.utils.db_api import get_user_by_id

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2 ** 14, 8, 1
SALT_LEN = 16


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_LEN)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        algo, n, r, p, salt_hex, hash_hex = stored.split("$")
        if algo != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(dk, expected)
    except (ValueError, TypeError):
        return False


async def resolve_admin_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = await get_user_by_id(user_id)
    if not user or user.role != "hr" or not user.is_active:
        request.session.clear()
        return None
    return user


async def require_admin_page(request: Request):
    """Для HTML-страниц: нет сессии -> редирект на форму входа."""
    user = await resolve_admin_user(request)
    if not user:
        raise AdminAuthRedirect()
    return user


async def require_admin_api(request: Request):
    """Для JSON-эндпоинтов: нет сессии -> 401, плюс лёгкая CSRF-защита по заголовку."""
    if request.headers.get("x-requested-with") != "fetch":
        raise HTTPException(status_code=403, detail="missing_csrf_header")
    user = await resolve_admin_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="not_authenticated")
    return user


class AdminAuthRedirect(StarletteHTTPException):
    def __init__(self):
        super().__init__(status_code=307, detail="not_authenticated")


def install_auth_redirect_handler(app):
    @app.exception_handler(AdminAuthRedirect)
    async def _handler(request: Request, exc: AdminAuthRedirect):
        return RedirectResponse(url="/admin/login", status_code=302)
