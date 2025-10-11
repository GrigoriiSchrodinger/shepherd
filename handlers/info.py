from asyncio import sleep
from datetime import datetime, timedelta
from aiogram import Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from config import logger, database
from middleware.permissions import rights_required, check_edit_permission
from utils.formatters import escape_md


@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def info_command(message: types.Message):
    """Показать информацию о пользователе (/info [username])."""
    try:
        args = message.text.split(maxsplit=1)
        current_user = message.from_user.username or str(message.from_user.id)

        if len(args) > 1 and args[1].strip():
            target_username = args[1].lstrip("@")
        else:
            target_username = current_user

        # Проверка существования
        if not database.user_exists(target_username):
            await message.answer(
                f"❌ Пользователь `{escape_md(target_username)}` не найден в базе данных.",
                parse_mode=None
            )
            return

        # Проверка прав на просмотр — декоратор уже ограничил вызов для нужных ролей,
        # но проверим дополнительно через check_edit_permission (moder может только себя)
        if not check_edit_permission(current_user, target_username) and current_user != target_username:
            await message.answer("🚫 У вас нет прав для просмотра информации об этом пользователе.")
            return

        user_data = database.get_user(target_username)
        if not user_data:
            await message.answer(f"❌ Не удалось получить данные для `{escape_md(target_username)}`.", parse_mode=None)
            return

        is_self = (target_username == current_user)
        display_name = "себя" if is_self else f"`{escape_md(target_username)}`"
        rights = user_data.get("rights", "user")
        category = user_data.get("category", "—")
        drop_percent = user_data.get("percent", 0)
        raw_access_until = user_data.get("access_until", "01.01.2000") or "01.01.2000"
        access_until = "нет доступа" if raw_access_until.strip() == "01.01.2000" else raw_access_until

        # Даты
        today = datetime.today().date()
        dates_count = int(user_data.get("dates", 0) or 0)
        end_date = today - timedelta(days=1)
        if dates_count > 0:
            start_date = end_date - timedelta(days=dates_count - 1)
            dates_text = f"{dates_count} дней (с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')})"
        else:
            dates_text = "нет установленного периода"

        # Формируем текст с экранированием
        info_text = f"ℹ️ Информация о пользователе {display_name}:\n\n"
        # Не показываем права, если target — moder и запрашивает он сам (как у тебя было раньше)
        if not (rights == "moder" and is_self):
            info_text += f"Права: `{escape_md(str(rights))}`\n"
        info_text += (
            f"Даты: {escape_md(dates_text)}\n"
            f"Максимум дней оборота: `{escape_md(str(user_data.get('turnover_days_max', '—')))}`\n"
            f"Минимальная выручка: `{escape_md(str(user_data.get('revenue_min', '—')))}`\n"
            f"Категория: `{escape_md(str(category))}`\n"
            f"Порог падения (%): `{escape_md(str(drop_percent))}`\n"
            f"Доступ до: `{escape_md(str(access_until))}`"
        )

        # Кнопки редактирования — показываем только если вызывающий имеет право редактировать
        kb = InlineKeyboardBuilder()
        caller = database.get_user(current_user) or {}
        caller_rights = caller.get("rights", "user")

        # проверяем: может ли текущий пользователь редактировать target
        can_edit = check_edit_permission(current_user, target_username)

        if can_edit:
            # формируем список доступных параметров в зависимости от роли вызывающего
            if caller_rights == "root":
                edit_params = ["rights", "turnover_days_max", "revenue_min", "category", "dates", "percent", "access_until"]
            elif caller_rights == "admin":
                edit_params = ["turnover_days_max", "revenue_min", "category", "dates", "percent"]
            elif caller_rights == "moder":
                edit_params = ["turnover_days_max", "revenue_min", "category", "dates", "percent"]
            else:
                edit_params = []

            labels = {
                "rights": "🛠 Права",
                "turnover_days_max": "📈 Оборот",
                "revenue_min": "💰 Выручка",
                "category": "🏷 Категория",
                "dates": "📅 Даты",
                "percent": "📉 Порог падения %",
                "access_until": "🔑 Доступ"
            }

            for param in edit_params:
                kb.button(text=labels[param], callback_data=f"edit:{param}:{target_username}")
            kb.adjust(2)

        await message.answer(info_text, parse_mode=None, reply_markup=kb.as_markup() if can_edit else None)
        logger.info(f"{current_user} запросил информацию для {target_username}")

    except Exception as e:
        logger.exception(f"Ошибка в info_command: {e}")
        await message.answer("❌ Произошла ошибка при получении информации.", parse_mode=None)


