from aiogram import Dispatcher, types, Bot
from aiogram.filters import Command
from config import logger, database
from feature.mpstats.reports_builder import ProductReportService
from middleware.permissions import rights_required

report_service = ProductReportService(database)


@rights_required(["root", "admin", "moder", "user"])
async def products_command(message: types.Message, bot: Bot) -> None:
    username = message.from_user.username or "unknown_user"
    logger.info(f"Команда /products от {username}")

    processing_msg = await message.answer("⏳ Формируем отчёт...")

    report_data = await report_service.generate_user_report(username)

    if not report_data:
        await message.answer("❌ Не удалось сформировать отчёт. Проверьте настройки пользователя.")
        await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
        return

    excel_bytes, caption, filename = report_data

    await message.answer_document(
        types.BufferedInputFile(file=excel_bytes, filename=filename),
        caption=caption
    )

    await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)


def setup(dp: Dispatcher) -> None:
    dp.message.register(products_command, Command("products"))
    logger.info("✅ Команда /products зарегистрирована")
