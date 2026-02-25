import logging
import sys
import json
from logging.config import dictConfig
from pathlib import Path
from typing import Any, Dict

# Создаем директорию для логов если не существует
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class CustomJsonFormatter(logging.Formatter):
    """Кастомный JSON formatter для структурированных логов"""

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись в JSON строку"""
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, 'extra') and record.extra:
            log_entry.update(record.extra)

        return json.dumps(log_entry, ensure_ascii=False)


def get_logging_config(env: str = "development") -> Dict[str, Any]:
    """Возвращает конфигурацию логирования в зависимости от среды"""

    # Общие хендлеры: всегда используется консоль
    common_handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default" if env == "development" else "json",
            "stream": sys.stdout,
        }
    }

    # Добавляем файловые хендлеры только в production
    if env == "production":
        common_handlers.update({
            "file_app": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(LOG_DIR / "app.log"),
                "mode": "a",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "json",
                "filename": str(LOG_DIR / "error.log"),
                "mode": "a",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "file_access": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(LOG_DIR / "access.log"),
                "mode": "a",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        })

    app_handlers = ["console"]
    uvicorn_handlers = ["console"]
    access_handlers = ["console"]
    error_handlers = ["console"]

    if env == "production":
        app_handlers += ["file_app", "file_error"]
        uvicorn_handlers += ["file_error"]
        access_handlers += ["file_access"]
        error_handlers += ["file_error"]

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)-8s] %(name)-20s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": CustomJsonFormatter,
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "access": {
                "format": '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)d',
                "datefmt": "%Y-%m-%d %H:%M:%S%z",
            },
        },
        "handlers": common_handlers,
        "loggers": {
            "app": {
                "handlers": app_handlers,
                "level": "DEBUG",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": uvicorn_handlers,
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": access_handlers,
                "level": "INFO",
                "propagate": False,
                "formatter": "access",
            },
            "uvicorn.error": {
                "handlers": error_handlers,
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": app_handlers,
                "level": "WARNING",
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "handlers": app_handlers,
                "level": "WARNING",
                "propagate": False,
            },
            "redis": {
                "handlers": app_handlers,
                "level": "WARNING",
                "propagate": False,
            },
            "fastapi": {
                "handlers": app_handlers,
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": error_handlers,
            "level": "WARNING",
        },
    }

    return config



def setup_logging(env: str = "development"):
    """Настройка логирования для приложения"""
    try:
        config = get_logging_config(env)
        dictConfig(config)

        logger = logging.getLogger("app")
        logger.info("Logging configured successfully for environment: %s", env)

    except Exception as e:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(LOG_DIR / "fallback.log")
            ]
        )
        fallback_logger = logging.getLogger("app")
        fallback_logger.error("Failed to configure logging: %s", e)


logger = logging.getLogger("app")