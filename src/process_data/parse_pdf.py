import os

import camelot

from src.config import data_dir


for file in os.listdir(data_dir):
    tables = camelot.read_pdf(os.path.join(data_dir, file), pages='all')

    # Выведем первую таблицу
    print(tables[0].df)

    # Сохраним в CSV, чтобы удобно было работать
    tables[0].to_csv(os.path.join(data_dir, "".join(file.split(".")[:-1]) + ".csv"))