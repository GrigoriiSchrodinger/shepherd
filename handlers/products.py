import os
import json
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Dict

import pandas as pd
from aiogram import Dispatcher, types, Bot
from aiogram.filters import Command

from api.mpstats_api import MpstatsAPI
from api.mpstats_module import MpstatsData, Product
from config import logger

DATE_FORMAT = "%Y-%m-%d"
DEFAULT_CATEGORY = "Женщинам/Толстовки, свитшоты и худи"

class ExcelReportGenerator:
    def __init__(self):
        self.api = MpstatsAPI(os.getenv('MPSTATS_API_TOKEN'))
        logger.info("Генератор отчетов инициализирован")

    async def generate_excel_report(
        self,
        start_date: str,
        end_date: str,
        category: str = DEFAULT_CATEGORY
    ) -> BytesIO:
        try:
            self._validate_dates(start_date, end_date)
            products, raw_response = await self._fetch_api_data(start_date, end_date, category)
            df = self._prepare_report_data(products, start_date, end_date)
            return self._create_excel(df)

        except Exception as e:
            logger.error(f"Ошибка при создании отчета: {str(e)}", exc_info=True)
            raise

    def _validate_dates(self, start_date: str, end_date: str) -> None:
        now = datetime.now().date()
        
        try:
            start_dt = datetime.strptime(start_date, DATE_FORMAT).date()
            end_dt = datetime.strptime(end_date, DATE_FORMAT).date()
        except ValueError as e:
            raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD") from e

        if start_dt > end_dt:
            raise ValueError("Дата начала не может быть позже даты окончания")
            
        if start_dt > now or end_dt > now:
            logger.warning("⚠️ Используются даты из будущего")

    async def _fetch_api_data(
        self,
        start_date: str,
        end_date: str,
        category: str
    ) -> tuple[List[Product], dict]:
        logger.info(f"Запрос данных для {category} с {start_date} по {end_date}")
        raw_data = await self.api.get_category_data(start_date, end_date, category)
        logger.debug("Полный ответ API:\n%s", json.dumps(raw_data, indent=2, ensure_ascii=False))
        items = raw_data.get("data", []) if isinstance(raw_data, dict) else raw_data
        return MpstatsData(items).products, raw_data

    def _prepare_report_data(
        self,
        products: List[Product],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        report = []
        logger.info(f"Обработка {len(products)} продуктов")
        
        for idx, product in enumerate(products, 1):
            try:
                report.append({
                    '№': idx,
                    'Название': product.name,
                    'Выручка': self._format_currency(getattr(product, 'revenue', 0)),
                    'Оборачиваемость': self._get_turnover_value(product.raw_data),
                    'Ссылка WB': self._get_wb_link(product.id),
                    'MPStats': self._build_mpstats_link(product.id, start_date, end_date)
                })
            except Exception as e:
                logger.error(f"Ошибка обработки продукта #{idx}: {str(e)}")
        return pd.DataFrame(report)

    def _get_turnover_value(self, raw_data: Dict) -> str:
        """Получение значения оборачиваемости из turnover_days"""
        try:
            # Получаем значение дней оборачиваемости
            turnover_days = raw_data.get('turnover_days')
            
            # Если параметр отсутствует в данных
            if turnover_days is None:
                logger.warning("Параметр turnover_days отсутствует в данных")
                return "Н/Д"
            
            # Форматируем целое число дней
            return f"{int(turnover_days)} дн."

        except Exception as e:
            logger.error(f"Ошибка обработки оборачиваемости: {str(e)}")
            return "Ошибка"

    def _get_wb_link(self, product_id: int) -> str:
        return f"https://www.wb.ru/catalog/{product_id}/detail.aspx"

    def _build_mpstats_link(
        self,
        product_id: int,
        start_date: str,
        end_date: str
    ) -> str:
        start_fmt = datetime.strptime(start_date, DATE_FORMAT).strftime("%d.%m.%Y")
        end_fmt = datetime.strptime(end_date, DATE_FORMAT).strftime("%d.%m.%Y")
        return f"https://mpstats.io/wb/item/{product_id}?d1={start_fmt}&d2={end_fmt}"

    def _format_currency(self, value: float) -> str:
        return f"{int(value):,} ₽".replace(',', ' ') if value > 0 else "Нет данных"

    def _create_excel(self, df: pd.DataFrame) -> BytesIO:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Товары')
            
            workbook = writer.book
            worksheet = writer.sheets['Товары']
            
            columns_config = {
                'A': 10,  # №
                'B': 50,  # Название
                'C': 20,  # Выручка
                'D': 20,  # Оборачиваемость
                'E': 50,  # Ссылка WB
                'F': 60   # MPStats
            }
            
            for col, width in columns_config.items():
                worksheet.set_column(f'{col}:{col}', width)
                
        output.seek(0)
        return output

report_generator = ExcelReportGenerator()


async def products_command(message: types.Message, bot: Bot) -> None:
    try:
        now = datetime.now()
        end_date = (now - timedelta(days=1)).strftime(DATE_FORMAT)
        start_date = (now - timedelta(days=30)).strftime(DATE_FORMAT)
        category = DEFAULT_CATEGORY

        processing_msg = await message.answer("⏳ Формируем отчет...")
        excel_file = await report_generator.generate_excel_report(start_date, end_date)

        
        caption = (
            "📊 Отчет по товарам\n\n"
            "📋 Параметры генерации:\n"
            f"• Дата начала: {start_date}\n"
            f"• Дата окончания: {end_date}\n"
            f"• Категория: {category}"
        )
        
        await message.answer_document(
            types.BufferedInputFile(
                file=excel_file.getvalue(),
                filename=f"WB_report_{datetime.now().strftime('%d.%m.%Y')}.xlsx"
            ),
            caption=caption
        )

        await bot.delete_message(
            chat_id=processing_msg.chat.id,
            message_id=processing_msg.message_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка команды: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}")

def setup(dp: Dispatcher) -> None:
    dp.message.register(products_command, Command("products"))
    logger.info("Команда /products зарегистрирована")