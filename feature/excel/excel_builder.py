from io import BytesIO
import pandas as pd


class ExcelBuilder:
    """Утилита для построения Excel-файлов из DataFrame."""

    def __init__(self, sheet_name: str = "Отчёт"):
        self.sheet_name = sheet_name

    def build(self, df: pd.DataFrame, columns_config: dict) -> BytesIO:
        """
        Создаёт Excel-файл из DataFrame с заданной шириной колонок.
        Работает с гиперссылками и форматами, возвращает BytesIO.
        """
        output = BytesIO()
        chunk_size = 10000  # запись чанками для экономии памяти

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            # создаём пустой Excel с листом
            df_head = df.head(0)  # заголовки без данных
            df_head.to_excel(writer, index=False, sheet_name=self.sheet_name)
            worksheet = writer.sheets[self.sheet_name]

            # задаём ширину колонок
            for col, width in columns_config.items():
                worksheet.set_column(f"{col}:{col}", width)

            # записываем данные чанками
            for start in range(0, len(df), chunk_size):
                df_chunk = df.iloc[start:start+chunk_size]
                df_chunk.to_excel(writer, index=False, header=False, startrow=start+1, sheet_name=self.sheet_name)

        output.seek(0)
        return output
