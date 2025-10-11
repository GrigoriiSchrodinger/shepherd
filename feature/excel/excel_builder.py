from io import BytesIO
import pandas as pd


class ExcelBuilder:
    """Утилита для построения Excel-файлов из DataFrame."""

    def __init__(self, sheet_name: str = "Отчёт"):
        self.sheet_name = sheet_name

    def build(self, df: pd.DataFrame, columns_config: dict) -> BytesIO:
        """Создаёт Excel-файл из DataFrame с заданной шириной колонок."""
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name=self.sheet_name)
            worksheet = writer.sheets[self.sheet_name]
            for col, width in columns_config.items():
                worksheet.set_column(f"{col}:{col}", width)
        output.seek(0)
        return output
