import inspect
from aiogram import types
from config import logger, database


def rights_required(allowed_rights: list, self_only_rights: list = None):
    self_only_rights = self_only_rights or []

    def decorator(handler):
        async def wrapper(event: types.TelegramObject, *args, **kwargs):
            # 🧩 Определяем, кто реальный пользователь
            if isinstance(event, types.Message):
                user = event.from_user
                message = event
            elif isinstance(event, types.CallbackQuery):
                user = event.from_user
                message = event.message
            else:
                logger.warning(f"⚠️ Неизвестный тип события: {type(event)}")
                return

            username = user.username or str(user.id)

            # 🗄 Проверяем, есть ли пользователь в БД
            user_data = database.get_user(username)
            if not user_data:
                await message.answer(
                    f"❌ У вас нет доступа. Пользователь `{username}` не найден в базе данных.",
                    parse_mode="Markdown"
                )
                logger.warning(f"Пользователь {username} не найден в БД.")
                return

            user_rights = user_data.get("rights")

            # 🚫 Проверяем права
            if user_rights not in allowed_rights:
                await message.answer("🚫 У вас нет доступа к этой команде.")
                logger.warning(f"❌ {username} пытался вызвать команду без прав ({user_rights})")
                return

            # 🔒 Если moder может только для себя
            if user_rights in self_only_rights:
                target_username = None

                # Если это команда с текстом (например /info <user>)
                if isinstance(event, types.Message):
                    args_split = message.text.split(maxsplit=2)
                    if len(args_split) > 1:
                        target_username = args_split[1].lstrip("@")

                # Если это callback (например, на кнопке)
                elif isinstance(event, types.CallbackQuery):
                    if ":" in event.data:
                        parts = event.data.split(":")
                        target_username = parts[-1].lstrip("@")

                # Проверка: moder не может изменять чужие данные
                if target_username and target_username != username:
                    await message.answer("🚫 Вы можете изменять данные только для себя.")
                    logger.warning(f"❌ {username} пытался изменить чужие данные ({target_username})")
                    return

            # 🧩 Вызываем сам хэндлер (без лишних аргументов)
            sig = inspect.signature(handler)
            valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

            return await handler(event, *args, **valid_kwargs)

        return wrapper
    return decorator

def check_edit_permission(current_user: str, target_username: str) -> bool:
    """
    Проверяет, имеет ли current_user право редактировать target_username.
    """
    current = database.get_user(current_user)
    target = database.get_user(target_username)

    if not current or not target:
        return False

    # root может всех
    if current["rights"] == "root":
        return True

    # admin может moder и user
    if current["rights"] == "admin" and target["role"] in ("moder", "user"):
        return True

    # moder может только user
    if current["rights"] == "moder" and target["role"] == "user":
        return True

    # user — только себя
    if current_user == target_username:
        return True

    return False
