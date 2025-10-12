from aiogram import types, Dispatcher
from config import database
from text import INCORRECT_FORMAT_FOR, PARAMETER_FOR_UPDATED, NO_EDITING_RIGHTS_USER


async def handle_text_edit(message: types.Message):
    current_user = message.from_user.username or str(message.from_user.id)

    pending = database.get_pending_edit(current_user)
    if not pending:
        return

    param = pending['param']
    target_username = pending['target']

    from middleware.permissions import check_edit_permission
    if not check_edit_permission(current_user, target_username):
        await message.answer(NO_EDITING_RIGHTS_USER)
        database.clear_pending_edit(current_user)
        return

    value = message.text.strip()

    try:
        if param in ("dates", "turnover_days_max", "revenue_min"):
            value = int(value)
        elif param == "percent":
            value = float(value)
    except Exception:
        await message.answer(INCORRECT_FORMAT_FOR.format(param=param))
        return

    if param.strip() == "category":
        parts = [p.strip() for p in value.split("/")]
        value = "/".join(parts)

    if param == "turnover_days_max":
        database.update_user_param(target_username, param, value)
        await message.answer(f"Обновили параметр оборачиваемости до {value} дней")
        return

    if param == "revenue_min":
        database.update_user_param(target_username, param, value)
        await message.answer(f"Обновили минимальную выручку от {value} рублей")
        return

    if param == "percent":
        database.update_user_param(target_username, param, value)
        await message.answer(f"Обновили процент падение остатков до {value}%")
        return

    if param == "category":
        database.update_user_param(target_username, param, value)
        await message.answer(f"Обновили категорию - {value}")
        return
    database.update_user_param(target_username, param, value)
    await message.answer(PARAMETER_FOR_UPDATED.format(param=param, value=value))

    database.clear_pending_edit(current_user)

def setup_handle_text_edit(dp: Dispatcher):
    dp.message.register(handle_text_edit)