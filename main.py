import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "8390506713:AAGKlZcg0IrG99FoNM890tB0W0gNs2tKuvs"
CHANNEL_ID = "@reelsrazyob"

def download_instagram_reel(reel_url):
    """Скачивает видео из Instagram используя сторонний API"""
    try:
        # Используем API для получения информации о видео
        api_url = "https://api.mediadl.app/api/download"
        
        # Отправляем запрос к API
        response = requests.post(api_url, data={"url": reel_url}, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"API вернул статус {response.status_code}")
            return None
            
        data = response.json()
        logger.info(f"Ответ API: {data}")
        
        # Получаем URL видео
        video_url = None
        
        if data.get("video"):
            video_url = data["video"]
        elif data.get("url"):
            video_url = data["url"]
        elif data.get("medias") and len(data["medias"]) > 0:
            video_url = data["medias"][0].get("url")
        
        if not video_url:
            logger.error("Не найден URL видео в ответе API")
            return None
        
        # Скачиваем видео
        video_response = requests.get(video_url, timeout=60)
        
        if video_response.status_code == 200:
            # Сохраняем видео во временный файл
            with open("temp_video.mp4", "wb") as f:
                f.write(video_response.content)
            return "temp_video.mp4"
        else:
            logger.error(f"Ошибка скачивания видео: {video_response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при скачивании видео: {str(e)}")
        return None

def handle_message(update: Update, context: CallbackContext):
    """Обработчик входящих сообщений"""
    user = update.effective_user
    instagram_url = update.message.text.strip()
    
    logger.info(f"Получена ссылка от {user.id}: {instagram_url}")
    
    # Проверяем, что это ссылка на Instagram
    if "instagram.com" not in instagram_url:
        update.message.reply_text(
            "❌ Это не похоже на ссылку Instagram. Отправь мне ссылку на рилс из Instagram."
        )
        return
    
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = update.message.reply_text("🔄 Начинаю обработку рилса...")
        
        # Скачиваем видео
        video_file = download_instagram_reel(instagram_url)
        
        if video_file:
            processing_msg.edit_text("📤 Публикую рилс в канале...")
            
            # Публикуем в канал
            with open(video_file, "rb") as video:
                context.bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=video,
                    caption=f"🎬 Новый рилс!\n\nОт: @{user.username}" if user.username else "🎬 Новый рилс!",
                    parse_mode=ParseMode.HTML
                )
            
            # Удаляем временный файл
            os.remove(video_file)
            
            processing_msg.edit_text("✅ Риелс успешно опубликован в канале!")
            logger.info(f"Риелс успешно опубликован в канал {CHANNEL_ID}")
        else:
            processing_msg.edit_text("❌ Не удалось скачать видео. Проверь ссылку и попробуй снова.")
            
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        error_msg = str(e)
        if "Forbidden" in error_msg:
            update.message.reply_text("❌ Бот не имеет прав для публикации в канале. Убедитесь, что бот добавлен как администратор канала.")
        else:
            update.message.reply_text(f"❌ Произошла ошибка: {error_msg}")

def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def main():
    """Основная функция для запуска бота"""
    # Создаем апдейтер
    updater = Updater(TOKEN, use_context=True)
    
    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
    
    # Добавляем обработчики
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запускается...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
