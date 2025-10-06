import logging
from typing import List, Dict

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Product:
    def __init__(self, data: Dict):
        self.id = data.get("id")
        self.name = data.get("name")
        self.revenue = data.get("revenue")
        self.turnover_days = data.get("turnover_days")
        self.graph = data.get("graph", [])

    def __repr__(self):
        return f"Product(id={self.id}, name={self.name}, revenue={self.revenue}, turnover_days={self.turnover_days})"

    def has_drop(self, drop_percentage: float) -> bool:
        """
        Проверяет, есть ли скачок в графике продаж на заданный процент.

        :param drop_percentage: Процент скачка
        :return: True, если скачок присутствует, иначе False
        """
        if not self.graph or len(self.graph) < 2:
            return False

        for i in range(1, len(self.graph)):
            if self.graph[i] < self.graph[i - 1]:
                drop = (self.graph[i - 1] - self.graph[i]) / self.graph[i - 1] * 100
                if drop >= drop_percentage:
                    return True
        return False


class MpstatsData:
    def __init__(self, data: List[Dict]):
        self.products = [Product(product_data) for product_data in data]

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