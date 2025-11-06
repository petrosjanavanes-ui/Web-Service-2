import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import httpx
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "8390506713:AAGKlZcg0IrG99FoNM890tB0W0gNs2tKuvs"
CHANNEL_ID = "@reelsrazyob"  # Твой канал

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    instagram_url = update.message.text.strip()
    
    logger.info(f"Получена ссылка от {user.id}: {instagram_url}")
    
    # Проверяем, что это ссылка на Instagram
    if "instagram.com" not in instagram_url:
        await update.message.reply_text(
            "❌ Это не похоже на ссылку Instagram. Отправь мне ссылку на рилс из Instagram."
        )
        return
    
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("🔄 Начинаю обработку рилса...")
        
        # Скачиваем видео
        video_data = await download_instagram_reel(instagram_url)
        
        if video_data:
            # Отправляем видео в канал
            await processing_msg.edit_text("📤 Публикую рилс в канале...")
            
            # Публикуем в канал
            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=video_data,
                caption=f"🎬 Новый рилс!\n\nОт: @{user.username or 'пользователя'}" if user.username else "🎬 Новый рилс!",
                parse_mode=ParseMode.HTML
            )
            
            await processing_msg.edit_text("✅ Риелс успешно опубликован в канале!")
            logger.info(f"Риелс успешно опубликован в канал {CHANNEL_ID}")
        else:
            await processing_msg.edit_text("❌ Не удалось скачать видео. Проверь ссылку и попробуй снова.")
            
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

async def download_instagram_reel(reel_url):
    """
    Скачивает видео из Instagram используя сторонний API
    """
    try:
        # Используем mediadl.app API для получения информации о видео
        api_url = "https://api.mediadl.app/api/download"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Отправляем запрос к API
            response = await client.post(api_url, data={"url": reel_url})
            
            if response.status_code != 200:
                logger.error(f"API вернул статус {response.status_code}")
                return None
                
            data = response.json()
            logger.info(f"Ответ API: {data}")
            
            # Получаем URL видео (может быть несколько вариантов качества)
            video_url = None
            
            # Пробуем разные возможные пути к видео в ответе API
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
            video_response = await client.get(video_url, timeout=60.0)
            
            if video_response.status_code == 200:
                # Сохраняем видео в временный файл (в памяти)
                return video_response.content
            else:
                logger.error(f"Ошибка скачивания видео: {video_response.status_code}")
                return None
                
    except httpx.TimeoutException:
        logger.error("Таймаут при запросе к API")
        return None
    except Exception as e:
        logger.error(f"Ошибка при скачивании видео: {str(e)}")
        return None

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

async def main():
    """Основная функция для запуска бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запускается...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
