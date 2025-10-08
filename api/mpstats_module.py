import json
import logging
from typing import List, Dict

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Product:
    def __init__(self, data: dict):
        self.raw_data = data  # Полные сырые данные
        self.id = data.get('nm_id', data.get('id', data.get('barcode')))
        self.name = data.get('name', 'Без названия')
        self.revenue = data.get('revenue', 0)
        logger.debug(f"Создан продукт: {self.id}")

    def _parse_nested_value(self, key: str, data: dict):
        """Рекурсивный поиск значения в данных"""
        for k, v in data.items():
            if k == key:
                return v
            if isinstance(v, dict):
                found = self._parse_nested_value(key, v)
                if found is not None:
                    return found
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        found = self._parse_nested_value(key, item)
                        if found is not None:
                            return found
        return None


class MpstatsData:
    def __init__(self, raw_data: list):
        self.products: List[Product] = []
        try:
            self.products = [Product(item) for item in raw_data]
            logger.info(f"Обработано продуктов: {len(self.products)}")
        except Exception as e:
            logger.error(f"Ошибка парсинга данных: {str(e)}")

    def filter_products(self, max_turnover_days: int, min_revenue: float) -> List[Product]:
        """
        Фильтрует продукты по заданным параметрам оборачиваемости и выручки.

        :param max_turnover_days: Максимальное количество дней оборачиваемости
        :param min_revenue: Минимальная выручка
        :return: Список отфильтрованных продуктов
        """
        filtered_products = [
            product for product in self.products
            if product.turnover_days <= max_turnover_days and product.revenue >= min_revenue
        ]
        return filtered_products

    def filter_products_with_drop(self, products: List[Product], drop_percentage: float) -> List[Product]:
        """
        Фильтрует продукты по наличию скачка в графике продаж на заданный процент.

        :param products: Список продуктов
        :param drop_percentage: Процент скачка
        :return: Список продуктов с скачком в графике продаж
        """
        filtered_products = [
            product for product in products
            if product.has_drop(drop_percentage)
        ]
        return filtered_products

    def sort_products_by_revenue(self, products: List[Product], reverse: bool = True) -> List[Product]:
        """
        Сортирует продукты по выручке.

        :param products: Список продуктов
        :param reverse: Если True, сортировка по убыванию, иначе по возрастанию
        :return: Список отсортированных продуктов
        """
        sorted_products = sorted(products, key=lambda x: x.revenue, reverse=reverse)
        return sorted_products