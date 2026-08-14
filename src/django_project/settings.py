from datetime import timedelta
import os
from pathlib import Path
from celery.schedules import crontab
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

MODE = os.getenv("MODE", 'DEVELOPMENT')

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    # Subdomínios de fexcompany.me
    "https://*.fexcompany.me",
    # Subdomínios de fabricadesoftware.ifc.edu.br
    "https://*.fabricadesoftware.ifc.edu.br",
    # Front-end local
    "http://localhost:8000",
    "http://localhost:5173",
    "http://localhost:3000",
]

API_URL = os.getenv("API_URL", "http://localhost:8000")
PAINEL_URL = os.getenv("PAINEL_URL", "http://localhost:3000")
BROKER_URL = os.getenv("BROKER_URL", "amqp://rafaelbochi:2012@localhost/fabricapainel")

# Security settings (uncomment and configure for production)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 3600
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_results",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",
    "django_extensions",
    "django_celery_beat",
    "simple_history",
    "core.populate.infra.populate_django_app",
    "core.user.infra.user_django_app",
    "core.uploader.infra.uploader_django_app",
    "core.work.infra.work_django_app",
    "core.assessment.infra.assessment_django_app",
    "core.edition.infra.edition_django_app",
    "core.field.infra.field_django_app",
    "core.cross_cutting_themes.infra.cross_cutting_themes_django_app",
    "debug_toolbar",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware"
]

ROOT_URLCONF = "django_project.urls"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
       "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    # Configurações de template para o browsable API
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.AdminRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ],
}


SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Fabrica Painel API",
    "DESCRIPTION": "API para gerenciamento do Fabrica Painel, incluindo endpoints e documentação.",
    "VERSION": "1.0.0"
}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "src/templates")
        ],  # Esse caminho já está correto
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

WSGI_APPLICATION = "django_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# DATABASES = {
#   'default': {DATABASES = {
#     'default': dj_database_url.config(
#         default=os.getenv('DATABASE_URL', 'postgres://user:password@localhost:5432/mydatabase')
#     )
# }
#   'ENGINE': "django.db.backends.postgresql",
#   'NAME': os.getenv("POSTGRES_NAME"),
#   'USER': os.getenv("POSTGRES_USER"),
#   'PASSWORD': os.getenv("POSTGRES_PASSWORD"),
#   'HOST': os.getenv("POSTGRES_HOST"),
#   'PORT': os.getenv("POSTGRES_PORT"),
# }
# }

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
    )
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True

# App Uploader settings

if MODE in ["PRODUCTION", "MIGRATE"]:
    MEDIA_ENDPOINT = "/media/"
else:
    MY_IP = os.getenv("MY_IP", "127.0.0.1")
    MEDIA_ENDPOINT = f"http://{MY_IP}:19003/media/"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
FILE_UPLOAD_PERMISSIONS = 0o640

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Whitenoise para servir arquivos estáticos em produção
if not DEBUG:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_METHODS = ("GET", "PATCH", "POST", "PUT", "DELETE")

AUTH_USER_MODEL = "user_django_app.User"

GRAPH_MODELS = {
    "all_applications": True,
    "group_models": True,
}

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "fabricadesoftware.araquari@ifc.edu.br")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

# Configurações de codificação para emails
DEFAULT_CHARSET = 'utf-8'
EMAIL_CHARSET = 'utf-8'

# Configurações básicas do Celery
CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_RESULT_BACKEND = "rpc://"
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

TOKEN_EXPIRATION_SECONDS = 1200

INTERNAL_IPS = ['*', 'localhost', '127.0.0.1', '172.17.0.1',]

# ------------------------------
# Password hashers customizados
# ------------------------------

if MODE == "DEVELOPMENT":
    # Hasher mais rápido apenas para dev
    from django.contrib.auth.hashers import PBKDF2PasswordHasher

    class FastPBKDF2PasswordHasher(PBKDF2PasswordHasher):
        iterations = 60000

    PASSWORD_HASHERS = [
        "src.django_project.settings.FastPBKDF2PasswordHasher",
    ]

elif MODE == "PRODUCTION":
    from django.contrib.auth.hashers import PBKDF2PasswordHasher

    class ProductionPBKDF2PasswordHasher(PBKDF2PasswordHasher):
        iterations = 200_000

    PASSWORD_HASHERS = [
        "src.django_project.settings.ProductionPBKDF2PasswordHasher",
    ]


CELERY_CONTROL_QUEUE_EXCLUSIVE = True
CELERY_TASK_TRACK_STARTED = True
