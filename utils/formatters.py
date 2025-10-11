from datetime import datetime
from config import DATE_FORMAT


def format_currency(value: float) -> str:
    """Форматирует число как валюту."""
    return f"{int(value):,} ₽".replace(",", " ") if value > 0 else "Нет данных"


def get_turnover_value(raw_data: dict) -> str:
    """Возвращает значение оборачиваемости."""
    turnover_days = raw_data.get("turnover_days")
    return f"{int(turnover_days)} дн." if turnover_days else "Н/Д"


def get_wb_link(product_id: int) -> str:
    """Возвращает ссылку на карточку WB."""
    return f"https://www.wb.ru/catalog/{product_id}/detail.aspx"


def build_mpstats_link(product_id: int, start_date: str, end_date: str) -> str:
    """Формирует ссылку на MPStats."""
    start_fmt = datetime.strptime(start_date, DATE_FORMAT).strftime("%d.%m.%Y")
    end_fmt = datetime.strptime(end_date, DATE_FORMAT).strftime("%d.%m.%Y")
    return f"https://mpstats.io/wb/item/{product_id}?d1={start_fmt}&d2={end_fmt}"
