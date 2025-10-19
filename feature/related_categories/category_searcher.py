from rapidfuzz import fuzz
from transliterate import translit
from config import logger
from feature.related_categories.category_cache import CategoryCache


class CategorySearcher:
    def __init__(self):
        self.cache = CategoryCache()
        self.categories = []

    async def load(self, force_refresh: bool = False):
        """Загружает категории из кэша или API."""
        self.categories = await self.cache.get_categories(force_refresh)

    def _transliterate_query(self, query: str) -> str:
        """Преобразует латинский запрос в кириллицу, если нужно."""
        # Если содержит латинские буквы, пробуем перевести
        if any("a" <= ch.lower() <= "z" for ch in query):
            try:
                transliterated = translit(query, "ru")
                logger.debug(f"Транслитерация: {query} -> {transliterated}")
                return transliterated
            except Exception:
                pass
        return query

    def search(self, query: str, limit: int = 10, threshold: int = 60):
        """Ищет категории по названию или пути, с учетом опечаток и латиницы."""
        if not self.categories:
            logger.warning("Категории не загружены — вызови load() перед поиском.")
            return []

        query = query.lower()
        query = self._transliterate_query(query)
        exact_matches = []
        fuzzy_matches = []

        for c in self.categories:
            name = c.get("name", "").lower()
            path = c.get("path", "").lower()

            # 1. Точное вхождение
            if query in name or query in path:
                exact_matches.append((100, c))
                continue

            # 2. Нечеткое сравнение (fuzzy)
            score = max(fuzz.partial_ratio(query, name), fuzz.partial_ratio(query, path))
            if score >= threshold:
                fuzzy_matches.append((score, c))

        # Сначала точные, потом fuzzy
        results = exact_matches + sorted(fuzzy_matches, key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]
