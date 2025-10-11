from aiogram import types, Dispatcher
from config import database
from utils.formatters import escape_md

async def handle_text_edit(message: types.Message):
    current_user = message.from_user.username or str(message.from_user.id)

    pending = database.get_pending_edit(current_user)
    if not pending:
        return  # ничего не делаем, обычный текст

    param = pending['param']
    target_username = pending['target']

    # Проверка прав на редактирование
    from middleware.permissions import check_edit_permission
    if not check_edit_permission(current_user, target_username):
        await message.answer("🚫 У вас нет прав редактировать этого пользователя.")
        database.clear_pending_edit(current_user)
        return

    value = message.text.strip()

    # Можно добавить кастомную обработку типа int/float для числовых полей
    try:
        if param in ("dates", "turnover_days_max", "revenue_min"):
            value = int(value)
        elif param == "percent":
            value = float(value)
    except Exception:
        await message.answer(f"❌ Неверный формат для `{escape_md(param)}`")
        return

    # Сохраняем
    database.update_user_param(target_username, param, value)
    await message.answer(f"✅ Параметр `{escape_md(param)}` обновлён на `{escape_md(str(value))}`")

    # очищаем pending
    database.clear_pending_edit(current_user)

def setup_handle_text_edit(dp: Dispatcher):
    dp.message.register(handle_text_edit)