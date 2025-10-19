import os
import json
import time

from api.mpstats_api import MpstatsAPI
from config import logger

CACHE_FILE = "categories.json"
CACHE_TTL = 60 * 60 * 24  # 24 часа


class CategoryCache:
    def __init__(self):
        self.api = MpstatsAPI()

    async def get_categories(self, force_refresh: bool = False):
        """Возвращает список категорий (из кэша или API)."""
        if not force_refresh and self._is_cache_valid():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Категории загружены из кэша ({len(data)}).")
                    return data
            except Exception as e:
                logger.warning(f"Ошибка чтения кэша: {e}")

        logger.info("Обновление категорий с API MPStats...")
        data = await self.api.get_categories()
        self._save_cache(data)
        return data

    def _is_cache_valid(self) -> bool:
        """Проверяет, не устарел ли кэш."""
        if not os.path.exists(CACHE_FILE):
            return False
        mtime = os.path.getmtime(CACHE_FILE)
        return (time.time() - mtime) < CACHE_TTL

    def _save_cache(self, data: list):
        """Сохраняет данные в кэш."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Категории сохранены в кэш ({CACHE_FILE}).")
        except Exception as e:
            logger.error(f"Ошибка при сохранении категорий: {e}")
