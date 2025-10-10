from datetime import datetime, timedelta

from aiogram import Dispatcher, types, Bot
from aiogram.filters import Command

from config import logger, DATE_FORMAT, DEFAULT_CATEGORY
from feature.excel import MpstatsExcelReport

# === Интеграция с Telegram ===
report_generator = MpstatsExcelReport()


async def products_command(message: types.Message, bot: Bot) -> None:
    """Команда Telegram /products — генерация отчёта."""
    try:
        now = datetime.now()
        end_date = (now - timedelta(days=1)).strftime(DATE_FORMAT)
        start_date = (now - timedelta(days=30)).strftime(DATE_FORMAT)
        category = DEFAULT_CATEGORY

        processing_msg = await message.answer("⏳ Формируем отчёт...")
        excel_file = await report_generator.generate(start_date, end_date, category)

        caption = (
            "📊 Отчёт по товарам\n\n"
            f"📅 Период: {start_date} — {end_date}\n"
            f"🏷 Категория: {category}"
        )

        await message.answer_document(
            types.BufferedInputFile(
                file=excel_file.getvalue(),
                filename=f"WB_report_{datetime.now().strftime('%d.%m.%Y')}.xlsx"
            ),
            caption=caption
        )

        await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)

    except Exception as e:
        logger.error(f"Ошибка команды /products: {e}")
        await message.answer(f"❌ Ошибка: {e}")


def setup(dp: Dispatcher) -> None:
    """Регистрация команды в aiogram."""
    dp.message.register(products_command, Command("products"))
    logger.info("✅ Команда /products зарегистрирована")
