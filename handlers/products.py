import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from aiogram import Dispatcher, types, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from api.mpstats_api import MpstatsAPI
from api.mpstats_module import MpstatsData

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Конфигурация
PRODUCTS_PER_PAGE = 5
DATE_FORMAT = "%Y-%m-%d"
DEFAULT_CATEGORY = "Женщинам/Толстовки, свитшоты и худи/Свитшот"


class PaginationManager:
    """Управление пагинацией и пользовательскими сессиями"""
    
    def __init__(self):
        self.api = MpstatsAPI(os.getenv('MPSTATS_API_TOKEN'))
        self.user_sessions: Dict[int, Dict[str, Any]] = defaultdict(dict)
        logger.info("Инициализирован PaginationManager")

    async def fetch_products(self, start_date: str, end_date: str, category: str = DEFAULT_CATEGORY) -> MpstatsData:
        """Загрузка данных из MPStats""" 
        try:
            data = await self.api.get_category_data(start_date, end_date, category)
            products = MpstatsData(data.get("data", []))
            filtered = products.filter_products(30, 200_000)
            return products.sort_products_by_revenue(
                products.filter_products_with_drop(filtered, 20)
            )
        except Exception as e:
            logger.error(f"Ошибка получения данных: {str(e)}")
            return MpstatsData([])

    async def send_page(
        self,
        chat_id: int,
        user_id: int,
        page: int,
        bot: Bot,
        start_date: str,
        end_date: str
    ) -> None:
        """Отправка страницы с товарами и пагинацией"""
        # Обновление данных сессии
        self.user_sessions[user_id].update({
            'chat_id': chat_id,
            'bot': bot,
            'start_date': start_date,
            'end_date': end_date
        })
        
        await self._cleanup_previous_messages(user_id)
        products = await self.fetch_products(start_date, end_date)
        total_pages = (len(products) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
        
        # Отправка товаров текущей страницы
        messages = [
            await self._send_product_message(bot, chat_id, product, page, i, user_id)
            for i, product in enumerate(products[page*PRODUCTS_PER_PAGE:(page+1)*PRODUCTS_PER_PAGE])
        ]
        
        # Отправка пагинации
        pagination_msg = await self._send_pagination_controls(bot, chat_id, page, total_pages, products)
        self.user_sessions[user_id]['message_ids'] = [msg.message_id for msg in messages] + [pagination_msg.message_id]

    async def _cleanup_previous_messages(self, user_id: int) -> None:
        """Удаление предыдущих сообщений"""
        if not (session := self.user_sessions.get(user_id)):
            return
            
        bot, chat_id = session.get('bot'), session.get('chat_id')
        message_ids = session.get('message_ids', [])
        
        if not bot or not chat_id:
            return

        for msg_id in message_ids:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения: {str(e)}")

    async def _send_product_message(
        self,
        bot: Bot,
        chat_id: int,
        product: Any,
        page: int,
        index: int,
        user_id: int  # Добавлен обязательный user_id
    ) -> types.Message:
        """Отправка сообщения с товаром"""
        position = page * PRODUCTS_PER_PAGE + index + 1
        
        # Получение дат из сессии пользователя
        start_date_str = self.user_sessions[user_id]['start_date']
        end_date_str = self.user_sessions[user_id]['end_date']
        
        # Форматирование дат для URL
        start_date = datetime.strptime(start_date_str, DATE_FORMAT).strftime("%d.%m.%Y")
        end_date = datetime.strptime(end_date_str, DATE_FORMAT).strftime("%d.%m.%Y")

        return await bot.send_message(
            chat_id=chat_id,
            text=(
                f"Товар №{position}\n"
                f"<a href='https://www.wildberries.ru/catalog/{product.id}/detail.aspx'>Wildberries</a>\n"
                f"<a href='https://mpstats.io/wb/item/{product.id}?d1={start_date}&d2={end_date}'>MPStats</a>\n"
                f"Выручка: {product.revenue:,} ₽\n"
                f"Оборачиваемость: {product.turnover_days} дн."
            ),
            parse_mode="HTML"
        )

    async def _send_pagination_controls(
        self,
        bot: Bot,
        chat_id: int,
        current_page: int,
        total_pages: int,
        products: list
    ) -> types.Message:
        """Кнопки пагинации"""
        builder = InlineKeyboardBuilder()
        if current_page > 0:
            builder.button(text="⬅ Назад", callback_data=f"prev_{current_page}")
        if (current_page + 1) * PRODUCTS_PER_PAGE < len(products):
            builder.button(text="Вперед ➡", callback_data=f"next_{current_page}")
        
        return await bot.send_message(
            chat_id=chat_id,
            text=f"Страница {current_page + 1} из {total_pages}",
            reply_markup=builder.as_markup()
        )


paginator = PaginationManager()


async def products_command(message: types.Message, bot: Bot) -> None:
    """Обработчик команды /products"""
    start_date = (datetime.now() - timedelta(days=30)).strftime(DATE_FORMAT)
    end_date = datetime.now().strftime(DATE_FORMAT)
    
    await paginator.send_page(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        page=0,
        bot=bot,
        start_date=start_date,
        end_date=end_date
    )


async def handle_callback(callback: types.CallbackQuery, bot: Bot) -> None:
    """Обработчик действий пагинации"""
    user_id = callback.from_user.id
    action, current_page = callback.data.split('_', 1)
    current_page = int(current_page)

    session_data = paginator.user_sessions.get(user_id, {})
    new_page = current_page - 1 if action == "prev" else current_page + 1
    
    await paginator.send_page(
        chat_id=callback.message.chat.id,
        user_id=user_id,
        page=new_page,
        bot=bot,
        start_date=session_data.get('start_date'),
        end_date=session_data.get('end_date')
    )
    await callback.answer()


def setup(dp: Dispatcher) -> None:
    dp.message.register(products_command, Command("products"))
    dp.callback_query.register(handle_callback)
    logger.info("Хендлеры успешно зарегистрированы")