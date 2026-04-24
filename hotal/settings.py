"""
Django settings for hotal project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# ========================
# 🔐 SECURITY
# ========================
SECRET_KEY = 'django-insecure-7nbkwhsp0tcnimo8d9yxkkbea4u(k4o+chyefuj$cmj!3y66w&'
DEBUG = True

ALLOWED_HOSTS = ['*']   # Dev mode


# ========================
# 📦 INSTALLED APPS
# ========================
INSTALLED_APPS = [
    "unfold",                 
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Hotel App
    "h_app.apps.HAppConfig",
]



# ========================
# 🧱 MIDDLEWARE
# ========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'hotal.urls'


# ========================
# 🎨 TEMPLATES
# ========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # ✅ Custom
                "h_app.context_processors.wishlist_count",
                "h_app.context_processors.admin_counts",
            ],
        },
    },
]

WSGI_APPLICATION = 'hotal.wsgi.application'


# ========================
# 🗄 DATABASE
# ========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ========================
# 🌍 INTERNATIONALIZATION
# ========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# ========================
# 🖼 STATIC & MEDIA
# ========================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # For deployment

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ========================
# 🔐 AUTH
# ========================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ========================
# 📧 EMAIL | SMTP (GMAIL)
# ========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'vaycay.in@gmail.com'
EMAIL_HOST_PASSWORD = 'ssxe scnu cmpq ygbd'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# ========================
# 💳 RAZORPAY
# ========================
RAZORPAY_KEY_ID = "rzp_test_RzKxES0kyY1jWY"
RAZORPAY_KEY_SECRET = "8E6QmzLq0ZKzFdQDWsslHB1y"


# ========================
# 🌍 SITE URL
# ========================
SITE_URL = "http://127.0.0.1:8000"


UNFOLD = {
    "SITE_TITLE": "Hotel Management Admin",
    "SITE_HEADER": "Hotel Management",
    "THEME": "dark",
    "SHOW_COUNTS": True,
}

TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "h_app.context_processors.admin_dashboard_stats",
]
