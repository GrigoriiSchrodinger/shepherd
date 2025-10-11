from aiogram import Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import database, logger
from middleware.permissions import rights_required, check_edit_permission
from utils.formatters import format_revenue

# === Словарь параметров для кнопок ===
PARAMS = {
    "Максимум дней оборота": "turnover_days_max",
    "Минимальная выручка": "revenue_min",
    "Категория": "category",
    "Даты": "dates",
    "Права": "rights"
}

# === Callback для кнопки "Изменить параметр" ===
@rights_required(["root", "admin", "moder"], self_only_rights=["moder"])
async def edit_param_callback(callback: types.CallbackQuery):
    try:
        data = callback.data.split(":")
        if len(data) != 3:
            return await callback.answer("Некорректный формат данных", show_alert=True)

        _, param, target_username = data
        current_user = callback.from_user.username

        # Проверяем права редактирования
        if not check_edit_permission(current_user, target_username):
            logger.warning(f"❌ {current_user} не имеет доступа для редактирования {target_username}")
            return await callback.answer("У вас нет прав для редактирования этого пользователя.", show_alert=True)

        # Сохраняем, какой параметр редактируется
        database.set_pending_edit(current_user, param, target_username)
        await callback.message.answer(f"✏️ Введите новое значение для *{param}*:", parse_mode="Markdown")

        await callback.answer()

    except Exception as e:
        logger.exception(f"Ошибка при обработке edit_param_callback: {e}")
        await callback.answer("Произошла ошибка при обработке команды.", show_alert=True)


# === Обработка нового значения параметра ===
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
        # --- ВАЛИДАЦИЯ ПО ТИПУ ---
        if param == "dates":
            value = int(text)
            if not (1 <= value <= 60):
                return await message.answer("⚠️ Количество дней должно быть от 1 до 60.")

        elif param == "revenue_min":
            try:
                value = float(text.replace(",", "."))
            except ValueError:
                return await message.answer("⚠️ Минимальная выручка должна быть числом (например: 10000 или 2500.50).")

        elif param == "turnover_days_max":
            value = int(text)
            if value < 1:
                return await message.answer("⚠️ Максимум дней оборота должен быть больше 0.")

        elif param == "category":
            value = text.strip()
            if not value:
                return await message.answer("⚠️ Категория не может быть пустой.")

        elif param == "rights":
            value = text.strip()
            if not value:
                return await message.answer("⚠️ Права не могут быть пустыми.")

        else:
            value = text

        # --- Обновляем в БД ---
        database.update_user_param(target_username, param, value)

        # Форматирование для отображения
        display_name = "себя" if target_username == username else f"@{target_username}"
        if param == "revenue_min":
            formatted_value = format_revenue(value)
        else:
            formatted_value = str(value)

        await message.answer(
            f"✅ Параметр *{param}* успешно обновлён у {display_name}: `{formatted_value}`",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.exception(f"Ошибка при обновлении параметра {param}: {e}")
        await message.answer("⚠️ Ошибка при сохранении значения. Попробуйте позже.")

    finally:
        database.clear_pending_edit(username)

# === Регистрация обработчиков ===
def setup_edit_handlers(dp: Dispatcher) -> None:
    dp.callback_query.register(edit_param_callback, F.data.startswith("edit:"))
    dp.message.register(handle_new_param_value)
    logger.info("✅ Обработчики редактирования параметров подключены")
