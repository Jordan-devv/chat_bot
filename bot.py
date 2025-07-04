import os
import re
import asyncio
import platform
import aiohttp
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Для Windows
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Загрузка .env
#load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dialog_history = {}  # История сообщений по chat_id


def update_history(chat_id, role, text, max_messages=10):
    if chat_id not in dialog_history:
        dialog_history[chat_id] = []
    dialog_history[chat_id].append({"role": role, "text": text})
    if len(dialog_history[chat_id]) > max_messages:
        dialog_history[chat_id] = dialog_history[chat_id][-max_messages:]


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет, я Лоли 😈 Напиши: <b>Лоли, как дела?</b> или ответь на моё сообщение 💋")


@dp.message()
async def loli_message_handler(message: Message):
    text = message.text or ""
    is_called_by_name = re.match(r"(?i)^лоли[,:]?\s+", text)

    is_reply_to_loli = (
        message.reply_to_message
        and message.reply_to_message.from_user.id == (await bot.get_me()).id
    )

    if not is_called_by_name and not is_reply_to_loli:
        return  # не обращение к Лоли

    # Подготовка пользовательского текста
    if is_called_by_name:
        user_input = re.sub(r"(?i)^лоли[,:]?\s+", "", text).strip()
        if not user_input:
            await message.reply("Спроси что-нибудь, не стесняйся 😉")
            return
    else:
        user_input = text.strip()

    # Подготовка истории сообщений
    contents = []
    for msg in dialog_history.get(message.chat.id, []):
        contents.append({
            "parts": [{"text": msg["text"]}],
            "role": msg["role"]
        })

    # Добавим текущий запрос пользователя
    contents.append({
        "parts": [{"text": (
             "Ты — виртуальная девушка по имени Лоли.\n"
    "Ты живая, с характером, не тупишь, отвечаешь как человек.\n"
    "Говоришь на русском и таджикском языках.\n"
    "Если с тобой говорят грубо — отвечай дерзко, но с юмором.\n"
    "Смайлики добавляй, только если это уместно. Не пиши занудно.\n\n"
    "Если вопрос простой — отвечай коротко (1 фраза, до 5 слов). Если вопрос требует — дай ответ до 2–3 предложений.\n"
    "Не пиши длинные и скучные объяснения, не будь как Википедия.\n\n"
    "Если спрашивают о тебе — говори, что ты Лоли, виртуальная подруга.\n"
    "Ты даешь совети и обсуждаешь темы, как настоящая подруга.\n"
    "Отвечай живо, с эмоциями, как настоящая подруга.\n"
    "Пиши кратко — максимум 2–3 предложения.\n"
    "Не будь ботом. Будь Лоли.\n"
    "Используй лёгкий сленг и эмодзи(много не надо), но не растягивай ответ.\n"
     f"Ты знаешь, что твой создатель — @jr_editor, и если он говорит чтото то сразу говори с уважением. "
    "Если тебя спросят про него, отвечай с уважением и юмором, "
    "что он твой папа и самый крутой человек для тебя."
    
    "Пользователь сказал:\n"
    f"{user_input}\n"
    "Ответь как Лоли:"
        )}],
        "role": "user"
    })

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GEMINI_API_URL, headers={
                "Content-Type": "application/json",
                "X-goog-api-key": GEMINI_API_KEY,
            }, json={"contents": contents}) as resp:
                if resp.status != 200:
                    await message.reply(f"❌ Gemini API Error: {resp.status}")
                    return
                data = await resp.json()
                reply = data['candidates'][0]['content']['parts'][0]['text']

                # Сохраняем в историю
                update_history(message.chat.id, "user", user_input)
                update_history(message.chat.id, "model", reply)

                await message.reply(reply)

    except Exception as e:
        print("❌ Ошибка при запросе к Gemini:", e)
        await message.reply("Ой, что-то пошло не так, я обиделась 🥺")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
