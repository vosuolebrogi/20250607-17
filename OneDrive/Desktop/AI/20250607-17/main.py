import os
import asyncio
from typing import Optional
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv
from logger_config import setup_logger, log_user_interaction, log_api_call

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger = setup_logger("telegram_bot")

# Инициализация клиентов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN not found in environment variables")
    exit(1)

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    exit(1)

# Инициализация OpenAI клиента
openai_client = OpenAI(api_key=OPENAI_API_KEY)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Bot started by user {user.id} (@{user.username})")
    
    log_user_interaction(logger, user.id, user.username, "start command")
    
    # Создаем кнопку для отправки геолокации
    location_button = KeyboardButton("📍 Отправить геолокацию", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
    
    welcome_message = (
        f"Привет, {user.first_name}! 👋\n\n"
        "🌍 Я помогу вам узнать интересные факты о местах рядом с вами!\n\n"
        "📍 Нажмите кнопку ниже, чтобы отправить свою геолокацию, "
        "и я расскажу что-то необычное о ближайшем интересном месте."
    )
    
    await update.message.reply_text(welcome_message, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    user = update.effective_user
    log_user_interaction(logger, user.id, user.username, "help command")
    
    help_message = (
        "🆘 *Помощь*\n\n"
        "📍 Этот бот помогает узнать интересные факты о местах рядом с вами.\n\n"
        "*Как пользоваться:*\n"
        "1. Отправьте команду /start\n"
        "2. Нажмите кнопку 'Отправить геолокацию'\n"
        "3. Получите интересный факт о ближайшем месте!\n\n"
        "*Доступные команды:*\n"
        "/start - начать работу с ботом\n"
        "/help - показать эту справку"
    )
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def get_place_fact(latitude: float, longitude: float) -> Optional[str]:
    """
    Получение интересного факта о месте через OpenAI API
    
    Args:
        latitude: Широта
        longitude: Долгота
    
    Returns:
        Интересный факт о месте или None в случае ошибки
    """
    try:
        prompt = f"""
        Координаты: {latitude}, {longitude}

        Найди интересное и необычное место не далее, чем в 3 км от этих координат. 
        Расскажи один увлекательный исторический факт, легенду или любопытную особенность об этом месте.
        
        Требования к ответу:
        - Ответ должен быть на русском языке
        - Длина 2-4 предложения  
        - Начни с названия места
        - Сделай рассказ интересным и познавательным
        - Если точного места нет, расскажи о ближайшем городе или регионе
        
        Пример формата ответа:
        "🏛️ Московский Кремль: Знаете ли вы, что..."
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по истории и географии, который рассказывает интересные факты о местах."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        fact = response.choices[0].message.content.strip()
        log_api_call(logger, "OpenAI", True, f"Generated fact for coordinates {latitude}, {longitude}")
        return fact
        
    except Exception as e:
        logger.error(f"Error getting place fact: {str(e)}")
        log_api_call(logger, "OpenAI", False, f"Error: {str(e)}")
        return None

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик получения геолокации"""
    user = update.effective_user
    location = update.message.location
    
    latitude = location.latitude
    longitude = location.longitude
    
    log_user_interaction(logger, user.id, user.username, f"shared location: {latitude}, {longitude}")
    
    # Отправляем сообщение о том, что ищем информацию
    processing_message = await update.message.reply_text(
        "🔍 Ищу интересные места рядом с вами...", 
        reply_markup=None
    )
    
    try:
        # Получаем факт о месте
        fact = await get_place_fact(latitude, longitude)
        
        if fact:
            await processing_message.edit_text(f"✨ {fact}")
            
            # Создаем кнопку для новой геолокации
            location_button = KeyboardButton("📍 Отправить новую геолокацию", request_location=True)
            keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
            
            await update.message.reply_text(
                "Хотите узнать о другом месте? Отправьте новую геолокацию! 🗺️",
                reply_markup=keyboard
            )
        else:
            await processing_message.edit_text(
                "😔 Извините, не удалось получить информацию о местах рядом с вами. "
                "Попробуйте еще раз позже."
            )
            
    except Exception as e:
        logger.error(f"Error processing location: {str(e)}")
        await processing_message.edit_text(
            "😔 Произошла ошибка при обработке вашей геолокации. "
            "Попробуйте еще раз позже."
        )

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик неизвестных сообщений"""
    user = update.effective_user
    log_user_interaction(logger, user.id, user.username, "sent unknown message")
    
    # Создаем кнопку для отправки геолокации
    location_button = KeyboardButton("📍 Отправить геолокацию", request_location=True)
    keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "🤔 Я понимаю только геолокацию!\n\n"
        "📍 Нажмите кнопку ниже, чтобы отправить свою геолокацию, "
        "и я расскажу интересный факт о ближайшем месте.",
        reply_markup=keyboard
    )

def main() -> None:
    """Основная функция запуска бота"""
    logger.info("Starting Telegram bot...")
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Регистрируем обработчик геолокации
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
    # Регистрируем обработчик всех остальных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
    
    logger.info("Bot handlers registered successfully")
    
    # Запускаем бота
    logger.info("Bot is starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main() 