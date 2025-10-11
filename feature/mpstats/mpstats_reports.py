import json
import os
from typing import Tuple, List

import pandas as pd

from api.mpstats_api import MpstatsAPI
from api.mpstats_module import MpstatsData, Product
from config import logger
from feature.excel.excel import BaseExcelReport
from feature.excel.excel_builder import ExcelBuilder
from utils.formatters import (
    format_currency,
    get_turnover_value,
    get_wb_link,
    build_mpstats_link
)

class MpstatsExcelReport(BaseExcelReport):
    """Генератор Excel-отчётов по данным MPStats."""

    def __init__(self):
        self.api = MpstatsAPI(os.getenv("MPSTATS_API_TOKEN"))
        self.excel = ExcelBuilder("Товары")
        logger.info("🔧 Генератор MPStats-отчетов инициализирован")

    async def generate_report(
        self,
        start_date: str,
        end_date: str,
        category: str,
        turnover_days_max: int,
        revenue_min: int
    ):
        """Основной метод генерации отчёта."""
        try:
            self.validate_dates(start_date, end_date)
            products, _ = await self._fetch_api_data(start_date, end_date, category)
            df = self._prepare_dataframe(products, start_date, end_date, turnover_days_max, revenue_min)
            return self.excel.build(df, self._get_columns_config())

        except Exception as e:
            logger.error(f"Ошибка при создании отчёта: {e}", exc_info=True)
            raise

    async def _fetch_api_data(self, start_date: str, end_date: str, category: str) -> Tuple[List[Product], dict]:
        """Получает данные из MPStats API."""
        logger.info(f"📡 Запрос данных для категории '{category}' с {start_date} по {end_date}")
        raw_data = await self.api.get_category_data(start_date, end_date, category)
        logger.debug("Полный ответ API:\n%s", json.dumps(raw_data, indent=2, ensure_ascii=False))

        items = raw_data.get("data", []) if isinstance(raw_data, dict) else raw_data
        return MpstatsData(items).products, raw_data

    def _prepare_dataframe(
        self,
        products: List[Product],
        start_date: str,
        end_date: str,
        turnover_days_max: int,
        revenue_min: int
    ) -> pd.DataFrame:
        """Создаёт DataFrame для отчёта."""
        filtered = self._filter_products(products, turnover_days_max, revenue_min)
        logger.info(f"📦 Обработка {len(filtered)} товаров из {len(products)}")

        rows = []
        for idx, product in enumerate(filtered, start=1):
            try:
                rows.append(self._product_to_row(idx, product, start_date, end_date))
            except Exception as e:
                logger.error(f"Ошибка обработки товара #{idx}: {e}")

        return pd.DataFrame(rows)

    @staticmethod
    def _filter_products(products: List[Product], turnover_days_max: int, revenue_min: int) -> List[Product]:
        """Фильтрует товары по критериям."""
        return [
            p for p in products
            if p.turnover_days < turnover_days_max and p.revenue > revenue_min
        ]

    @staticmethod
    def _product_to_row(idx: int, product: Product, start_date: str, end_date: str) -> dict:
        """Преобразует товар в строку отчёта."""
        return {
            "№": idx,
            "Название": product.name,
            "Выручка": format_currency(product.revenue),
            "Оборачиваемость": get_turnover_value(product.raw_data),
            "Ссылка WB": get_wb_link(product.id),
            "MPStats": build_mpstats_link(product.id, start_date, end_date),
        }

    @staticmethod
    def _get_columns_config() -> dict:
        """Возвращает настройки ширины колонок."""
        return {
            "A": 8,   # №
            "B": 50,  # Название
            "C": 20,  # Выручка
            "D": 20,  # Оборачиваемость
            "E": 50,  # Ссылка WB
            "F": 60,  # MPStats
        }

