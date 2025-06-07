import logging
import sys
from typing import Optional

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Настройка логгера с консольным выводом
    
    Args:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Настроенный логгер
    """
    # Создаем логгер
    logger = logging.getLogger(name)
    
    # Устанавливаем уровень логирования
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Проверяем, что обработчики еще не добавлены
    if not logger.handlers:
        # Создаем обработчик для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Создаем форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчик к логгеру
        logger.addHandler(console_handler)
    
    return logger

def log_user_interaction(logger: logging.Logger, user_id: int, username: Optional[str], action: str):
    """
    Логирование взаимодействия с пользователем
    
    Args:
        logger: Логгер
        user_id: ID пользователя
        username: Имя пользователя (может быть None)
        action: Действие пользователя
    """
    username_str = f"@{username}" if username else "Unknown"
    logger.info(f"User {user_id} ({username_str}) performed action: {action}")

def log_api_call(logger: logging.Logger, api_name: str, success: bool, details: str = ""):
    """
    Логирование API вызовов
    
    Args:
        logger: Логгер
        api_name: Имя API
        success: Успешность вызова
        details: Дополнительные детали
    """
    status = "SUCCESS" if success else "FAILED"
    message = f"API call to {api_name}: {status}"
    if details:
        message += f" - {details}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message) 