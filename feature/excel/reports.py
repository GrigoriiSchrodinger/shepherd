from datetime import datetime, timedelta
from config import DATE_FORMAT, logger

from feature.excel.excel import MpstatsExcelReport


class ProductReportService:
    """Сервис для подготовки Excel-отчёта по товарам."""

    def __init__(self, database):
        self.database = database
        self.report_generator = MpstatsExcelReport()

    async def generate_user_report(self, username: str) -> tuple[bytes, str, str] | None:
        """Формирует отчёт для конкретного пользователя."""
        try:
            user_data = self.database.get_user(username)
            if not user_data:
                logger.warning(f"Пользователь {username} не найден в БД")
                return None

            # Получаем данные пользователя
            days = user_data["dates"]
            category = user_data["category"]
            turnover_days_max = user_data["turnover_days_max"]
            revenue_min = user_data["revenue_min"]

            # Расчёт диапазона дат
            now = datetime.now()
            end_date = (now - timedelta(days=1)).strftime(DATE_FORMAT)
            start_date = (now - timedelta(days=days)).strftime(DATE_FORMAT)

            logger.info(f"Формирование отчёта для {username}: {start_date} — {end_date}, {category}")

            # Генерация Excel
            excel_file = await self.report_generator.generate(start_date, end_date, category, turnover_days_max, revenue_min)

            # Подготовка описания
            caption = (
                "📊 Отчёт по товарам\n\n"
                f"📅 Период: {start_date} — {end_date}\n"
                f"🏷 Категория: {category}"
            )

            filename = f"WB_report_{datetime.now().strftime('%d.%m.%Y')}.xlsx"

            return excel_file.getvalue(), caption, filename

        except Exception as e:
            logger.error(f"Ошибка формирования отчёта для {username}: {e}", exc_info=True)
            return None
