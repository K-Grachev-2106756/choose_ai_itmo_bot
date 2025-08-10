import os
import requests

from src.config import data_urls, data_dir


os.makedirs(data_dir, exist_ok=True)

for url, name in data_urls:
    response = requests.get(url)
    response.raise_for_status()

    filename = os.path.join(data_dir, f"uchebny_plan_{name}.pdf")

    with open(filename, 'wb') as f:
        f.write(response.content)

    print(f'Файл сохранён в {filename}')
