from __future__ import annotations

import logging
from logging.config import dictConfig

from app.settings import Settings, get_settings


def _resolve_log_level(level_name: str) -> int:
    resolved = logging.getLevelName(level_name.upper())
    if isinstance(resolved, int):
        return resolved
    return logging.INFO


def configure_logging(settings: Settings | None = None, *, force: bool = False) -> None:
    if getattr(configure_logging, "_configured", False) and not force:
        return

    if settings is None:
        settings = get_settings()

    level = _resolve_log_level(settings.LOG_LEVEL)

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {
                "handlers": ["default"],
                "level": level,
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": False,
                },
            },
        }
    )

    configure_logging._configured = True
