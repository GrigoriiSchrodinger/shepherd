import aiohttp
from dotenv import load_dotenv
from config import logger, BASE_URL, MAX_PAGE_SIZE
import os

load_dotenv()
MPSTATS_API_TOKEN = os.getenv('MPSTATS_API_TOKEN')

class MpstatsAPI:
    def __init__(self, token: str, base_url: str = BASE_URL):
        self.token = token
        self.base_url = base_url
        self.headers = {
            "X-Mpstats-TOKEN": self.token,
            "Content-Type": "application/json"
        }

    async def get_category_data(
        self,
        d1: str,
        d2: str,
        category_path: str,
        revenue_min: int = None,
        turnover_days_max: int = None
    ) -> list:
        """Получение всех товаров категории с фильтрацией на стороне API."""
        all_items = []
        start = 0

        # Формируем filterModel на основе переданных параметров
        filter_model = {}
        if revenue_min is not None:
            filter_model["revenue"] = {"filterType": "number", "type": "greaterThan", "filter": revenue_min}
        if turnover_days_max is not None:
            filter_model["turnover_days"] = {"filterType": "number", "type": "lessThan", "filter": turnover_days_max}

        async with aiohttp.ClientSession() as session:
            while True:
                payload = {
                    "startRow": start,
                    "endRow": start + MAX_PAGE_SIZE,
                    "filterModel": filter_model,  # добавили фильтры
                    "sortModel": [{"colId": "revenue", "sort": "desc"}]  # сортировка по выручке
                }

                params = {
                    "d1": d1,
                    "d2": d2,
                    "path": category_path
                }

                logger.info(f"Запрос категории: start={start}, end={start + MAX_PAGE_SIZE}")

                try:
                    async with session.post(
                        f"{self.base_url}/wb/get/category",
                        headers=self.headers,
                        params=params,
                        json=payload
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()

                        items = data.get("data", [])
                        total = data.get("total", 0)

                        all_items.extend(items)
                        logger.info(f"Загружено {len(all_items)} из {total} товаров...")

                        if len(all_items) >= total or not items:
                            break  # все данные получены

                        start += MAX_PAGE_SIZE

                except Exception as e:
                    logger.error(f"Ошибка запроса mpstats.io: {e}")
                    break

        return all_items
