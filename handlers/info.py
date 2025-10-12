from asyncio import sleep
from datetime import datetime, timedelta
from aiogram import Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from config import logger, database
from middleware.permissions import rights_required, check_edit_permission
from text import *
from utils.formatters import escape_md


@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def info_command(message: types.Message):
    try:
        args = message.text.split(maxsplit=1)
        current_user = message.from_user.username or str(message.from_user.id)
        target_username = args[1].lstrip("@") if len(args) > 1 and args[1].strip() else current_user

        if not database.user_exists(target_username):
            await message.answer(NOT_FOUND_IN_THE_DATABASE.format(target_username=escape_md(target_username)))
            return

        if not check_edit_permission(current_user, target_username) and current_user != target_username:
            await message.answer(NO_VIEWING_RIGHTS)
            return

        user_data = database.get_user(target_username)
        if not user_data:
            await message.answer(COULDNT_GET_THE_DATA_FOR.format(target_username=escape_md(target_username)))
            return

        is_self = (target_username == current_user)
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

        kb = InlineKeyboardBuilder()
        caller = database.get_user(current_user) or {}
        caller_rights = caller.get("rights", "user")
        can_edit = check_edit_permission(current_user, target_username)

        if can_edit:
            if caller_rights == "root":
                edit_params = ["rights", "turnover_days_max", "revenue_min", "category", "dates", "percent", "access_until"]
            elif caller_rights == "admin":
                edit_params = ["turnover_days_max", "revenue_min", "category", "dates", "percent"]
            elif caller_rights == "moder":
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

        await message.answer(info_text, parse_mode=None, reply_markup=kb.as_markup() if can_edit else None)
        logger.info(f"{current_user} запросил информацию для {target_username}")

    except Exception as e:
        logger.exception(f"Ошибка в info_command: {e}")
        await message.answer(AN_ERROR_OCCURRED_IN_RECEIVING_DATA)


@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def edit_param_callback(callback: types.CallbackQuery):
    """Обработка нажатия на кнопку редактирования параметра."""
    try:
        data = (callback.data or "").split(":")
        if len(data) != 3:
            return await callback.answer(INCORRECT_FORMAT, show_alert=True)

        _, param, target_username = data
        current_user = callback.from_user.username or str(callback.from_user.id)

        # Проверка прав
        if not check_edit_permission(current_user, target_username):
            return await callback.answer(NO_EDITING_RIGHTS, show_alert=True)

        delete_after = []

        # === Обработка специальных параметров ===
        if param == "dates":
            kb = InlineKeyboardBuilder()
            for d in [7, 14, 30]:
                kb.button(text=f"{d} дней", callback_data=f"edit_value:{param}:{d}:{target_username}")
            kb.adjust(3)
            msg = await callback.message.answer(CHOOSE_DAYS, reply_markup=kb.as_markup())
            delete_after.append(msg)

        elif param == "rights":
            kb = InlineKeyboardBuilder()
            for r in ["root", "admin", "moder", "user"]:
                kb.button(text=r, callback_data=f"edit_value:{param}:{r}:{target_username}")
            kb.adjust(4)
            msg = await callback.message.answer(CHOOSE_RIGHTS, reply_markup=kb.as_markup())
            delete_after.append(msg)

        elif param == "access_until":
            kb = InlineKeyboardBuilder()
            options = [
                (ACCESS_OPTION_1_DAY, 1),
                (ACCESS_OPTION_14_DAYS, 14),
                (ACCESS_OPTION_30_DAYS, 30),
                (ACCESS_OPTION_90_DAYS, 90),
                (ACCESS_FOREVER, 0)
            ]
            for label, val in options:
                kb.button(text=label, callback_data=f"edit_access:{val}:{target_username}")
            kb.adjust(3)
            msg = await callback.message.answer(ACCESS_SETTINGS, reply_markup=kb.as_markup())
            delete_after.append(msg)

        else:
            # Обычное текстовое редактирование
            database.set_pending_edit(current_user, param, target_username)
            msg = await callback.message.answer(
                EDIT_PROMPT.format(param=param),
                parse_mode=None
            )
            delete_after.append(msg)

        await callback.answer()

        # Удаляем временные сообщения через 10 секунд
        await sleep(10)
        for m in delete_after:
            try:
                await m.delete()
            except Exception:
                pass

    except Exception as e:
        logger.exception(f"Ошибка edit_param_callback: {e}")
        await callback.answer(GENERIC_ERROR, show_alert=True)


