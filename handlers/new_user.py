# handlers/new_user.py
from datetime import datetime, timedelta
from asyncio import sleep
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import logger, database
from middleware.permissions import rights_required, check_edit_permission
from utils.formatters import escape_md
from text import *


@rights_required(["root"])
async def new_user_command(message: types.Message):
    """/newuser <username> — запуск создания нового пользователя (root only)."""
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2 or not args[1].strip():
            await message.answer(NEWUSER_MISSING_USERNAME, parse_mode=None)
            return

        new_username = args[1].strip().lstrip("@")

        if database.user_exists(new_username):
            await message.answer(NEWUSER_ALREADY_EXISTS.format(target_username=escape_md(new_username)), parse_mode=None)
            return

        kb = InlineKeyboardBuilder()
        options = [
            (ACCESS_OPTION_1_DAY, 1),
            (ACCESS_OPTION_14_DAYS, 14),
            (ACCESS_OPTION_30_DAYS, 30),
            (ACCESS_OPTION_90_DAYS, 90),
            (ACCESS_FOREVER, 0)
        ]
        for label, val in options:
            kb.button(text=label, callback_data=f"create_user:{new_username}:{val}")
        kb.adjust(3)

        await message.answer(
            NEWUSER_CREATION_HEADER.format(username=escape_md(new_username)),
            parse_mode=None,
            reply_markup=kb.as_markup()
        )

        logger.info(f"{message.from_user.username} начал создание пользователя {new_username}")

    except Exception as e:
        logger.exception(f"Ошибка new_user_command: {e}")
        await message.answer(NEWUSER_INIT_ERROR, parse_mode=None)


@rights_required(["root"])
async def create_user_callback(callback: types.CallbackQuery):
    """Обработка выбора срока доступа и создание пользователя + показ info."""
    try:
        parts = (callback.data or "").split(":")
        if len(parts) != 3:
            return await callback.answer(INCORRECT_DATA, show_alert=True)

        _, username, days = parts
        days = int(days)
        actor = callback.from_user.username or str(callback.from_user.id)

        # вычисляем access_until
        if days == 0:
            access_until = "31.12.2099"
        else:
            access_until = (datetime.today() + timedelta(days=days)).strftime("%d.%m.%Y")

        # дефолтные параметры пользователя
        user_data = {
            "username": username,
            "rights": "user",
            "dates": 30,
            "turnover_days_max": 30,
            "revenue_min": 300000,
            "category": "Женщинам",
            "percent": 20.0,
            "access_until": access_until
        }

        # сохраняем через репозиторий
        database.add_user(user_data)
        logger.info(f"{actor} создал пользователя {username} с доступом до {access_until}")

        # удаляем сообщение с кнопками создания (если возможно)
        try:
            await callback.message.delete()
        except Exception:
            pass

        # подтверждение
        confirm = await callback.message.answer(
            NEWUSER_CREATED.format(username=escape_md(username), access_until=escape_md(access_until)),
            parse_mode=None
        )

        # показываем карточку пользователя (как /info) — используем внутреннюю функцию
        await _send_info_for_username(callback.message.chat.id, actor, username)

        # удаляем подтверждение через 3 секунды, чтобы не захламлять чат
        await sleep(3)
        try:
            await confirm.delete()
        except Exception:
            pass

        await callback.answer()

    except Exception as e:
        logger.exception(f"Ошибка create_user_callback: {e}")
        await callback.answer(NEWUSER_CREATION_ERROR, show_alert=True)


async def _send_info_for_username(chat_id: int, requester_username: str, target_username: str):
    """
    Собирает текст и клавиатуру как в /info и отправляет в указанный chat_id.
    """
    # Проверки
    if not database.user_exists(target_username):
        await _safe_send(chat_id, NOT_FOUND_IN_THE_DATABASE.format(target_username=escape_md(target_username)), parse_mode=None)
        return

    user_data = database.get_user(target_username)
    if not user_data:
        await _safe_send(chat_id, COULDNT_GET_THE_DATA_FOR.format(target_username=escape_md(target_username)), parse_mode=None)
        return

    is_self = (target_username == requester_username)
    display_name = target_username
    rights = user_data.get("rights", "user")
    category = user_data.get("category", "—")
    drop_percent = user_data.get("percent", 0)
    raw_access_until = user_data.get("access_until", "01.01.2000") or "01.01.2000"
    access_until = NO_ACCESS if raw_access_until.strip() == "01.01.2000" else raw_access_until

    # Заголовок
    if is_self:
        header = INFO_PARAMS_SELF
    else:
        header = INFO_PARAMS_OTHER.format(display_name=display_name)

    # Даты
    today = datetime.today().date()
    dates_count = int(user_data.get("dates", 0) or 0)
    end_date = today - timedelta(days=1)
    if dates_count > 0:
        start_date = (end_date - timedelta(days=dates_count - 1)).strftime('%d.%m.%Y')
        dates_text = DAYS_FROM.format(
            dates_count=dates_count,
            start_date=start_date,
            end_date=end_date.strftime('%d.%m.%Y')
        )
    else:
        dates_text = THERE_IS_NO_SET_PERIOD

    rights_line = RIGHTS_LINE.format(rights=rights) if not (rights == "moder" and is_self) else ""

    info_text = USER_INFO.format(
        header=header,
        rights_line=rights_line,
        dates_text=dates_text,
        turnover_days_max=user_data.get("turnover_days_max", "—"),
        revenue_min=user_data.get("revenue_min", "—"),
        category=category,
        drop_percent=drop_percent,
        access_until=access_until
    )

    # Клавиатура (как в info_command) — показываем кнопки, если requester может редактировать
    kb = InlineKeyboardBuilder()
    requester = database.get_user(requester_username) or {}
    requester_rights = requester.get("rights", "user")
    can_edit = check_edit_permission(requester_username, target_username)

    if can_edit:
        if requester_rights == "root":
            edit_params = ["rights", "turnover_days_max", "revenue_min", "category", "dates", "percent", "access_until"]
        elif requester_rights == "admin":
            edit_params = ["turnover_days_max", "revenue_min", "category", "dates", "percent"]
        elif requester_rights == "moder":
            edit_params = ["turnover_days_max", "revenue_min", "category", "dates", "percent"]
        else:
            edit_params = []

        labels = {
            "rights": RIGHTS,
            "turnover_days_max": TURNOVER_DAYS_MAX,
            "revenue_min": REVENUE_MIN,
            "category": CATEGORY,
            "dates": DATES,
            "percent": PERCENT_TEXT,
            "access_until": ACCESS_UNTIL
        }

        for param in edit_params:
            kb.button(text=labels[param], callback_data=f"edit:{param}:{target_username}")
        kb.adjust(2)

    await _safe_send(chat_id, info_text, reply_markup=kb.as_markup() if can_edit else None, parse_mode=None)


async def _safe_send(chat_id: int, text: str, **send_kwargs):
    """Обёртка для безопасной отправки сообщений (чтобы ошибки Telegram не ломали логику)."""
    try:
        # импорт внутри функции чтобы избежать циклических импортов при старте
        from config import bot
        await bot.send_message(chat_id, text, **send_kwargs)
    except Exception as e:
        logger.exception(f"Не удалось отправить сообщение в чат {chat_id}: {e}")


def setup_new_user(dp: Dispatcher):
    dp.message.register(new_user_command, Command("newuser"))
    dp.callback_query.register(create_user_callback, F.data.startswith("create_user:"))
    logger.info("✅ Команда /newuser подключена")