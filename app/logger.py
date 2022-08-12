import logging
from typing import Optional

logger: Optional[logging.Logger] = None


def init_logger():
    """Инициализирует логгер приложения."""
    global logger

    logger = logging.getLogger(__name__)


def get_logger() -> logging.Logger:
    """Возвращает экземпляр логгера приложения.

    Returns:
        logging.Logger - экземпляр логгера
    """
    if not logger:
        init_logger()

    return logger
