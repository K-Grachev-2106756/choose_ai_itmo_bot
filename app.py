import logging
import re

from aiogram import Bot, Dispatcher, executor, types
from huggingface_hub import InferenceClient

from src.config import HF_API_TOKEN, TG_API_TOKEN, program_questions, HF_API_MODEL
from src.process_data.utils import load_plan

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TG_API_TOKEN)
dp = Dispatcher(bot)
client = InferenceClient(
    provider="auto",
    api_key=HF_API_TOKEN,  # или просто подставь HF_API_TOKEN
)

ai_plan, ai_product_plan = load_plan("ai"), load_plan("ai_product")

# Состояния пользователя и данные сессии (в памяти)
user_sessions = {}

# Вспомогательная функция обращения к Hugging Face Inference API
def query_hf_model(prompt: str) -> str:
    """
    Запрос к модели Hugging Face через InferenceClient.
    Предполагается, что используется текстовая модель, поддерживающая text_generation.
    """
    try:
        # Запрос генерации текста
        output = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=HF_API_MODEL,  # или нужная тебе модель
            # parameters={"max_new_tokens": 150, "return_full_text": False}
        )
        # output — это список словарей с ключом 'generated_text'
        if output:
            generated_text = re.sub(r"<think>.*?</think>", "", output.choices[0].message.content, flags=re.DOTALL).strip()
            return generated_text if generated_text else "Даже не знаю что сказать."
        else:
            return "Не удалось получить ответ от модели."
    except Exception as e:
        return f"Ошибка запроса к HF модели: {e}"

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Задать вопрос", "Выбрать программу обучения")
    await message.answer("Привет, абитуриент! AI ИЛИ AI-PRODUCT: что выберешь именно ты?", reply_markup=keyboard)

# Обработка нажатий на кнопки
@dp.message_handler(lambda message: message.text == "Задать вопрос")
async def handle_ask_question(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("AI", "AI-PRODUCT")
    await message.answer("По какой программе вы бы хотели узнать подробнее?", reply_markup=keyboard)
    user_sessions[message.from_user.id] = {"mode": "choose_program_for_question"}

@dp.message_handler(lambda message: message.text == "Выбрать программу обучения")
async def handle_choose_program(message: types.Message):
    await message.answer("Сейчас я задам вам несколько вопросов, чтобы подобрать лучшие дисциплины.")
    user_sessions[message.from_user.id] = {
        "mode": "choose_program",
        "answers": [],
        "current_q": 0
    }
    # Задаем первый вопрос
    await message.answer(program_questions[0])

# Обработка обычных сообщений
@dp.message_handler()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    session = user_sessions.get(user_id)

    if not session:
        await message.answer("Пожалуйста, выберите действие с помощью кнопок.")
        return

    mode = session.get("mode")

    if mode == "choose_program_for_question":
        # Сохраняем выбор программы
        program = message.text.upper()
        if program not in ["AI", "AI-PRODUCT"]:
            await message.answer("Пожалуйста, выберите одну из программ: AI или AI-PRODUCT.")
            return

        # Сохраняем программу в сессию
        session["program"] = program

        # Загружаем инфо по учебному плану в текст (например, берем только таблицу и делаем строку)
        plan_text = ai_plan if program == "AI" else ai_product_plan
        
        session["plan_info"] = plan_text
        session["mode"] = "ask_question_with_context"

        await message.answer("Отлично! Теперь задайте ваш вопрос по этой программе.")

    elif mode == "ask_question_with_context":
        # Получаем вопрос пользователя
        user_question = message.text
        program = session.get("program")
        plan_info = session.get("plan_info", "")

        prompt = (
            f"Ты — помощник по учебному плану магистратуры по программе {program}. "
            "Вот информация о дисциплинах:\n"
            f"{plan_info}\n\n"
            "Если вопрос не относится к учебному плану, ответь 'не могу подсказать'.\n"
            f"Вопрос пользователя: {user_question}\n"
            "Ответ:"
        )

        response = query_hf_model(prompt)
        await message.answer(response)

        # Завершаем сессию
        user_sessions.pop(user_id)

    elif mode == "ask_question":
        # Если остался старый режим, просто предложи выбрать действие
        await message.answer("Пожалуйста, сначала выберите программу, по которой хотите задать вопрос.")

    elif mode == "choose_program":
        # Тут логика "выбрать программу обучения" (как было)
        session["answers"].append(message.text)
        session["current_q"] += 1

        if session["current_q"] < len(program_questions):
            await message.answer(program_questions[session["current_q"]])
        else:
            answers_text = "\n".join(f"Вопрос: {q}\nОтвет: {a}" for q, a in zip(program_questions, session["answers"]))
            prompt = (
                "Ты — помощник по учебному плану магистратуры по искусственному интеллекту. "
                "Используй данные ответы пользователя и информацию об учебном плане, чтобы порекомендовать, какие дисциплины лучше прослушать.\n"
                f"{answers_text}\n"
                f"Дисциплины на направлении 'Искусственный интеллект':\n{ai_plan}\n"
                f"Дисциплины на направлении 'Управление ИИ-продуктами/AI Product':\n{ai_product_plan}\n"
                "Дай развернутый ответ и рекомендации."
            )
            response = query_hf_model(prompt)
            await message.answer(response)
            user_sessions.pop(user_id)

    else:
        await message.answer("Пожалуйста, выберите действие с помощью кнопок.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
