from datetime import datetime, timedelta
from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import database, logger
from middleware.permissions import rights_required
from utils.formatters import format_revenue, escape_md


# === /info ===
@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def info_command(message: types.Message):
    args = message.text.split(maxsplit=1)
    target_username = args[1] if len(args) > 1 else message.from_user.username or "unknown_user"
    current_user = message.from_user.username or "unknown_user"

    if not database.user_exists(target_username):
        await message.answer(f"❌ Пользователь `{escape_md(target_username)}` не найден в базе данных.", parse_mode="Markdown")
        return

    user_data = database.get_user(target_username)
    if not user_data:
        await message.answer(f"❌ Не удалось получить данные для `{escape_md(target_username)}`.", parse_mode="Markdown")
        return

    # Если moder — можно смотреть только свои данные
    display_name = "себя" if target_username == current_user else f"`{escape_md(target_username)}`"
    is_self = (target_username == current_user)

    rights = escape_md(user_data.get('rights'))
    category = escape_md(user_data.get('category'))

    # === Расчет дат ===
    today = datetime.today().date()
    dates_count = user_data.get('dates', 0)
    end_date = today - timedelta(days=1)
    start_date = end_date - timedelta(days=dates_count - 1) if dates_count > 0 else end_date
    dates_text = (
        f"{dates_count} дней (с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')})"
        if dates_count > 0 else "нет установленного периода"
    )

    # === Формируем текст ===
    info_text = (
        f"ℹ️ Информация о пользователе {display_name}:\n\n"
    )
    if rights == "root"  or not is_self:
        info_text += f"Права: {rights}\n"

    info_text += (
        f"Даты: {dates_text}\n"
        f"Максимум дней оборота: {user_data.get('turnover_days_max')}\n"
        f"Минимальная выручка: {format_revenue(user_data.get('revenue_min'))}\n"
        f"Категория: {category}"
    )

    # === Формируем кнопки ===
    user_rights = database.get_user(current_user).get("rights", "user")
    kb = InlineKeyboardBuilder()

    # Root видит все
    if user_rights == "root":
        for param, label in [
            ("rights", "🛠 Права"),
            ("turnover_days_max", "📈 Оборот"),
            ("revenue_min", "💰 Выручка"),
            ("category", "🏷 Категория"),
            ("dates", "📅 Даты"),
        ]:
            kb.button(text=label, callback_data=f"edit:{param}:{target_username}")

    # Admin видит всё, кроме прав
    elif user_rights == "admin":
        for param, label in [
            ("turnover_days_max", "📈 Оборот"),
            ("revenue_min", "💰 Выручка"),
            ("category", "🏷 Категория"),
            ("dates", "📅 Даты"),
        ]:
            kb.button(text=label, callback_data=f"edit:{param}:{target_username}")

    # Moder может редактировать только свои данные
    elif user_rights == "moder" and is_self:
        for param, label in [
            ("turnover_days_max", "📈 Оборот"),
            ("revenue_min", "💰 Выручка"),
            ("category", "🏷 Категория"),
            ("dates", "📅 Даты"),
        ]:
            kb.button(text=label, callback_data=f"edit:{param}:{target_username}")

    kb.adjust(2)

    await message.answer(
        info_text,
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

    logger.info(f"{current_user} запросил информацию для {target_username}")


# === Регистрация ===
def setup_info(dp: Dispatcher) -> None:
    dp.message.register(info_command, Command("info"))
    logger.info("✅ Команда /info зарегистрирована")
