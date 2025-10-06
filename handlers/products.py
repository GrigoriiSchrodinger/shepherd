import os
from collections import defaultdict
from datetime import datetime, timedelta

from aiogram import Dispatcher, types, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from api.mpstats_api import MpstatsAPI
from api.mpstats_module import MpstatsData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

PRODUCTS_PER_PAGE = 5

class PaginationManager:
    def __init__(self):
        self.api = MpstatsAPI(os.getenv('MPSTATS_API_TOKEN'))
        self.user_sessions = defaultdict(dict)
        logger.info("Инициализация PaginationManager завершена")

    async def fetch_products(self, start_date: str, end_date: str, category: str):
        logger.debug(f"Загрузка данных за период {start_date} - {end_date}")
        data = await self.api.get_category_data(
            start_date,
            end_date,
            category
        )
        mpstats_data = MpstatsData(data.get("data", []))
        filtered = mpstats_data.filter_products(30, 200000)
        return mpstats_data.sort_products_by_revenue(
            mpstats_data.filter_products_with_drop(filtered, 20)
        )

    async def send_page(self, chat_id: int, user_id: int, page: int, bot: Bot, start_date: str, end_date: str):
        logger.info(f"Отправка страницы {page} для user={user_id}, chat={chat_id}")
        
        # Обновляем сессию
        session_data = {
            'message_ids': self.user_sessions[user_id].get('message_ids', []),
            'chat_id': chat_id
        }
        self.user_sessions[user_id] = session_data
        self.user_sessions[user_id]['bot'] = bot

        # Удаление старых сообщений
        await self._delete_previous_messages(user_id)
        
        products = await self.fetch_products(
            start_date=start_date,
            end_date=end_date,
            category="Женщинам/Толстовки, свитшоты и худи/Свитшот"
        )
        
        total_pages = (len(products) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
        
        start = page * PRODUCTS_PER_PAGE
        messages_to_send = products[start:start+PRODUCTS_PER_PAGE]
        
        new_message_ids = []
        
        # Форматирование дат для URL
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        url_date_format = "%d.%m.%Y"
        
        # Отправка товаров с нумерацией
        for index, product in enumerate(messages_to_send):
            global_position = start + index + 1
            mpstats_url = (
                f"https://mpstats.io/wb/item/{product.id}"
                f"?d1={start_date_obj.strftime(url_date_format)}"
                f"&d2={end_date_obj.strftime(url_date_format)}"
            )
            
            msg = await bot.send_message(
                chat_id=chat_id,
                text=(
                    f"Товар №{global_position}\n"
                    f"<a href='https://www.wildberries.ru/catalog/{product.id}/detail.aspx'>wildberries</a>\n"
                    f"<a href='{mpstats_url}'>Аналитика MPStats</a>\n"
                    f"Выручка: {product.revenue:,} ₽\n"
                    f"Оборачиваемость: {product.turnover_days} дн."
                ),
                parse_mode="HTML"
            )
            new_message_ids.append(msg.message_id)
        
        # Кнопки пагинации
        builder = InlineKeyboardBuilder()
        if page > 0:
            builder.button(text="⬅ Назад", callback_data=f"prev_{page}")
        if (page + 1) * PRODUCTS_PER_PAGE < len(products):
            builder.button(text="Вперед ➡", callback_data=f"next_{page}")
        
        # Отправляем сообщение с пагинацией
        pagination_msg = await bot.send_message(
            chat_id=chat_id,
            text=f"Страница {page + 1} из {total_pages}",
            reply_markup=builder.as_markup()
        )
        new_message_ids.append(pagination_msg.message_id)
        
        # Обновляем ID сообщений в сессии
        self.user_sessions[user_id]['message_ids'] = new_message_ids

    async def _delete_previous_messages(self, user_id: int):
        """Удаляет сообщения предыдущей страницы"""
        logger.info(f"Удаление сообщений для user_id={user_id}")
        session = self.user_sessions.get(user_id, {})
        message_ids = session.get('message_ids', [])
        chat_id = session.get('chat_id')
        bot = session.get('bot')
        
        if not all([bot, chat_id, message_ids]):
            logger.warning(f"Невозможно удалить: bot={bot is not None}, chat_id={chat_id}, messages={len(message_ids)}")
            return

        try:
            logger.info(f"Удаление {len(message_ids)} сообщений...")
            for msg_id in message_ids:
                await bot.delete_message(chat_id, msg_id)
        except Exception as e:
            logger.error(f"Ошибка удаления: {str(e)}")
        
        self.user_sessions[user_id]['message_ids'] = []

paginator = PaginationManager()

async def products_command(message: types.Message, bot: Bot):
    logger.info(f"/products от {message.from_user.id}")
    
    # Вычисляем динамические даты за последние 30 дней
    today = datetime.today()
    start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")  # .replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Обновляем сессию с новыми датами
    paginator.user_sessions[message.from_user.id].update({
        'start_date': start_date,
        'end_date': end_date
    })
    
    await paginator.send_page(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        page=0,
        bot=bot,
        start_date=start_date,
        end_date=end_date
    )

async def handle_callback(callback: types.CallbackQuery, bot: Bot):
    logger.info(f"Callback от {callback.from_user.id}")
    user_id = callback.from_user.id
    
    # Получаем даты из сессии пользователя
    session_data = paginator.user_sessions.get(user_id, {})
    start_date = session_data.get('start_date')
    end_date = session_data.get('end_date')
    
    action, page_str = callback.data.split('_', 1)
    current_page = int(page_str)
    new_page = current_page - 1 if action == "prev" else current_page + 1
    
    await paginator.send_page(
        chat_id=callback.message.chat.id,
        user_id=user_id,
        page=new_page,
        bot=bot,
        start_date=start_date,
        end_date=end_date
    )
    await callback

def setup(dp: Dispatcher):
    dp.message.register(products_command, Command("products"))
    dp.callback_query.register(handle_callback)
    logger.info("Хендлеры зарегистрированы")