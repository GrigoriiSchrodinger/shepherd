from io import BytesIO
import pandas as pd

class ExcelBuilder:
    """Утилита для построения Excel-файлов из DataFrame с минимальным потреблением памяти."""
    def __init__(self, sheet_name: str = "Отчёт"):
        self.sheet_name = sheet_name

    def build(self, df: pd.DataFrame, columns_config: dict) -> BytesIO:
        """
        Создаёт Excel-файл из DataFrame с заданной шириной колонок.
        Поддерживает гиперссылки и форматирование, возвращает BytesIO.
        """
        output = BytesIO()
        chunk_size = 5000

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet(self.sheet_name)
            writer.sheets[self.sheet_name] = worksheet

            # Заголовки
            for col_idx, col_name in enumerate(df.columns):
                worksheet.write(0, col_idx, col_name)
                col_letter = chr(65 + col_idx)
                if col_letter in columns_config:
                    worksheet.set_column(f"{col_letter}:{col_letter}", columns_config[col_letter])

            # Запись данных чанками
            row_offset = 1
            for start in range(0, len(df), chunk_size):
                df_chunk = df.iloc[start:start+chunk_size]
                for i, (_, row) in enumerate(df_chunk.iterrows()):
                    for j, col in enumerate(df.columns):
                        value = row[col]
                        if col in ("Ссылка WB", "MPStats") and isinstance(value, str) and value.startswith("http"):
                            worksheet.write_url(row_offset + i, j, value, string=value)
                        else:
                            worksheet.write(row_offset + i, j, value)
                row_offset += len(df_chunk)

        output.seek(0)
        return output
