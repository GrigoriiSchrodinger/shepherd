import asyncio
import os
import psutil
from aiogram import Dispatcher
from config import bot
from middleware.auth_middleware import AuthMiddleware
import handlers

async def monitor_resources(interval: float = 0.5):
    """Мониторит использование CPU и памяти."""
    process = psutil.Process(os.getpid())
    while True:
        cpu = process.cpu_percent(interval=None)
        mem = process.memory_info().rss / 1024 / 1024  # в MB
        print(f"[MONITOR] CPU: {cpu:.1f}% | Memory: {mem:.2f} MB")
        await asyncio.sleep(interval)

# --- helper для логирования памяти в ключевых местах ---
def log_memory(msg: str):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024
    print(f"[MEMORY] {msg} | Usage: {mem:.2f} MB")

async def main() -> None:
    dp = Dispatcher()
    dp.message.middleware.register(AuthMiddleware())
    handlers.setup(dp)

    # Запускаем мониторинг в фоне
    asyncio.create_task(monitor_resources())

    # Пример вставки логирования перед генерацией отчета
    log_memory("Перед стартом polling")

    await dp.start_polling(bot)

    # Если у тебя есть async-генерация отчетов, можно логировать прямо там
    # log_memory("После генерации отчета")

if __name__ == "__main__":
    asyncio.run(main())
