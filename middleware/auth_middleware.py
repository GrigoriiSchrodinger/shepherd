from typing import Awaitable, Callable, Dict, Any
from aiogram import types
from database.user_repository import UserRepository
from config import logger
from datetime import datetime
from text import *

class AuthMiddleware:
    def __init__(self):
        self.user_repo = UserRepository()

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        username = user.username or "no_username"
        command = event.text or "no_command"

        log_context = {
            "user_id": user.id,
            "username": username,
            "command": command,
            "chat_type": event.chat.type,
            "message_id": event.message_id,
            "timestamp": event.date.isoformat()
        }

        # === Проверка наличия username ===
        if not user.username:
            logger.warning("Access attempt without username", extra={"context": log_context})
            await event.answer(AUTH_NO_USERNAME)
            return

        # === Проверка, есть ли пользователь в БД ===
        if not self.user_repo.user_exists(user.username):
            logger.warning("Unauthorized access attempt", extra={"context": log_context})
            await event.answer(AUTH_NOT_REGISTERED)
            return

        # === Проверка срока доступа ===
        user_data = self.user_repo.get_user(user.username)
        access_until = user_data.get("access_until", "01.01.2000")

        try:
            access_date = datetime.strptime(access_until, "%d.%m.%Y").date()
        except ValueError:
            access_date = datetime(2000, 1, 1).date()  # fallback

        today = datetime.today().date()

        if access_date < today:
            logger.warning(
                f"Access denied — expired ({access_until})",
                extra={"context": log_context}
            )
            await event.answer(AUTH_ACCESS_EXPIRED)
            return

        # === Всё ок — продолжаем ===
        logger.info("Successful access", extra={"context": log_context})
        return await handler(event, data)