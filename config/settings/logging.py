import os

from config.env import BASE_DIR

# Ensure logs directory exists
os.makedirs(f"{BASE_DIR}/logs", exist_ok=True)

# Rich logging setup
try:
    from rich.theme import Theme
    from rich.traceback import install as rich_traceback_install

    # Install rich traceback for pretty errors
    rich_traceback_install(show_locals=True, suppress=[])

    # Custom theme for log levels
    custom_theme = Theme({
        "logging.level.debug": "dim white",
        "logging.level.info": "bold blue",
        "logging.level.warning": "bold yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold red on white",
    })

    # Reconfigure rich theme
    import rich

    rich.reconfigure(theme=custom_theme)

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Formatters
FORMATTERS = {
    "verbose": {
        "format": "{levelname} {asctime} {threadName} {module} {filename}:{lineno} {name} {funcName} {message}",
        "style": "{",
    },
    "simple": {
        "format": "{levelname} {asctime} {module}:{lineno} {funcName} {message}",
        "style": "{",
    },
}

# Handlers
HANDLERS = {
    "console_handler": {
        "class": "rich.logging.RichHandler" if RICH_AVAILABLE else "logging.StreamHandler",
        "formatter": None if RICH_AVAILABLE else "simple",
        "rich_tracebacks": True,
        "show_time": True,
        "show_path": False,
        "markup": True,  # enables emojis and colors in messages
    },
    "file_handler": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": f"{BASE_DIR}/logs/django.log",
        "mode": "a",
        "formatter": "simple",
        "backupCount": 5,
        "maxBytes": 5 * 1024 * 1024,  # 5MB
        "encoding": "utf-8",
    },
    "detailed_file_handler": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": f"{BASE_DIR}/logs/django_detailed.log",
        "mode": "a",
        "formatter": "verbose",
        "backupCount": 5,
        "maxBytes": 5 * 1024 * 1024,  # 5MB
        "encoding": "utf-8",
    },
}

# Loggers
LOGGERS = {
    "django": {
        "handlers": ["console_handler", "detailed_file_handler"],
        "level": "INFO",
        "propagate": False,
    },
    "django.request": {
        "handlers": ["file_handler"],
        "level": "WARNING",
        "propagate": False,
    },
    "core": {
        "handlers": ["console_handler", "detailed_file_handler"],
        "level": "INFO",
        "propagate": False,
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": FORMATTERS,
    "handlers": HANDLERS,
    "loggers": LOGGERS,
}
