"""
Configuration Django - SAE 2.04 - Groupe RTGRP12.

Service de supervision des températures :
 - lecture des mesures collectées via MQTT et stockées dans MySQL ;
 - dashboard graphique, logs critiques, export Excel, import CSV.
"""
from pathlib import Path
import os

# Chargement du fichier .env s'il existe (python-dotenv)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    """Lit une variable d'environnement booléenne ('1', 'true', 'yes', 'on')."""
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# --- Sécurité ----------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-a-changer-en-production")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]
# Requis par Django pour les formulaires POST quand on accède via une IP/host distant.
CSRF_TRUSTED_ORIGINS = [
    f"http://{h}" for h in ALLOWED_HOSTS if h not in ("127.0.0.1", "localhost")
]


# --- Applications ------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "monitoring",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Sert les fichiers statiques (CSS de l'admin) sous gunicorn, sans Apache.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sae204.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "sae204.wsgi.application"


# --- Base de données ---------------------------------------------------------
# Par défaut : MySQL sur le serveur Windows (.131).
# Mettre DB_ENGINE=sqlite pour une démo locale rapide sans MySQL.
if os.getenv("DB_ENGINE", "mysql").lower() == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "sae204"),
            "USER": os.getenv("DB_USER", "collecte"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "10.252.12.131"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }


# --- Cache (résilience si la base est injoignable) ---------------------------
# Cache fichier : partagé entre les workers gunicorn et conservé après redémarrage.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / ".django_cache",
        "TIMEOUT": 3600,  # durée de conservation des dernières données (1 h)
    }
}


# --- Mots de passe -----------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalisation ----------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
# Les capteurs envoient des dates "naïves" (heure locale) : on désactive l'UTC
# pour éviter tout décalage horaire à l'affichage.
USE_TZ = False


# --- Fichiers statiques ------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise : compression des fichiers statiques (servis par gunicorn).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Paramètres métier (seuils de température critique en °C) -----------------
TEMP_CRITICAL_HIGH = float(os.getenv("TEMP_CRITICAL_HIGH", "30"))
TEMP_CRITICAL_LOW = float(os.getenv("TEMP_CRITICAL_LOW", "5"))


# --- Messages (classes CSS Bootstrap) ----------------------------------------
from django.contrib.messages import constants as messages  # noqa: E402

MESSAGE_TAGS = {
    messages.DEBUG: "secondary",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}
