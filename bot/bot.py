import asyncio
import logging
import os
from nlu_parser import parse_intent
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from recognizer import ogg_2_wav, recognize_speech
import requests
from database import (
    init_db, add_user, add_note, add_reminder,
    get_notes, get_reminders, delete_note, delete_reminder
)

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
RASA_URL = os.getenv("RASA_URL", "http://rasa:5005")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

logging.basicConfig(level=logging.INFO)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await add_user(message.from_user.id, message.from_user.username)

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Создать заметку")],
            [types.KeyboardButton(text="Создать напоминание")],
            [types.KeyboardButton(text="Посмотреть записи")]
        ],
        resize_keyboard=True
    )

    await message.answer("Привет! Выбери действие:", reply_markup=keyboard)

# ========== /help ==========
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Возможности:\n"
        "- Отправь голосовое сообщение — я сам всё пойму.\n"
        "- Либо используй текстовое меню.\n\n"
        "Команды:\n"
        "/start — перезапуск\n"
        "/help — помощь"
    )

# ========== buttons ==========
@router.message(F.text)
async def handle_buttons(message: Message):
    text = message.text.strip()

    if text == "Создать заметку":
        await message.answer("Отправь голосовое сообщение с заметкой")

    elif text == "Создать напоминание":
        await message.answer("Отправь голосовое сообщение с напоминанием")

    elif text == "Посмотреть записи":
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Мои заметки"), types.KeyboardButton(text="Мои напоминания")],
                [types.KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        )
        await message.answer("Что хочешь посмотреть?", reply_markup=keyboard)

    elif text == "Мои заметки":
        notes = await get_notes(message.from_user.id)
        if notes:
            for n_id, note_text in notes:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="Удалить", callback_data=f"delete_note:{n_id}")]]
                )
                await message.answer(note_text, reply_markup=keyboard)
        else:
            await message.answer("Нет заметок.")

    elif text == "Мои напоминания":
        reminders = await get_reminders(message.from_user.id)
        if reminders:
            for r_id, reminder_text in reminders:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="Удалить", callback_data=f"delete_reminder:{r_id}")]]
                )
                await message.answer(reminder_text, reply_markup=keyboard)
        else:
            await message.answer("Нет напоминаний.")

    elif text == "Назад":
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Создать заметку")],
                [types.KeyboardButton(text="Создать напоминание")],
                [types.KeyboardButton(text="Посмотреть записи")]
            ],
            resize_keyboard=True
        )
        await message.answer("Главное меню.", reply_markup=keyboard)

    else:
        await message.answer("Непонятная команда. Используй меню или отправь голосовое сообщение.")

# ========== whisper + rasa ==========
@router.message(F.voice)
async def voice_handler(message: Message):
    try:
        add_user(message.from_user.id, message.from_user.username)

        voice = message.voice
        file = await bot.get_file(voice.file_id)
        downloaded_file = await bot.download_file(file.file_path)

        ogg_path = f"voice_{message.message_id}.ogg"
        wav_path = f"voice_{message.message_id}.wav"

        with open(ogg_path, "wb") as f:
            f.write(downloaded_file.read())

        await ogg_2_wav(ogg_path, wav_path)
        text = await recognize_speech(wav_path)
        await message.answer(f"Распознан текст:\n{text}")

        lowered_text = text.lower()

        if lowered_text.startswith("создай заметку"):
            intent = "create_note"
            confidence = 1.0
        elif lowered_text.startswith("создай напоминание"):
            intent = "create_reminder"
            confidence = 1.0
        else:
            intent_result = await parse_intent(text)
            intent = intent_result["intent"]
            confidence = intent_result["confidence"]

        if confidence > 0.7:
            if intent == "create_note":
                await add_note(message.from_user.id, text)
                await message.answer("Заметка добавлена.")
            elif intent == "create_reminder":
                await add_reminder(message.from_user.id, text)
                await message.answer("Напоминание добавлено.")
            else:
                await message.answer("Не понял, что нужно сделать. Попробуй еще раз.")
        else:
            await message.answer("Я не уверен в распознавании команды. Попробуй сказать по-другому.")

    except Exception as e:
        logging.error(f"[VOICE_HANDLER ERROR] {message.from_user.id}: {str(e)}")
        await message.answer("Ошибка при обработке голосового сообщения.")
    finally:
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

# ========== delete ==========
@router.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data
    if data.startswith("delete_note:"):
        note_id = int(data.split(":")[1])
        await delete_note(note_id)
        await callback.message.edit_text("Заметка удалена.")
        await callback.answer()

    elif data.startswith("delete_reminder:"):
        reminder_id = int(data.split(":")[1])
        await delete_reminder(reminder_id)
        await callback.message.edit_text("Напоминание удалено.")
        await callback.answer()

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
