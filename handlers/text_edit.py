from aiogram import types, Dispatcher
from config import database

async def handle_text_edit(message: types.Message):
    current_user = message.from_user.username or str(message.from_user.id)

    pending = database.get_pending_edit(current_user)
    if not pending:
        return

    param = pending['param']
    target_username = pending['target']

    from middleware.permissions import check_edit_permission
    if not check_edit_permission(current_user, target_username):
        await message.answer("🚫 У вас нет прав редактировать этого пользователя.")
        database.clear_pending_edit(current_user)
        return

    value = message.text.strip()

    try:
        if param in ("dates", "turnover_days_max", "revenue_min"):
            value = int(value)
        elif param == "percent":
            value = float(value)
    except Exception:
        await message.answer(f"❌ Неверный формат для {param}`")
        return

    if param.strip() == "category":
        parts = [p.strip() for p in value.split("/")]
        value = "/".join(parts)

    database.update_user_param(target_username, param, value)
    await message.answer(f"✅ Параметр {param} обновлён на {value}")

    # очищаем pending
    database.clear_pending_edit(current_user)

def setup_handle_text_edit(dp: Dispatcher):
    dp.message.register(handle_text_edit)