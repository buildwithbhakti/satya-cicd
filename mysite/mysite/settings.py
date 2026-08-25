from pathlib import Path
import os
import environ
from cryptography.fernet import Fernet
from csp.constants import NONCE, NONE, SELF 


env = environ.Env(DEBUG=(bool, False))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

FERNET = Fernet(os.environ['ENCRYPTION_KEY'].encode())
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'accounts',
    'teachers',
    'students',
    'speech',
    'tailwind',
    'theme',
    'evaluate',
    'django_recaptcha',
    'single_session',
    'django_q',
    'modeltranslation',
    'auditlog',
    'axes',
    'csp',
]

TAILWIND_APP_NAME = "theme"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'accounts.middleware.RestrictAdminByIPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'axes.middleware.AxesMiddleware',

]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'accounts.backends.EmailOrUsernameModelBackend',  # Replace with your app name
    'django.contrib.auth.backends.ModelBackend',  # Keep default as fallback
]

AXES_FAILURE_LIMIT     = 5              # failed attempts before lockout
AXES_COOLOFF_TIME      = 1             # lockout duration in hours
AXES_RESET_ON_SUCCESS  = True          # reset counter after successful login
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]
AXES_LOCKOUT_TEMPLATE = 'lockout.html'  # or use AXES_LOCKOUT_URL


ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Strict'  # or 'Lax'


# Django-Q2 config — using DB as broker (no Redis needed)
Q_CLUSTER = {
    'name': 'DjangoQ2',
    'workers': 2,
    'timeout': 60,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',  # uses your existing DB
}

WSGI_APPLICATION = 'mysite.wsgi.application'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'


DATABASES = {'default': env.db()}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'accounts.utils.password_validators.StrongPasswordValidator', 
    },
    {
        'NAME': 'accounts.utils.password_validators.PasswordHistoryValidator',
        'OPTIONS': {'history_limit': 5},  # Remember last 5 passwords
    },
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_SERVER')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = env('EMAIL_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = env('EMAIL_FROM')
# EMAIL_TIMEOUT = 10

# Session expires after X seconds of inactivity (e.g., 30 minutes)
# SESSION_COOKIE_AGE = 1800  # in seconds
# Reset the timer on every request (key for inactivity-based expiry)
# SESSION_SAVE_EVERY_REQUEST = True
# Optional: expire session when browser closes
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Strict'  # or 'Lax'

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

ADMIN_ALLOWED_IPS = os.getenv('ADMIN_ALLOWED_IPS', '127.0.0.1').split(',')

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGES = [
    ('en', 'English'),
    ('hi', 'हिन्दी'),
    ('mr', 'मराठी'),
]

LANGUAGE_CODE = 'en'

TIME_ZONE = 'Asia/Kolkata'
USE_TZ = False

USE_I18N = True
USE_L10N = True

TIME_FORMAT = "H:i A"
DATETIME_FORMAT = "j F Y, H:i A"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOG_FILES_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILES_URL = '/logs/'

MODEL_FILES_DIR = os.path.join(BASE_DIR, 'models')
MODEL_FILES_URL = '/models/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "accounts.CustomUser"

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')

RECAPTCHA_PUBLIC_KEY = env('RECAPTCHA_PUBLIC_KEY') 
RECAPTCHA_PRIVATE_KEY = env('RECAPTCHA_PRIVATE_KEY')
SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]
RECAPTCHA_DOMAIN = 'www.recaptcha.net'
os.environ['RECAPTCHA_TESTING'] = 'True'

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],

        "script-src": [
            SELF,
            NONCE,
            "https://cdnjs.cloudflare.com",
            "https://unpkg.com",
            "https://gistlangserver.in",
            "https://cdn.jsdelivr.net",
            "https://dhruva-api.bhashini.gov.in",
            "https://www.recaptcha.net/recaptcha/", 
            # "https://www.google.com/recaptcha/",
            # "https://www.gstatic.com/recaptcha/",
        ],

        "style-src": [
            SELF,
            "'unsafe-inline'",
            "https://cdnjs.cloudflare.com",
            "https://gistlangserver.in",
            "https://cdn.jsdelivr.net",
        ],

        "connect-src": [
            "'self'",
            "https://www.google.com",
            "https://inputtools.google.com",
            "https://gistlangserver.in",
            "https://dhruva-api.bhashini.gov.in",
        ],

        "font-src": [
            "'self'",
            "data:",
            "https://gistlangserver.in",
            "https://cdnjs.cloudflare.com",
        ],

        "img-src": [
            "'self'",
            "data:",
            "https://www.w3.org",
            "https://gistlangserver.in",
            "https://www.google.com",
            "https://www.gstatic.com", 
        ],

        "frame-src": [
            "'self'",
            "https://www.recaptcha.net/recaptcha/",
            # "https://www.google.com",
        ],

        "media-src": [
            "'self'",
            "blob:",
            "data:",
            "https://gistlangserver.in",
        ],

        "worker-src":       ["'self'", "blob:"],
        "manifest-src":     ["'self'"],
        "object-src":       ["'none'"],
        "base-uri":         ["'self'"],
        "form-action":      ["'self'"],
        "frame-ancestors":  ["'self'"],
    }
}

# Report-only mode for development
# CONTENT_SECURITY_POLICY_REPORT_ONLY = {
#     "DIRECTIVES": {
#         # same directives — violations logged but not blocked
#     }
# }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(request)s',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/app.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/security.log',
            'maxBytes': 1024 * 1024 * 20,
            'backupCount': 10,
            'formatter': 'json',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'DEBUG',
    },
}