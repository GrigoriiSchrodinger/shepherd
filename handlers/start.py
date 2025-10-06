from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import html

async def command_start_handler(message: Message) -> None:
    """
    Этот хэндлер получает сообщения с командой /start
    """
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!")

def setup(dispatcher: Dispatcher):
    dispatcher.message.register(command_start_handler, CommandStart())