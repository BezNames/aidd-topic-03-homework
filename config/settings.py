import logging
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

import os

_env = os.environ.get


def _bool_env(name, default=False):
    val = _env(name)
    if val is None:
        return default
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "yes", "y", "on")
    return bool(val)


SECRET_KEY = _env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    secret_file = BASE_DIR / ".secret_key"
    try:
        if secret_file.exists():
            SECRET_KEY = secret_file.read_text(encoding="utf-8").strip()
        else:
            from django.utils.crypto import get_random_string

            SECRET_KEY = get_random_string(length=64)
            secret_file.write_text(SECRET_KEY, encoding="utf-8")
    except OSError:
        SECRET_KEY = "django-insecure-dev-key-change-me-in-production"

DEBUG = _bool_env("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [
    host.strip()
    for host in (_env("DJANGO_ALLOWED_HOSTS") or "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap3",
    "dashboard",
    "user",
    "rest_framework",
    "django_filters",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap3"
CRISPY_TEMPLATE_PACK = "bootstrap3"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "main_format": {
            "format": "[{module} {asctime} {levelname}] {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "main_format",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "main_format",
            "filename": str(BASE_DIR / "app.logs"),
            "level": "INFO",
        },
    },
    "loggers": {
        "dashboard": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "user": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

logger = logging.getLogger("dashboard")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = _env("DJANGO_DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        import re

        match = re.match(
            r"postgresql://(?P<user>[^:@]+):(?P<password>[^@]+)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<name>[^?]+)",
            DATABASE_URL,
        )
        if not match:
            raise ImproperlyConfigured(
                "DJANGO_DATABASE_URL must be in the format "
                "postgresql://user:password@host:port/dbname"
            )
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": match["name"],
                "USER": match["user"],
                "PASSWORD": match["password"],
                "HOST": match["host"],
                "PORT": match["port"] or "5432",
            }
        }
    else:
        raise ImproperlyConfigured(
            "Unsupported DJANGO_DATABASE_URL scheme: starts with "
            f"{DATABASE_URL.split(':')[0]!r}"
        )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "user.User"

TINKOFF_TOKEN = _env("TINKOFF_TOKEN", "")

"""Celery Configuration Options"""
CELERY_TIMEZONE = "Europe/Moscow"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = _env("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")

"""Debug Celery"""
CELERY_TASK_ALWAYS_EAGER = _bool_env("CELERY_TASK_ALWAYS_EAGER", False)