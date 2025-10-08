import aiohttp
from dotenv import load_dotenv
from config import logger
import os

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получаем токен из переменных окружения
MPSTATS_API_TOKEN = os.getenv('MPSTATS_API_TOKEN')

# Базовый URL для API mpstats.io
BASE_URL = "https://mpstats.io/api"


class MpstatsAPI:
    def __init__(self, token: str, base_url: str = BASE_URL):
        self.token = token
        self.base_url = base_url
        self.headers = {
            "X-Mpstats-TOKEN": self.token,
            "Content-Type": "application/json"
        }

    async def get_category_data(self, d1: str, d2: str, category_path: str) -> dict:
        """
        Получает данные о категории из API mpstats.io.

        :param d1: Начальная дата (YYYY-MM-DD)
        :param d2: Конечная дата (YYYY-MM-DD)
        :param category_path: Путь к категории
        :return: Данные о категории в формате JSON
        """
        params = {
            "d1": d1,
            "d2": d2,
            "path": category_path
        }

        # Логирование параметров запроса
        logger.info(f"Параметры запроса: {params}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/wb/get/category", headers=self.headers, params=params) as response:
                    response.raise_for_status()  # Проверяем, что запрос успешен
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка при запросе к API mpstats.io: {e}")
                return {}
            except Exception as e:
                logger.error(f"Произошла ошибка: {e}")
                return {}