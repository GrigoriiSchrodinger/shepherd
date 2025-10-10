import os
import json
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Tuple

import pandas as pd

from api.mpstats_api import MpstatsAPI
from api.mpstats_module import MpstatsData, Product
from config import logger, DATE_FORMAT


# === Базовый класс ===
class BaseExcelReport:
    """Базовый класс для генерации Excel-отчётов."""

    @staticmethod
    def _validate_dates(start_date: str, end_date: str) -> None:
        """Проверяет корректность диапазона дат."""
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

    @staticmethod
    def _format_currency(value: float) -> str:
        """Форматирует число как валюту."""
        return f"{int(value):,} ₽".replace(",", " ") if value > 0 else "Нет данных"

    @staticmethod
    def _create_excel(df: pd.DataFrame, columns_config: Dict[str, int], sheet_name: str = "Отчёт") -> BytesIO:
        """Создаёт Excel-файл из DataFrame."""
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            worksheet = writer.sheets[sheet_name]

            for col, width in columns_config.items():
                worksheet.set_column(f"{col}:{col}", width)

        output.seek(0)
        return output


# === Класс-наследник для MPStats ===
class MpstatsExcelReport(BaseExcelReport):
    """Генератор Excel-отчётов по данным MPStats."""

    def __init__(self):
        self.api = MpstatsAPI(os.getenv("MPSTATS_API_TOKEN"))
        logger.info("🔧 Генератор MPStats-отчетов инициализирован")

    async def generate(self, start_date: str, end_date: str, category: str) -> BytesIO:
        """Основной метод генерации отчёта."""
        try:
            self._validate_dates(start_date, end_date)
            products, _ = await self._fetch_api_data(start_date, end_date, category)
            df = self._prepare_dataframe(products, start_date, end_date)
            return self._create_excel(df, self._get_columns_config(), "Товары")

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

    def _prepare_dataframe(self, products: List[Product], start_date: str, end_date: str) -> pd.DataFrame:
        """Создаёт DataFrame для отчёта."""
        report_rows = []
        logger.info(f"📦 Обработка {len(products)} товаров")

        for idx, product in enumerate(products, start=1):
            try:
                if product.turnover_days < 10 and product.revenue > 300_000:
                    report_rows.append({
                        "№": idx,
                        "Название": product.name,
                        "Выручка": self._format_currency(product.revenue),
                        "Оборачиваемость": self._get_turnover_value(product.raw_data),
                        "Ссылка WB": self._get_wb_link(product.id),
                        "MPStats": self._build_mpstats_link(product.id, start_date, end_date)
                    })
            except Exception as e:
                logger.error(f"Ошибка обработки товара #{idx}: {e}")

        return pd.DataFrame(report_rows)

    @staticmethod
    def _get_turnover_value(raw_data: Dict) -> str:
        """Возвращает значение оборачиваемости."""
        turnover_days = raw_data.get("turnover_days")
        if turnover_days is None:
            logger.warning("⏳ Параметр turnover_days отсутствует")
            return "Н/Д"
        return f"{int(turnover_days)} дн."

    @staticmethod
    def _get_wb_link(product_id: int) -> str:
        return f"https://www.wb.ru/catalog/{product_id}/detail.aspx"

    @staticmethod
    def _build_mpstats_link(product_id: int, start_date: str, end_date: str) -> str:
        start_fmt = datetime.strptime(start_date, DATE_FORMAT).strftime("%d.%m.%Y")
        end_fmt = datetime.strptime(end_date, DATE_FORMAT).strftime("%d.%m.%Y")
        return f"https://mpstats.io/wb/item/{product_id}?d1={start_fmt}&d2={end_fmt}"

    @staticmethod
    def _get_columns_config() -> Dict[str, int]:
        """Возвращает настройки ширины колонок."""
        return {
            "A": 8,   # №
            "B": 50,  # Название
            "C": 20,  # Выручка
            "D": 20,  # Оборачиваемость
            "E": 50,  # Ссылка WB
            "F": 60,  # MPStats
        }
