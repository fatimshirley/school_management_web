from pathlib import Path
import os
import dj_database_url

# ============================================================
# CHEMINS DU PROJET
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SÉCURITÉ
# ============================================================
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-local-development-key-change-me"
)
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

# ============================================================
# HÔTES AUTORISÉS
# ============================================================
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS = [
        RENDER_EXTERNAL_HOSTNAME,
    ]
else:
    ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1",
    ]

# ============================================================
# APPLICATIONS
# ============================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
    "apps.students",
    "apps.teachers",
    "apps.subjects",
    "apps.grades",
    "apps.absences",
    "apps.dashboard",
    "apps.academic",
]

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise pour servir les fichiers statiques en production
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ============================================================
# URLS
# ============================================================
ROOT_URLCONF = "config.urls"

# ============================================================
# TEMPLATES
# ============================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR.parent / "frontend" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ============================================================
# WSGI
# ============================================================
WSGI_APPLICATION = "config.wsgi.application"

# ============================================================
# BASE DE DONNÉES
# ============================================================
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ============================================================
# VALIDATION DES MOTS DE PASSE
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

# ============================================================
# INTERNATIONALISATION
# ============================================================
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True

# ============================================================
# FICHIERS STATIQUES
# ============================================================
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR.parent / "frontend" / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ============================================================
# WHITE NOISE
# ============================================================
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# ============================================================
# FICHIERS MEDIA
# ============================================================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.parent / "frontend" / "media"

# ============================================================
# EMAIL
# ============================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ============================================================
# LOGGING
# ============================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "school_format": {
            "format": "[{asctime}] [{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "school_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR.parent / "logs" / "school.log",
            "formatter": "school_format",
        },
    },
    "loggers": {
        "school": {
            "handlers": ["school_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ============================================================
# AUTHENTIFICATION
# ============================================================
LOGIN_URL = "connexion"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "connexion"

# ============================================================
# SÉCURITÉ HTTPS — PRODUCTION
# ============================================================
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# ============================================================
# CSRF — RENDER
# ============================================================
CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(
        f"https://{RENDER_EXTERNAL_HOSTNAME}"
    )