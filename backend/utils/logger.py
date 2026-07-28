from modules import (
    LOGGING_PATH,
    RotatingFileHandler,
    current_app,
    dictConfig,
    logging,
    os,
    sys,
)

__all__ = ["Logging", "configure_logging"]


def configure_logging():
    # 1. Configure the logging system BEFORE creating the app instance
    os.makedirs(LOGGING_PATH, exist_ok=True)

    log_file = os.path.join(LOGGING_PATH, "app.log")
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": log_file,
                    "maxBytes": 1048576,  # 1 MB
                    "backupCount": 5,
                    "formatter": "default",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "file"],
            },
        }
    )


class Logging(logging.LoggerAdapter):
    def __init__(self, name, level=logging.INFO):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Enable propagation so messages flow upwards to root handlers (like files)
        logger.propagate = True

        super().__init__(logger, {})
