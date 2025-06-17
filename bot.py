from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from PIL import Image
import pytesseract
import os
import fitz  # PyMuPDF
from langdetect import detect
from docx import Document
from datetime import datetime
import logging
import json
import csv

TOKEN = "8187242209:AAE8ZsXRJHfpqlr5-pfICIFZ33hl5RGUvTQ"
ADMIN_CHAT_ID = 984818559

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
log = logging.getLogger()

user_format_choice = {}

def extract_text_from_image(path):
    image = Image.open(path)
    lang = detect(pytesseract.image_to_string(image))
    return pytesseract.image_to_string(image, lang=lang)

def extract_table_from_image(path):
    image = Image.open(path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    rows = []
    current_line = []
    last_top = None
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        if not word:
            continue
        top = data['top'][i]
        if last_top is None:
            last_top = top
        if abs(top - last_top) > 10:
            rows.append(current_line)
            current_line = []
            last_top = top
        current_line.append(word)
    if current_line:
        rows.append(current_line)
    return rows

def extract_text_from_pdf_pages(path):
    text_by_page = []
    with fitz.open(path) as doc:
        for page in doc:
            text = page.get_text()
            text_by_page.append(text)
    return text_by_page

def save_to_docx(text, filename):
    doc = Document()
    doc.add_paragraph(text)
    doc.save(filename)

def save_to_txt(text, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

def save_to_csv(rows, filename):
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def log_user_history(entry, path="history.json"):
    history = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    history.append(entry)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📄 Только текст", callback_data="text")],
        [InlineKeyboardButton("📁 Только файл", callback_data="file")],
        [InlineKeyboardButton("📄+📁 Текст и файл", callback_data="both")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери формат ответа перед отправкой файла:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
       "📌 Я умею распознавать текст и таблицы с фото и PDF.\n\n"
    "Ты можешь выбрать формат ответа:\n"
    "- 📄 Только текст\n"
    "- 📁 Только файл (.docx, .txt, .csv)\n"
    "- 📄+📁 Оба варианта\n\n"
    "Нажми /start, чтобы выбрать формат перед отправкой документа."
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = "history.json"
    if not os.path.exists(path):
        await update.message.reply_text("История пуста.")
        return
    with open(path, "r", encoding="utf-8") as f:
        try:
            history = json.load(f)
        except json.JSONDecodeError:
            await update.message.reply_text("Ошибка чтения истории.")
            return
    total = len(history)
    users = set(entry["user_id"] for entry in history)
    file_types = {}
    formats = {}
    errors = 0
    for entry in history:
        file_types[entry["file_type"]] = file_types.get(entry["file_type"], 0) + 1
        formats[entry["format"]] = formats.get(entry["format"], 0) + 1
        if "ошибка" in entry["status"]:
            errors += 1
    stats_text = (
    f"📊 Статистика использования:\n"
    f"Всего обращений: {total}\n"
    f"Уникальных пользователей: {len(users)}\n"
    f"Ошибок: {errors}\n\n"
    f"Типы файлов:\n" +
    "\n".join([f"• {k}: {v}" for k, v in file_types.items()]) +
    "\n\nФорматы ответов:\n" +
    "\n".join([f"• {k}: {v}" for k, v in formats.items()])
)

    await update.message.reply_text(stats_text)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_format_choice[query.from_user.id] = query.data
    await query.edit_message_text(text=f"✅ Формат установлен: {query.data}")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id
    username = message.from_user.username or f"ID:{user_id}"
    file_format = user_format_choice.get(user_id, "both")
    if message.document:
        file = await message.document.get_file()
        ext = file.file_path.split('.')[-1].lower()
    elif message.photo:
        file = await message.photo[-1].get_file()
        ext = "jpg"
    else:
        await message.reply_text("Отправь, пожалуйста, изображение или PDF.")
        return
    file_path = f"temp_{file.file_id}.{ext}"
    await file.download_to_drive(file_path)
    try:
        if ext == "pdf":
            pages = extract_text_from_pdf_pages(file_path)
            full_text = "\n\n".join([f"--- Страница {i+1} ---\n{t}" for i, t in enumerate(pages)])
            if file_format in ["text", "both"]:
                for i, page_text in enumerate(pages):
                    if page_text.strip():
                        await message.reply_text(f"📄 Страница {i+1}:\n\n{page_text[:4000]}")
            if file_format in ["file", "both"]:
                save_to_docx(full_text, file_path + ".docx")
                save_to_txt(full_text, file_path + ".txt")
                await message.reply_document(InputFile(file_path + ".docx"), filename="result.docx")
                await message.reply_document(InputFile(file_path + ".txt"), filename="result.txt")
                os.remove(file_path + ".docx")
                os.remove(file_path + ".txt")
        else:
            text = extract_text_from_image(file_path)
            table = extract_table_from_image(file_path)
            if not text.strip():
                await message.reply_text("❌ Не удалось распознать текст.")
                log_user_history({
                    "user_id": user_id,
                    "username": username,
                    "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "file_type": ext,
                    "format": file_format,
                    "status": "ошибка (пустой текст)"
                })
                return
            if page_text.strip():
                await message.reply_text(f"📄 Страница {i+1}:\n\n{page_text[:4000]}")

            if file_format in ["file", "both"]:
                save_to_docx(text, file_path + ".docx")
                save_to_txt(text, file_path + ".txt")
                save_to_csv(table, file_path + ".csv")
                await message.reply_document(InputFile(file_path + ".docx"), filename="result.docx")
                await message.reply_document(InputFile(file_path + ".txt"), filename="result.txt")
                await message.reply_document(InputFile(file_path + ".csv"), filename="table.csv")
                os.remove(file_path + ".docx")
                os.remove(file_path + ".txt")
                os.remove(file_path + ".csv")
        log.info(f"{username} — файл {ext} обработан — формат {file_format}")
        log_user_history({
            "user_id": user_id,
            "username": username,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "file_type": ext,
            "format": file_format,
            "status": "успешно"
        })
    except Exception as e:
        await message.reply_text("Произошла ошибка при обработке.")
        log.error(f"{username} — исключение: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def notify_admin(application):
    await application.bot.send_message(chat_id=ADMIN_CHAT_ID, text="🤖 Бот загружен и готов к работе!")

app = ApplicationBuilder().token(TOKEN).post_init(notify_admin).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
app.run_polling()
