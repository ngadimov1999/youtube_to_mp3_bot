# YouTube to MP3 Telegram Bot

Телеграм бот для преобразования YouTube видео в MP3 файлы.

## Возможности

- 🎵 Преобразование YouTube видео в MP3
- ⚡ Быстрая обработка
- 📤 Прямая отправка файла в чат
- 🔒 Работает локально

## Требования

- Python 3.8+
- FFmpeg (для конвертации аудио)
- Telegram Bot Token

## Установка

### 1. Перейди в папку проекта
```bash
cd youtube_to_mp3_bot
```

### 2. Создай виртуальное окружение
```bash
python -m venv venv
```

### 3. Активируй виртуальное окружение

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Установи зависимости
```bash
pip install -r requirements.txt
```

### 5. Установи FFmpeg

**Windows (через Chocolatey):**
```bash
choco install ffmpeg
```

**macOS (через Homebrew):**
```bash
brew install ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install ffmpeg
```

### 6. Создай файл .env
Скопируй `.env.example` в `.env` и добавь свой Telegram Bot Token:
```bash
cp .env.example .env
```

Отредактируй `.env`:
```
TELEGRAM_BOT_TOKEN=your_actual_token_here
```

## Получение Telegram Bot Token

1. Открой [@BotFather](https://t.me/botfather) в Telegram
2. Отправь команду `/newbot`
3. Следуй инструкциям для создания бота
4. Скопируй полученный токен в файл `.env`

## Запуск

```bash
python -m youtube_to_mp3_bot.bot
```

## Использование

1. Найди бота в Telegram (по имени, которое ты задал)
2. Отправь команду `/start`
3. Отправь ссылку на YouTube видео
4. Дождись загрузки и получи MP3 файл!

## Структура проекта

```
youtube_to_mp3_bot/
├── __init__.py
├── bot.py                 # Основной файл бота
├── youtube_handler.py     # Логика загрузки и конвертации
├── requirements.txt       # Зависимости Python
├── .env.example          # Шаблон переменных окружения
├── .gitignore            # Gitignore файл
└── README.md             # Этот файл
```

## Примечания

- Максимальный размер файла для Telegram: 50 МБ
- Убедись, что FFmpeg установлен и доступен в PATH
- Для бесперебойной работы используй VPS/сервер

## Лицензия

MIT
