# 🤖 Telegram OCR Bot с аналитикой

Бот, который распознаёт текст и таблицы с изображений и PDF-документов, отправленных в Telegram.

## 🧠 Возможности

- 📸 Распознавание текста с изображений (jpg, png)
- 📄 Обработка PDF-файлов (в том числе многостраничных)
- 📊 Распознавание таблиц
- 🌍 Автоопределение языка текста
- 📂 Ответ в виде текста, файла .docx, .txt или обоих
- 📈 Встроенная статистика использования (`/stats`)
- ☁️ Поддержка облачного развёртывания через Render.com
- 🛡 Токены и Chat ID хранятся в переменных окружения

## 🚀 Развёртывание на Render.com

1. **Залей проект на GitHub**
2. **Создай новый Web Service** на [Render.com](https://render.com)
   - Runtime: `Python 3`
   - Build command:
     ```bash
     pip install -r requirements.txt
     ```
   - Start command:
     ```bash
     python bot.py
     ```
3. **Добавь переменные окружения:**
   - `BOT_TOKEN=твой_токен_из_BotFather`
   - `ADMIN_CHAT_ID=твой_Telegram_ID`

4. Нажми **Deploy** — и бот будет работать 24/7 🚀

## 🛠 Команды

- `/start` — выбор формата ответа
- `/help` — краткая инструкция
- `/stats` — статистика использования (доступна только администратору)

## 📂 Примеры входных данных

- Фото или скан с текстом
- PDF-документ
- Изображение с таблицей

## 📃 Лицензия

MIT — используй и дорабатывай свободно.