@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def edit_value_callback(callback: types.CallbackQuery):
    """Обработка выбора значения (dates, rights, access_until и т.п.)."""
    try:
        data = (callback.data or "").split(":")
        current_user = callback.from_user.username or str(callback.from_user.id)

        if not data:
            return await callback.answer(INCORRECT_DATA, show_alert=True)

        if data[0] == "edit_value":
            _, param, value, target_username = data

            if not check_edit_permission(current_user, target_username):
                return await callback.answer(NO_EDITING_RIGHTS, show_alert=True)

            if param == "dates":
                value = int(value)

            database.update_user_param(target_username, param, value)
            confirm = await callback.message.answer(
                f"Обновили параметр, отчет будет за послдение {value} дней",
                parse_mode=None
            )
            await callback.answer()

        elif data[0] == "edit_access":
            _, days, target_username = data
            days = int(days)

            if not check_edit_permission(current_user, target_username):
                return await callback.answer(NO_EDITING_RIGHTS, show_alert=True)

            if days == -1:
                new_date = "01.01.2000"
            elif days == 0:
                new_date = "31.12.2099"
            else:
                new_date_obj = datetime.today() + timedelta(days=days)
                new_date = new_date_obj.strftime("%d.%m.%Y")

            database.update_user_param(target_username, "access_until", new_date)
            confirm = await callback.message.answer(
                ACCESS_UPDATED.format(username=escape_md(target_username), date=escape_md(new_date)),
                parse_mode=None
            )
            await callback.answer()

        else:
            return await callback.answer(UNKNOWN_COMMAND, show_alert=True)

        # Удаляем сообщение с подтверждением через 3 секунды
        await sleep(3)
        try:
            await confirm.delete()
        except Exception:
            pass

    except Exception as e:
        logger.exception(f"Ошибка edit_value_callback: {e}")
        await callback.answer(GENERIC_ERROR, show_alert=True)

HELP_TEXT_USER = """
Команды:
/products - генерация отчета
"""

HELP_TEXT_MODER = """
Команды:
/info - просмотр и редактирование параметров отчета и пользователя
/products - генерация отчета
"""

HELP_TEXT_ADMIN = """
Команды:
/info - просмотр и редактирование параметров отчета и пользователя
/info UserName - просмотр и редактирование параметров отчета другого пользователя
/products - генерация отчета
"""

HELP_TEXT_ROOT = """
Команды:
/newuser UserName - создание нового пользователя
/info - просмотр и редактирование параметров отчета и пользователя
/info UserName - просмотр и редактирование параметров отчета другого пользователя
/products - генерация отчета

Информация о правах доступа:

Root - может все

Admin:
• Не может добавлять пользователей
• Не может редактировать доступ себя и других
• Может редактировать параметры себя и других пользователей (кроме других admin и root)
• Может просматривать информацию о себе и других (кроме других admin и root)

Moder:
• Не может менять параметры других пользователей
• Не может добавлять пользователей
• Не может редактировать доступ для других
• Не может просматривать информацию о других
• Может просматривать информацию о себе
• Может менять параметры для себя

User:
• Может вызвать только команду /products
"""

async def cmd_help(message: types.Message):
    logger.info(f"📩 /help вызван пользователем @{message.from_user.username}")
    username = message.from_user.username or str(message.from_user.id)
    user_data = database.get_user(username)

    if not user_data:
        await message.answer("❌ Пользователь не найден в базе данных.")
        return

    rights = user_data.get("rights")

    if rights =="root":
        text = HELP_TEXT_ROOT
    elif rights == "admin":
        text = HELP_TEXT_ADMIN
    elif rights == "moder":
        text = HELP_TEXT_MODER
    else:
        text = HELP_TEXT_USER

    await message.answer(text)

def setup_info(dp: Dispatcher):
    dp.message.register(info_command, Command("info"))
    dp.message.register(cmd_help, Command("help"))
    dp.callback_query.register(edit_param_callback, F.data.startswith("edit:"))
    dp.callback_query.register(edit_value_callback, F.data.startswith(("edit_value:", "edit_access:")))
    logger.info("✅ Команда /info и кнопки редактирования подключены")