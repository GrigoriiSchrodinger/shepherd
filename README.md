# Shepherd Telegram Bot

Этот проект представляет собой простой эхо-бот для Telegram, созданный с использованием библиотеки `aiogram` версии 3.x. Бот повторяет отправленные пользователем текстовые сообщения и отвечает на команду `/start`.

## Установка и запуск

1. **Склонируйте репозиторий**:

    ```bash
    git clone https://github.com/yourusername/shepherd.git
    cd shepherd
    ```

2. **Создайте виртуальное окружение**:

    ```bash
    python -m venv venv
    ```

3. **Активируйте виртуальное окружение**:

    - Для Windows:

        ```bash
        venv\Scripts\activate
        ```

    - Для macOS и Linux:

        ```bash
        source venv/bin/activate
        ```

4. **Установите зависимости**:

    ```bash
    pip install -r requirements.txt
    ```

5. **Настройте токен бота**:

    Создайте файл `.env` в корневой директории проекта и добавьте токен вашего бота:

    ```env
    TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
    ```

6. **Запустите бота**:

    ```bash
    python bot/main.py
    ```

## Структура проекта

```
shepherd/
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py
│   │   └── echo.py
│   ├── config.py
│   └── main.py
├── .env
├── requirements.txt
└── README.md
```

## Лицензия

MIT License

Copyright (c) 2023 Ваш Имя

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Шаг 3: Настройка файлов внутри `bot`

#### Файл `bot/config.py`

Содержимое файла `bot/config.py`:

```python bot/config.py
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получаем токен из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
```

#### Файл `bot/handlers/__init__.py`

Содержимое файла `bot/handlers/__init__.py`:

```python bot/handlers/__init__.py
from .start import command_start_handler
from .echo import echo_handler

__all__ = [
    'command_start_handler',
    'echo_handler'
]
```

#### Файл `bot/handlers/start.py`

Содержимое файла `bot/handlers/start.py`:

```python bot/handlers/start.py
from aiogram import html
from aiogram.types import Message
from aiogram.filters import CommandStart

async def command_start_handler(message: Message) -> None:
    """
    Этот хэндлер получает сообщения с командой /start
    """
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!")
```

#### Файл `bot/handlers/echo.py`

Содержимое файла `bot/handlers/echo.py`:

```python bot/handlers/echo.py
from aiogram.types import Message

async def echo_handler(message: Message) -> None:
    """
    Хэндлер будет пересылать полученное сообщение обратно отправителю
    """
    try:
        # Отправляем копию полученного сообщения
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # Но не все типы поддерживаются для копирования, поэтому нужно обрабатывать это
        await message.answer("Неподдерживаемый тип сообщения!")
```

#### Файл `bot/main.py`

Содержимое файла `bot/main.py`:

```python bot/main.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.exceptions import TelegramAPIError

from .config import TELEGRAM_BOT_TOKEN
from .handlers import command_start_handler, echo_handler

# Включаем логирование
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def main() -> None:
    # Инициализируем экземпляр Bot с параметрами по умолчанию, которые будут переданы во все вызовы API
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Создаем экземпляр Dispatcher для управления обработчиками
    dp = Dispatcher()

    # Регистрируем хэндлеры
    dp.message.register(command_start_handler, CommandStart())
    dp.message.register(echo_handler)

    # Запускаем обработку событий
    try:
        await dp.start_polling(bot)
    except TelegramAPIError as e:
        logger.error(f"Ошибка Telegram API: {e}")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Объяснение изменений:

1. **Файл `bot/config.py`**:
   - Загружает переменные окружения из файла `.env`.
   - Экспортирует токен бота.

2. **Файл `bot/handlers/__init__.py`**:
   - Импортирует и экспортирует хэндлеры `command_start_handler` и `echo_handler`.

3. **Файл `bot/handlers/start.py`**:
   - Определяет хэндлер для команды `/start`.

4. **Файл `bot/handlers/echo.py`**:
   - Определяет хэндлер для обработки текстовых сообщений.

5. **Файл `bot/main.py`**:
   - Инициализирует бота и диспетчер.
   - Регистрирует хэндлеры.
   - Запускает обработку событий.

### Шаг 4: Запуск бота

1. **Активируйте виртуальное окружение**:

    - Для Windows:

        ```bash
        venv\Scripts\activate
        ```

    - Для macOS и Linux:

        ```bash
        source venv/bin/activate
        ```

2. **Установите зависимости**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Настройте токен бота**:

    Убедитесь, что файл `.env` содержит правильный токен:

    ```env .env
    TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
    ```

4. **Запустите бота**:

    ```bash
    python bot/main.py