@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def edit_param_callback(callback: types.CallbackQuery):
    """Обработка нажатия на кнопку редактирования параметра."""
    try:
        data = (callback.data or "").split(":")
        if len(data) != 3:
            return await callback.answer("Некорректный формат данных", show_alert=True)

        _, param, target_username = data
        current_user = callback.from_user.username or str(callback.from_user.id)

        # Проверка прав
        if not check_edit_permission(current_user, target_username):
            return await callback.answer("🚫 У вас нет прав редактировать этого пользователя.", show_alert=True)

        delete_after = []

        # === Обработка специальных параметров ===
        if param == "dates":
            kb = InlineKeyboardBuilder()
            for d in [7, 14, 30]:
                kb.button(text=f"{d} дней", callback_data=f"edit_value:{param}:{d}:{target_username}")
            kb.adjust(3)
            msg = await callback.message.answer("Выберите количество дней:", reply_markup=kb.as_markup())
            delete_after.append(msg)

        elif param == "rights":
            kb = InlineKeyboardBuilder()
            for r in ["root", "admin", "moder", "user"]:
                kb.button(text=r, callback_data=f"edit_value:{param}:{r}:{target_username}")
            kb.adjust(4)
            msg = await callback.message.answer("Выберите права:", reply_markup=kb.as_markup())
            delete_after.append(msg)

        elif param == "access_until":
            kb = InlineKeyboardBuilder()
            options = [
                ("+1 день", 1), ("+14 дней", 14), ("+30 дней", 30),
                ("+90 дней", 90), ("Бессрочно", 0), ("Удалить доступ", -1)
            ]
            for label, val in options:
                kb.button(text=label, callback_data=f"edit_access:{val}:{target_username}")
            kb.adjust(3)
            msg = await callback.message.answer("Настройка доступа:", reply_markup=kb.as_markup())
            delete_after.append(msg)

        else:
            # Обычное текстовое редактирование
            database.set_pending_edit(current_user, param, target_username)
            msg = await callback.message.answer(
                f"✏️ Введите новое значение для `{escape_md(param)}`:",
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
        await callback.answer("Произошла ошибка.", show_alert=True)


@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def edit_value_callback(callback: types.CallbackQuery):
    """Обработка выбора значения (dates, rights, access_until и т.п.)."""
    try:
        data = (callback.data or "").split(":")
        current_user = callback.from_user.username or str(callback.from_user.id)

        if not data:
            return await callback.answer("Некорректные данные.", show_alert=True)

        if data[0] == "edit_value":
            _, param, value, target_username = data

            if not check_edit_permission(current_user, target_username):
                return await callback.answer("🚫 Нет прав для редактирования.", show_alert=True)

            if param == "dates":
                value = int(value)

            database.update_user_param(target_username, param, value)
            confirm = await callback.message.answer(
                f"✅ Параметр `{escape_md(param)}` обновлён на `{escape_md(str(value))}`",
                parse_mode=None
            )
            await callback.answer()

        elif data[0] == "edit_access":
            _, days, target_username = data
            days = int(days)

            if not check_edit_permission(current_user, target_username):
                return await callback.answer("🚫 Нет прав для редактирования.", show_alert=True)

            if days == -1:
                new_date = "01.01.2000"
            elif days == 0:
                new_date = "31.12.2099"
            else:
                new_date_obj = datetime.today() + timedelta(days=days)
                new_date = new_date_obj.strftime("%d.%m.%Y")

            database.update_user_param(target_username, "access_until", new_date)
            confirm = await callback.message.answer(
                f"✅ Доступ для @{escape_md(target_username)} установлен до `{escape_md(new_date)}`",
                parse_mode=None
            )
            await callback.answer()

        else:
            return await callback.answer("Неизвестная команда.", show_alert=True)

        # Удаляем сообщение с подтверждением через 3 секунды
        await sleep(3)
        try:
            await confirm.delete()
        except Exception:
            pass

    except Exception as e:
        logger.exception(f"Ошибка edit_value_callback: {e}")
        await callback.answer("Произошла ошибка.", show_alert=True)


def setup_info(dp: Dispatcher):
    dp.message.register(info_command, Command("info"))
    dp.callback_query.register(edit_param_callback, F.data.startswith("edit:"))
    dp.callback_query.register(edit_value_callback, F.data.startswith(("edit_value:", "edit_access:")))
    logger.info("✅ Команда /info и кнопки редактирования подключены")
