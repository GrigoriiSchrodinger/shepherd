import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import TELEGRAM_BOT_TOKEN
from middleware.auth_middleware import AuthMiddleware
import handlers

async def main() -> None:
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.message.middleware.register(AuthMiddleware())
    handlers.setup(dp)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
