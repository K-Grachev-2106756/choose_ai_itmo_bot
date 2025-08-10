import os

from dotenv import load_dotenv

load_dotenv()


data_urls = [
    ('https://api.itmo.su/constructor-ep/api/v1/static/programs/10130/plan/abit/pdf', "ai"),
    ('https://api.itmo.su/constructor-ep/api/v1/static/programs/10033/plan/abit/pdf', "ai_product")
]

data_dir = os.path.join(os.getcwd(), "data")

TG_API_TOKEN = os.getenv("TG_API_TOKEN")
HF_API_URL = os.getenv("HF_API_URL")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

program_questions = [
    "Какие у вас есть базовые знания в области ИИ?",
    "В каких направлениях ИИ вы хотите развиваться?",
    "Сколько времени готовы уделять обучению в неделю?",
    "Какие навыки планируете улучшить?",
]