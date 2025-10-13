import asyncio
import os
import psutil
from aiogram import Dispatcher
from config import bot
from middleware.auth_middleware import AuthMiddleware
import handlers

import asyncio

async def monitor_resources(interval: int = 0.5):
    """Мониторит использование CPU и памяти."""
    loop = asyncio.get_event_loop()
    loop.slow_callback_duration = 0.1  # логировать все "медленные" задачи >100ms
    process = psutil.Process(os.getpid())
    while True:
        cpu = process.cpu_percent(interval=None)  # % CPU
        mem = process.memory_info().rss / 1024 / 1024  # в МБ
        print(f"[MONITOR] CPU: {cpu:.1f}% | Memory: {mem:.2f} MB")
        await asyncio.sleep(interval)


async def main() -> None:
    dp = Dispatcher()
    dp.message.middleware.register(AuthMiddleware())
    handlers.setup(dp)

    # Запускаем мониторинг в фоне
    asyncio.create_task(monitor_resources())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
