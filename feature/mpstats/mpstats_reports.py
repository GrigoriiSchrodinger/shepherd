import json
import os
from datetime import datetime
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
        revenue_min: int,
        drop_threshold_percent: float
    ):
        """Основной метод генерации отчёта."""
        try:
            self.validate_dates(start_date, end_date)
            products, _ = await self._fetch_api_data(start_date, end_date, category)
            df = self._prepare_dataframe(products, start_date, end_date, turnover_days_max, revenue_min, drop_threshold_percent)
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
        revenue_min: int,
        drop_threshold_percent: float
    ) -> pd.DataFrame:
        """Создаёт DataFrame для отчёта."""
        filtered = self._filter_products(products, turnover_days_max, revenue_min, start_date, end_date, drop_threshold_percent)
        logger.info(f"📦 Обработка {len(filtered)} товаров из {len(products)}")

        rows = []
        for idx, product in enumerate(filtered, start=1):
            try:
                rows.append(self._product_to_row(idx, product, start_date, end_date))
            except Exception as e:
                logger.error(f"Ошибка обработки товара #{idx}: {e}")

        return pd.DataFrame(rows)

    @staticmethod
    def _filter_products(
            products: List[Product],
            turnover_days_max: int,
            revenue_min: int,
            start_date: str,
            end_date: str,
            drop_threshold_percent: float
    ) -> List[Product]:
        """Фильтрует товары по обороту, выручке, дате первого SKU и резкому падению остатков."""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        def has_sharp_drop(stocks_graph: List[int]) -> bool:
            """Проверяет резкое падение остатков по графику."""
            if not stocks_graph or len(stocks_graph) < 2:
                return False
            for i in range(len(stocks_graph) - 1):
                current = stocks_graph[i]
                next_val = stocks_graph[i + 1]
                if current == 0:
                    continue
                drop_percent = (current - next_val) / current * 100
                if drop_percent >= drop_threshold_percent:
                    return True
            return False

        filtered = []
        for p in products:
            # Проверяем оборот и выручку
            if p.turnover_days >= turnover_days_max or p.revenue <= revenue_min:
                continue

            # Проверяем sku_first_date
            if p.sku_first_date:
                try:
                    sku_dt = datetime.strptime(p.sku_first_date, "%Y-%m-%d")
                    if not (start_dt <= sku_dt <= end_dt):
                        continue
                except Exception:
                    # если дата некорректная, пропускаем фильтр
                    pass

            # Проверяем резкое падение остатков
            stocks_graph = p.raw_data.get("stocks_graph", [])
            if not has_sharp_drop(stocks_graph):
                continue

            filtered.append(p)
        return filtered

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

