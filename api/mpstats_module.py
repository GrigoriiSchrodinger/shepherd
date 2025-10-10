from typing import List

from config import logger

class Product:
    def __init__(self, data: dict):
        self.raw_data = data
        self.id = data.get('nm_id', data.get('id', data.get('barcode')))
        self.name = data.get('name', 'Без названия')
        self.revenue = data.get('revenue', 0)
        self.turnover_days = data.get('turnover_days', 0)
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