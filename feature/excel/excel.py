from datetime import datetime
from config import logger, DATE_FORMAT


class BaseExcelReport:
    """Базовый класс для генерации Excel-отчётов."""

    @staticmethod
    def validate_dates(start_date: str, end_date: str) -> tuple:
        """Проверяет корректность диапазона дат и возвращает datetime-объекты."""
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

        return start_dt, end_dt