SECRET_KEY = "SECRET"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "admin_edit_lock",
    "tests",
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}

ADMIN_EDIT_LOCK_DURATION = 60
ADMIN_EDIT_LOCK_MAX_DURATION = 10 * 60
