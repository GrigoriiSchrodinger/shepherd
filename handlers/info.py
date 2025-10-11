from asyncio import sleep
from datetime import datetime, timedelta
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import database, logger
from middleware.permissions import rights_required, check_edit_permission
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

    is_self = (target_username == current_user)
    display_name = "себя" if is_self else f"`{escape_md(target_username)}`"
    rights = escape_md(user_data.get('rights'))
    category = escape_md(user_data.get('category'))
    drop_percent = user_data.get('percent', 0)
    access_until = user_data.get('access_until', 'нет доступа')

    # Даты
    today = datetime.today().date()
    dates_count = user_data.get('dates', 0)
    end_date = today - timedelta(days=1)
    start_date = end_date - timedelta(days=dates_count - 1) if dates_count > 0 else end_date
    dates_text = f"{dates_count} дней (с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')})" if dates_count > 0 else "нет установленного периода"

    # === Формируем текст ===
    raw_access_until = user_data.get('access_until', '01.01.2000')
    if raw_access_until.strip() == "01.01.2000":
        access_until = "нет доступа"
    else:
        access_until = raw_access_until

    info_text = f"ℹ️ Информация о пользователе {display_name}:\n\n"
    if rights != "moder" or not is_self:
        info_text += f"Права: {rights}\n"
    info_text += (
        f"Даты: {dates_text}\n"
        f"Максимум дней оборота: {user_data.get('turnover_days_max')}\n"
        f"Минимальная выручка: {format_revenue(user_data.get('revenue_min'))}\n"
        f"Категория: {category}\n"
        f"Порог падения (%): {drop_percent}\n"
        f"Доступ до: {access_until}"
    )


    kb = InlineKeyboardBuilder()
    user_rights = database.get_user(current_user).get("rights", "user")

    # === Кнопки редактирования параметров ===
    edit_params = []
    if user_rights == "root":
        edit_params = ["rights", "turnover_days_max", "revenue_min", "category", "dates", "percent", "access_until"]
    elif user_rights == "admin":
        edit_params = ["turnover_days_max", "revenue_min", "category", "dates", "percent", "access_until"]
    elif user_rights == "moder" and is_self:
        edit_params = ["turnover_days_max", "revenue_min", "category", "dates", "percent", "access_until"]

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
    await message.answer(info_text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    logger.info(f"{current_user} запросил информацию для {target_username}")


# === Хендлер нажатий на кнопки редактирования ===
@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def edit_param_callback(callback: types.CallbackQuery):
    try:
        data = callback.data.split(":")
        if len(data) != 3:
            return await callback.answer("Некорректный формат данных", show_alert=True)

        _, param, target_username = data
        current_user = callback.from_user.username

        if not check_edit_permission(current_user, target_username):
            return await callback.answer("У вас нет прав для редактирования этого пользователя.", show_alert=True)

        delete_after = []  # сохраняем созданные сообщения для последующего удаления

        # Специальные кнопки для некоторых параметров
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
            # Обычное редактирование через текст
            database.set_pending_edit(current_user, param, target_username)
            msg = await callback.message.answer(f"✏️ Введите новое значение для *{param}*:", parse_mode="Markdown")
            delete_after.append(msg)

        await callback.answer()

        # Удаляем эти временные сообщения через 10 секунд
        await sleep(10)
        for m in delete_after:
            try:
                await m.delete()
            except Exception:
                pass

    except Exception as e:
        logger.exception(f"Ошибка edit_param_callback: {e}")
        await callback.answer("Произошла ошибка.", show_alert=True)


# === Обработка выбора через кнопки (dates, rights, access_until) ===
@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def edit_value_callback(callback: types.CallbackQuery):
    try:
        data = callback.data.split(":")
        current_user = callback.from_user.username

        if data[0] == "edit_value":
            _, param, value, target_username = data
            if not check_edit_permission(current_user, target_username):
                return await callback.answer("Нет прав для редактирования", show_alert=True)

            if param == "dates":
                value = int(value)

            database.update_user_param(target_username, param, value)
            confirm = await callback.message.answer(f"✅ Параметр *{param}* обновлён на {value}", parse_mode="Markdown")
            await callback.answer()

        elif data[0] == "edit_access":
            _, days, target_username = data
            days = int(days)

            if not check_edit_permission(current_user, target_username):
                return await callback.answer("Нет прав для редактирования", show_alert=True)

            if days == -1:
                new_date = "01.01.2000"
            elif days == 0:
                new_date = "31.12.2099"
            else:
                new_date_obj = datetime.today() + timedelta(days=days)
                new_date = new_date_obj.strftime("%d.%m.%Y")

            database.update_user_param(target_username, "access_until", new_date)
            confirm = await callback.message.answer(
                f"✅ Доступ для @{target_username} установлен до {new_date}",
                parse_mode="Markdown"
            )
            await callback.answer()

            # Удаляем сообщение о подтверждении через 3 секунды
            await sleep(3)
            try:
                await confirm.delete()
            except Exception:
                pass

    except Exception as e:
        logger.exception(f"Ошибка edit_value_callback: {e}")
        await callback.answer("Произошла ошибка.", show_alert=True)

# === Регистрация ===
def setup_info(dp: Dispatcher):
    dp.message.register(info_command, Command("info"))
    dp.callback_query.register(edit_param_callback, F.data.startswith("edit:"))
    dp.callback_query.register(edit_value_callback, F.data.startswith(("edit_value:", "edit_access:")))
    logger.info("✅ Команда /info и кнопки редактирования подключены")
