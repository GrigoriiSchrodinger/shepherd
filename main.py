import asyncio
from aiogram import Dispatcher
from config import bot
from middleware.auth_middleware import AuthMiddleware
import handlers


async def main() -> None:
    dp = Dispatcher()
    dp.message.middleware.register(AuthMiddleware())
    handlers.setup(dp)

    await dp.start_polling(bot)

    # Если у тебя есть async-генерация отчетов, можно логировать прямо там
    # log_memory("После генерации отчета")

if __name__ == "__main__":
    asyncio.run(main())
