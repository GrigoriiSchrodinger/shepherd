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

if __name__ == "__main__":
    asyncio.run(main())
