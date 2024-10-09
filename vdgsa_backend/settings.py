"""
Django settings for vdgsa_backend project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
from typing import List
from dotenv import load_dotenv
import os

import stripe  # type: ignore
from bleach.sanitizer import ALLOWED_ATTRIBUTES  # type: ignore
from django.urls.base import reverse_lazy

load_dotenv()

RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / 'stripe_key') as f:
    stripe.api_key = f.read().strip()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ftty4_3b^64x%nubicrpz9qf(xr%h2w+3h#!)@be5c(l)f_xlj'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Change the email backend in production
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS: List[str] = []

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = reverse_lazy('login')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_extensions',
    'vdgsa_backend.accounts',
    'vdgsa_backend.api_schema',
    'vdgsa_backend.emails',
    'vdgsa_backend.rental_viols',
    'vdgsa_backend.stripe_wix_proxy',
    'vdgsa_backend.stripe_email_webhook',
    'vdgsa_backend.conclave_registration',
    'corsheaders',
    'django_recaptcha',

    'markdownify.apps.MarkdownifyConfig',
]

CORS_ALLOWED_ORIGINS: List[str] = []

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vdgsa_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'vdgsa_tags': 'vdgsa_backend.templatetags.filters',
            }
        },
    },
]

WSGI_APPLICATION = 'vdgsa_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vdgsa_postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5432'
    }
}

DEFAULT_FROM_EMAIL = 'VdGSA Website <webmaster@vdgsa.org>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]
# In docker container, ends up being /usr/src/static
STATIC_ROOT = BASE_DIR.parent / 'static'

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": [
            'a',
            'abbr',
            'acronym',
            'b',
            'blockquote',
            'em',
            'i',
            'li',
            'ol',
            'p',
            'strong',
            'ul',
            'br',
        ],
        "WHITELIST_ATTRS": {
            **ALLOWED_ATTRIBUTES,
            'a': ALLOWED_ATTRIBUTES.get('a') + ['target']
        },
        "MARKDOWN_EXTENSIONS": [
            'markdown.extensions.attr_list',
        ]
    }
}



# Misc custom settings --------------------------------------------------------
MAX_NUM_FAMILY_MEMBERS = 3

MEDIA_ROOT = BASE_DIR.parent / 'uploads'
MEDIA_URL = '/uploads/'
