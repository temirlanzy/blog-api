"""Local development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True

# Set SQL_LOGGING = True to print every SQL query (useful for checking N+1).
SQL_LOGGING = False

if SQL_LOGGING:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "loggers": {
            "django.db.backends": {"handlers": ["console"], "level": "DEBUG"},
        },
    }
