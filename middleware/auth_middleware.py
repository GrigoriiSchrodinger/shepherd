from typing import Awaitable, Callable, Dict, Any
from aiogram import types
from database.user_repository import UserRepository
from config import logger  # Импортируем настроенный логгер

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
        user_id = user.id
        username = user.username or "no_username"
        command = event.text or "no_command"

        log_context = {
            "user_id": user_id,
            "username": username,
            "command": command,
            "chat_type": event.chat.type,
            "message_id": event.message_id,
            "timestamp": event.date.isoformat()
        }

        if not user.username:
            logger.warning(
                "Access attempt without username", 
                extra={"context": log_context}
            )
            await event.answer("❌ Для использования бота требуется Telegram username")
            return

        if not self.user_repo.user_exists(user.username):
            logger.warning(
                "Unauthorized access attempt",
                extra={"context": log_context}
            )
            await event.answer("🔒 Доступ запрещён. Ваш username не зарегистрирован")
            return

        logger.info(
            "Successful access", 
            extra={"context": log_context}
        )
        return await handler(event, data)