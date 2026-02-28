"""
Django settings for core_alp project.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY & DEBUG ---
SECRET_KEY = 'django-insecure-c&v)pd1zrisbvgi3hw$rij06ga6=nrjyj-cmd9g38efxxzle#b' 
DEBUG = False
ALLOWED_HOSTS = ['*']
SITE_ID = 1 # Wajib untuk django.contrib.sites

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', 

    # Third-party Apps
    'widget_tweaks',

    # Allauth (HANYA AKUN LOKAL)
    'allauth',
    'allauth.account',
    
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', 
    
    # Project App
    'alp_app',
    'profiles_app',
    'dashboard_app',
    'manager_app',
]

# --- MIDDLEWARE & URLS ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware', # Allauth Middleware
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core_alp.urls'

X_FRAME_OPTIONS = 'SAMEORIGIN'

# --- TEMPLATES ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'alp_app' / 'templates'], # PATH YANG SUDAH KOREK
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Wajib untuk allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core_alp.wsgi.application'

# --- DATABASE & PASSWORDS ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
AUTH_PASSWORD_VALIDATORS = [] 

# --- STATIC & MEDIA ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# --- ALLAUTH CONFIGURATION ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_FORMS = {
}

LOGIN_REDIRECT_URL = '/' 
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"           
ACCOUNT_PASSWORD_MIN_LENGTH = 1               
ACCOUNT_USERNAME_MIN_LENGTH = 1               

# --- EMAIL CONFIGURATION (PRODUCTION/REAL) ---
# Hapus atau komentar EMAIL_BACKEND console tadi
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ilyasamumtaza@gmail.com' 

# Ganti ini dengan 16 digit kode "App Password" dari Google Account kamu
EMAIL_HOST_PASSWORD = '' 

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- SOCIAL ACCOUNT CONFIG ---
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# Biar user nggak perlu milih akun lagi kalau cuma punya satu
SOCIALACCOUNT_LOGIN_ON_GET = True

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')