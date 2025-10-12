from datetime import datetime, timedelta

from aiogram import Dispatcher, types, Bot
from aiogram.filters import Command

from api.mpstats_api import MpstatsAPI
from config import logger, database, MAX_TOTAL_PRODUCTS, DATE_FORMAT
from feature.mpstats.reports_builder import ProductReportService
from middleware.permissions import rights_required

report_service = ProductReportService(database)


@rights_required(["root", "admin", "moder", "user"])
async def products_command(message: types.Message, bot: Bot) -> None:
    username = message.from_user.username or "unknown_user"
    logger.info(f"Команда /products от {username}")

    processing_msg = await message.answer("⏳ Формируем отчёт...")

    user_data = database.get_user(username)
    if not user_data:
        logger.warning(f"Пользователь {username} не найден в БД")
        return None

    days = user_data["dates"]
    category = user_data["category"]
    turnover_days_max = user_data["turnover_days_max"]
    revenue_min = user_data["revenue_min"]
    now = datetime.now()
    end_date = (now - timedelta(days=1)).strftime(DATE_FORMAT)
    start_date = (now - timedelta(days=days)).strftime(DATE_FORMAT)

    category_count = await MpstatsAPI().get_category_total(
        start_date, end_date, category, revenue_min, turnover_days_max
    )

    if category_count > MAX_TOTAL_PRODUCTS:
        await message.answer(f"Превышены лимиты, товаров в запросе - {category_count}.\nИзмени параметры запроса либо сузь категорию")
        await bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
        return

    report_data = await report_service.generate_user_report(username)

    if not report_data:
        await message.answer("❌ Не удалось сформировать отчёт")
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
