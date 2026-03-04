"""Main Telegram bot handler"""
import os
import json
import logging
import asyncio
import time
from collections import deque
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from .youtube_handler import download_youtube_as_mp3, is_valid_youtube_url

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global queue for processing
processing_queue = deque()
queue_lock = asyncio.Lock()
processing = False
AVERAGE_PROCESSING_TIME = 45  # Average time in seconds to process one video

# User tracking
USERS_FILE = 'users.json'
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Set your admin Telegram ID


def load_users() -> set:
    """Load user IDs from JSON file."""
    if Path(USERS_FILE).exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()


def save_users(users: set) -> None:
    """Save user IDs to JSON file."""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(list(users), f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {str(e)}")


def add_user(user_id: int) -> None:
    """Add user to tracking list."""
    users = load_users()
    users.add(user_id)
    save_users(users)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast message to all users (admin only)."""
    # Check if user is admin
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ты не администратор")
        return
    
    # Get message text
    if context.args:
        message_text = ' '.join(context.args)
    else:
        await update.message.reply_text(
            "Использование: /broadcast <сообщение>\n"
            "Пример: /broadcast Привет всем пользователям!"
        )
        return
    
    users = load_users()
    
    if not users:
        await update.message.reply_text("❌ Нет пользователей для отправки")
        return
    
    status_msg = await update.message.reply_text(
        f"📤 Отправляю сообщение {len(users)} пользователям...\n0/{len(users)} отправлено"
    )
    
    sent = 0
    failed = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML'
            )
            sent += 1
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {str(e)}")
            failed += 1
        
        # Update status every 10 messages
        if sent % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"📤 Отправляю сообщение {len(users)} пользователям...\n"
                    f"{sent}/{len(users)} отправлено"
                )
            except:
                pass
    
    await status_msg.edit_text(
        f"✅ Рассылка завершена\n"
        f"✓ Отправлено: {sent}\n"
        f"✗ Ошибок: {failed}"
    )


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics (admin only)."""
    # Check if user is admin
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ты не администратор")
        return
    
    users = load_users()
    await update.message.reply_text(
        f"👥 <b>Статистика пользователей</b>\n\n"
        f"Всего пользователей: {len(users)}",
        parse_mode='HTML'
    )

# Global queue for processing
processing_queue = deque()
queue_lock = asyncio.Lock()
processing = False
AVERAGE_PROCESSING_TIME = 45  # Average time in seconds to process one video

# User tracking
USERS_FILE = 'users.json'
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Set your admin Telegram ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    # Track user
    add_user(update.effective_user.id)
    
    welcome_message = (
        "🎵 <b>YouTube to MP3 Converter Bot</b>\n\n"
        "Отправь мне ссылку на YouTube видео, и я преобразую его в MP3 файл!\n\n"
        "Просто отправь URL видео (например: https://www.youtube.com/watch?v=...)"
    )
    await update.message.reply_text(welcome_message, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_message = (
        "📖 <b>Справка</b>\n\n"
        "1. Отправь ссылку на YouTube видео\n"
        "2. Бот загрузит видео и преобразует его в MP3\n"
        "3. Получи MP3 файл!\n\n"
        "Поддерживаемые ссылки:\n"
        "• https://www.youtube.com/watch?v=...\n"
        "• https://youtu.be/..."
    )
    await update.message.reply_text(help_message, parse_mode='HTML')


async def process_queue(application: Application) -> None:
    """Process videos from the queue."""
    global processing
    
    while True:
        async with queue_lock:
            if not processing_queue:
                processing = False
                await asyncio.sleep(1)
                continue
            
            processing = True
            user_id, url, status_message = processing_queue.popleft()
        
        try:
            # Update status that processing started
            if status_message:
                await status_message.edit_text("⏳ Обрабатываю видео...")
            
            # Download and convert
            mp3_path = download_youtube_as_mp3(url)
            
            # Check file size
            file_size = os.path.getsize(mp3_path)
            max_size = 50 * 1024 * 1024  # 50 MB limit for Telegram
            
            if file_size > max_size:
                await status_message.edit_text(
                    f"❌ Файл слишком большой ({file_size / 1024 / 1024:.1f} МБ). "
                    f"Максимум 50 МБ"
                )
                os.remove(mp3_path)
                await asyncio.sleep(1)
                continue
            
            # Send file
            await status_message.edit_text("📤 Отправляю файл...")
            
            # Get the video title from filename
            video_title = os.path.basename(mp3_path).replace('.mp3', '')
            
            with open(mp3_path, 'rb') as audio_file:
                await application.bot.send_audio(
                    chat_id=user_id,
                    audio=audio_file,
                    caption="✅ Готово!",
                    title=video_title
                )
            
            # Cleanup
            os.remove(mp3_path)
            await status_message.delete()
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            error_text = str(e)
            
            # Handle country restriction error
            if "not made this video available in your country" in error_text:
                error_message = (
                    "🌍 <b>Видео недоступно в вашей стране</b>\n\n"
                    "Автор видео ограничил доступ для вашего региона.\n\n"
                    "💡 Способы решения:\n"
                    "• Используйте VPN или прокси-сервер\n"
                    "• Свяжитесь с автором видео\n"
                    "• Выберите другое видео"
                )
            else:
                error_message = f"❌ Ошибка при обработке видео:\n{error_text[:200]}"
            
            try:
                if status_message:
                    await status_message.edit_text(error_message, parse_mode='HTML' if "🌍" in error_message else None)
            except:
                pass
        
        await asyncio.sleep(1)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages with YouTube links."""
    # Track user
    add_user(update.effective_user.id)
    
    url = update.message.text.strip()
    
    # Validate URL
    if not is_valid_youtube_url(url):
        await update.message.reply_text(
            "❌ Пожалуйста, отправь корректную ссылку на YouTube видео"
        )
        return
    
    # Add to queue
    status_message = await update.message.reply_text("📋 Добавляю в очередь...")
    
    async with queue_lock:
        processing_queue.append((update.effective_user.id, url, status_message))
        queue_position = len(processing_queue)
    
    # Calculate waiting time
    waiting_time = (queue_position - 1) * AVERAGE_PROCESSING_TIME
    minutes = waiting_time // 60
    seconds = waiting_time % 60
    
    # Send status message
    if queue_position == 1:
        status_text = "⏳ Твоё видео сейчас обрабатывается..."
    else:
        if minutes > 0:
            time_text = f"{minutes} мин {seconds} сек"
        else:
            time_text = f"{seconds} сек"
        status_text = f"📍 Ты #{queue_position} в очереди\n⏱️ Примерное время ожидания: {time_text}"
    
    await status_message.edit_text(status_text)


def main() -> None:
    """Start the bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env файле")
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add background queue processor
    async def start_queue(app):
        asyncio.create_task(process_queue(app))
    
    application.post_init = start_queue
    
    # Run the bot
    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
