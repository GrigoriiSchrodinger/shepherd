from aiogram import Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import database, logger
from middleware.permissions import rights_required, check_edit_permission
from utils.formatters import format_revenue, format_category


# === Callback для кнопки "Изменить параметр" ===
@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def edit_param_callback(callback: types.CallbackQuery):
    try:
        data = callback.data.split(":")
        if len(data) != 3:
            return await callback.answer("Некорректный формат данных", show_alert=True)

        _, param, target_username = data
        current_user = callback.from_user.username

        if not check_edit_permission(current_user, target_username):
            logger.warning(f"❌ {current_user} не имеет доступа для редактирования {target_username}")
            return await callback.answer("У вас нет прав для редактирования этого пользователя.", show_alert=True)

        database.set_pending_edit(current_user, param, target_username)

        kb = InlineKeyboardBuilder()

        # Кнопки для дат
        if param == "dates":
            for days in [7, 14, 30]:
                kb.button(text=f"{days} дней", callback_data=f"set_date:{days}:{target_username}")
            kb.adjust(3)
            await callback.message.answer(f"📅 Выберите новый период дат для *{target_username}*:",
                                          reply_markup=kb.as_markup(),
                                          parse_mode="Markdown")

        # Кнопки для прав
        elif param == "rights":
            for right in ["root", "admin", "moder", "user"]:
                kb.button(text=right, callback_data=f"set_rights:{right}:{target_username}")
            kb.adjust(2)
            await callback.message.answer(f"🛠 Выберите новые права для *{target_username}*:",
                                          reply_markup=kb.as_markup(),
                                          parse_mode="Markdown")
        else:
            await callback.message.answer(f"✏️ Введите новое значение для *{param}*:", parse_mode="Markdown")

        await callback.answer()

    except Exception as e:
        logger.exception(f"Ошибка при обработке edit_param_callback: {e}")
        await callback.answer("Произошла ошибка при обработке команды.", show_alert=True)


# === Callback для кнопок дат ===
@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def set_date_callback(callback: types.CallbackQuery):
    try:
        _, days, target_username = callback.data.split(":")
        days = int(days)
        current_user = callback.from_user.username

        if not check_edit_permission(current_user, target_username):
            return await callback.answer("У вас нет прав для редактирования этого пользователя.", show_alert=True)

        database.update_user_param(target_username, "dates", days)
        database.clear_pending_edit(current_user)

        await callback.message.answer(f"✅ Период дат для *{target_username}* обновлён: `{days}` дней", parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception(f"Ошибка при set_date_callback: {e}")
        await callback.answer("Произошла ошибка.", show_alert=True)


# === Callback для кнопок прав ===
@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def set_rights_callback(callback: types.CallbackQuery):
    try:
        _, new_rights, target_username = callback.data.split(":")
        current_user = callback.from_user.username

        if not check_edit_permission(current_user, target_username):
            return await callback.answer("У вас нет прав для редактирования этого пользователя.", show_alert=True)

        database.update_user_param(target_username, "rights", new_rights)
        database.clear_pending_edit(current_user)

        await callback.message.answer(f"✅ Права пользователя *{target_username}* обновлены: `{new_rights}`", parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception(f"Ошибка при set_rights_callback: {e}")
        await callback.answer("Произошла ошибка.", show_alert=True)


# === Обработка нового значения параметра (ввод с клавиатуры) ===
@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def handle_new_param_value(message: types.Message):
    username = message.from_user.username
    text = message.text.strip()

    pending = database.get_pending_edit(username)
    if not pending:
        return

    param = pending["param"]
    target_username = pending["target"]

    logger.info(f"💾 {username} обновляет {param} у {target_username} → {text}")

    try:
        if param == "dates":
            value = int(text)
            if not (1 <= value <= 60):
                return await message.answer("⚠️ Количество дней должно быть от 1 до 60.")
        elif param == "revenue_min":
            try:
                value = float(text.replace(",", "."))
            except ValueError:
                return await message.answer("⚠️ Минимальная выручка должна быть числом.")
        elif param == "turnover_days_max":
            value = int(text)
            if value < 1:
                return await message.answer("⚠️ Максимум дней оборота должен быть больше 0.")
        elif param == "category":
            value = format_category(text)
            if not value:
                return await message.answer("⚠️ Категория не может быть пустой.")
        elif param == "rights":
            value = text.strip()
            if not value:
                return await message.answer("⚠️ Права не могут быть пустыми.")
        else:
            value = text

        database.update_user_param(target_username, param, value)

        display_name = "себя" if target_username == username else f"@{target_username}"
        formatted_value = format_revenue(value) if param == "revenue_min" else str(value)
        await message.answer(f"✅ Параметр *{param}* успешно обновлён у {display_name}: `{formatted_value}`", parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Ошибка при обновлении параметра {param}: {e}")
        await message.answer("⚠️ Ошибка при сохранении значения. Попробуйте позже.")
    finally:
        database.clear_pending_edit(username)


# === Регистрация обработчиков ===
def setup_edit_handlers(dp: Dispatcher) -> None:
    dp.callback_query.register(edit_param_callback, F.data.startswith("edit:"))
    dp.callback_query.register(set_date_callback, F.data.startswith("set_date:"))
    dp.callback_query.register(set_rights_callback, F.data.startswith("set_rights:"))
    dp.message.register(handle_new_param_value)
    logger.info("✅ Обработчики редактирования параметров подключены")
