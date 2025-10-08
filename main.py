import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import TELEGRAM_BOT_TOKEN
import handlers
import database  # Добавляем импорт

async def main() -> None:
    database.init_db()  # Инициализация БД
    
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    handlers.setup(dp)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
