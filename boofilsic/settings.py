import logging
import os
import sys

import environ
from django.utils.translation import gettext_lazy as _

from boofilsic import __version__

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    with open(os.path.join(BASE_DIR, "build_version")) as f:
        NEODB_VERSION = __version__ + "-" + f.read().strip()
except Exception:
    NEODB_VERSION = __version__ + "-unknown"

TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# Parse configuration from:
# - environment variables
# - neodb.env file in project root directory
# - /etc/neodb.env
environ.Env.read_env("/etc/neodb.env")
environ.Env.read_env(os.path.join(BASE_DIR, "neodb.env"))

# ====== List of user configuration variables ======
env = environ.FileAwareEnv(
    # WARNING: do not run with debug mode turned on in production
    NEODB_DEBUG=(bool, False),
    # WARNING: must use your own key and keep it secret
    NEODB_SECRET_KEY=(str),
    # Site information
    NEODB_SITE_NAME=(str),
    NEODB_SITE_DOMAIN=(str),
    NEODB_SITE_LOGO=(str, "/s/img/logo.svg"),
    NEODB_SITE_ICON=(str, "/s/img/icon.png"),
    NEODB_USER_ICON=(str, "/s/img/avatar.svg"),
    NEODB_SITE_INTRO=(str, ""),
    NEODB_SITE_HEAD=(str, ""),
    NEODB_SITE_DESCRIPTION=(
        str,
        "reviews about book, film, music, podcast and game.",
    ),
    # Links in site footer
    NEODB_SITE_LINKS=(dict, {}),
    # Alternative domains
    NEODB_ALTERNATIVE_DOMAINS=(list, []),
    # Preferred languages in catalog
    NEODB_PREFERRED_LANGUAGES=(list, ["en", "zh"]),  # , "ja", "ko", "de", "fr", "es"
    # Invite only mode
    # when True: user will not be able to register unless with invite token
    # (generated by `neodb-manage invite --create`)
    NEODB_INVITE_ONLY=(bool, False),
    NEODB_ENABLE_LOCAL_ONLY=(bool, False),
    NEODB_EXTRA_APPS=(list, []),
    # Mastodon/Pleroma instance allowed to login, keep empty to allow any instance to login
    NEODB_LOGIN_MASTODON_WHITELIST=(list, []),
    # DATABASE
    NEODB_DB_URL=(str, "postgres://user:pass@127.0.0.1:5432/neodb"),
    # Redis, for cache and job queue
    NEODB_REDIS_URL=(str, "redis://127.0.0.1:6379/0"),
    # Search backend, in one of these formats:
    # typesense://user:insecure@127.0.0.1:8108/catalog
    NEODB_SEARCH_URL=(str, ""),
    # EMAIL CONFIGURATION, in one of these formats:
    # "smtp://<username>:<password>@<host>:<port>"
    # "smtp+tls://<username>:<password>@<host>:<port>"
    # "smtp+ssl://<username>:<password>@<host>:<port>"
    # "anymail://<anymail_backend_name>?<anymail_args>"
    NEODB_EMAIL_URL=(str, ""),
    # EMAIL FROM
    NEODB_EMAIL_FROM=(str, "🧩 NeoDB <no-reply@neodb.social>"),
    # ADMIN_USERS
    NEODB_ADMIN_USERNAMES=(list, []),
    # List of available proxies for proxy downloader, in format of http://server1?url=__URL__,http://s2?url=__URL__,...
    NEODB_DOWNLOADER_PROXY_LIST=(list, []),
    # Timeout of downloader requests, in seconds
    NEODB_DOWNLOADER_REQUEST_TIMEOUT=(int, 90),
    # Timeout of downloader cache, in seconds
    NEODB_DOWNLOADER_CACHE_TIMEOUT=(int, 300),
    # Number of retries of downloader, when site is using RetryDownloader
    NEODB_DOWNLOADER_RETRIES=(int, 3),
    # Number of marks required for an item to be included in discover
    NEODB_MIN_MARKS_FOR_DISCOVER=(int, 1),
    # if True, only show title language with NEODB_PREFERRED_LANGUAGES
    NEODB_DISCOVER_FILTER_LANGUAGE=(bool, False),
    # if True, only show items marked by local users rather than entire network
    NEODB_DISCOVER_SHOW_LOCAL_ONLY=(bool, False),
    # if True, show popular public posts instead of recent ones.
    NEODB_DISCOVER_SHOW_POPULAR_POSTS=(bool, False),
    # update popular items every X minutes.
    NEODB_DISCOVER_UPDATE_INTERVAL=(int, 60),
    # Disable cron jobs, * for all
    NEODB_DISABLE_CRON_JOBS=(list, []),
    # federated search peers
    NEODB_SEARCH_PEERS=(list, []),
    # INTEGRATED TAKAHE CONFIGURATION
    TAKAHE_DB_URL=(str, "postgres://takahe:takahepass@127.0.0.1:5432/takahe"),
    # Spotify - https://developer.spotify.com/
    SPOTIFY_API_KEY=(str, "TESTONLY"),
    # The Movie Database (TMDB) - https://developer.themoviedb.org/
    TMDB_API_V3_KEY=(str, "TESTONLY"),
    # Google Books - https://developers.google.com/books/docs/v1/using - not used at the moment
    GOOGLE_API_KEY=(str, "TESTONLY"),
    # Discogs - personal access token from https://www.discogs.com/settings/developers
    DISCOGS_API_KEY=(str, "TESTONLY"),
    # IGDB - https://api-docs.igdb.com/
    IGDB_API_CLIENT_ID=(str, "TESTONLY"),
    IGDB_API_CLIENT_SECRET=(str, ""),
    # Discord webhooks
    DISCORD_WEBHOOKS=(dict, {"user-report": None}),
    # Slack API token, for sending exceptions to Slack, may deprecate in future
    SLACK_API_TOKEN=(str, ""),
    THREADS_APP_ID=(str, ""),
    THREADS_APP_SECRET=(str, ""),
    NEODB_ENABLE_LOGIN_BLUESKY=(bool, False),
    NEODB_ENABLE_LOGIN_THREADS=(bool, False),
    # SSL only, better be True for production security
    SSL_ONLY=(bool, False),
    NEODB_SENTRY_DSN=(str, ""),
    NEODB_SENTRY_SAMPLE_RATE=(float, 0),
    NEODB_FANOUT_LIMIT_DAYS=(int, 9),
)

# ====== End of user configuration variables ======

SECRET_KEY = env("NEODB_SECRET_KEY")
DEBUG = env("NEODB_DEBUG")
DATABASES = {
    "takahe": env.db_url("TAKAHE_DB_URL"),
    "default": env.db_url("NEODB_DB_URL"),
}
DATABASES["default"]["OPTIONS"] = {"client_encoding": "UTF8"}
DATABASES["default"]["TEST"] = {"DEPENDENCIES": ["takahe"]}
DATABASES["takahe"]["OPTIONS"] = {"client_encoding": "UTF8"}
DATABASES["takahe"]["TEST"] = {"DEPENDENCIES": []}
REDIS_URL = env("NEODB_REDIS_URL")
CACHES = {"default": env.cache_url("NEODB_REDIS_URL")}
_parsed_redis_url = env.url("NEODB_REDIS_URL")
RQ_QUEUES = {
    q: {
        "HOST": _parsed_redis_url.hostname,
        "PORT": _parsed_redis_url.port,
        "DB": _parsed_redis_url.path[1:],
        "DEFAULT_TIMEOUT": -1,
    }
    for q in ["mastodon", "export", "import", "fetch", "crawl", "ap", "cron"]
}

_parsed_search_url = env.url("NEODB_SEARCH_URL")
SEARCH_BACKEND = None
TYPESENSE_CONNECTION = {}
if _parsed_search_url.scheme == "typesense":
    SEARCH_BACKEND = "TYPESENSE"
    TYPESENSE_CONNECTION = {
        "api_key": _parsed_search_url.password,
        "nodes": [
            {
                "host": _parsed_search_url.hostname,
                "port": _parsed_search_url.port,
                "protocol": "http",
            }
        ],
        "connection_timeout_seconds": 2,
    }
    TYPESENSE_INDEX_NAME = _parsed_search_url.path[1:]
# elif _parsed_search_url.scheme == "meilisearch":
#     SEARCH_BACKEND = 'MEILISEARCH'
#     MEILISEARCH_SERVER = 'http://127.0.0.1:7700'
#     MEILISEARCH_KEY =  _parsed_search_url.password

DEFAULT_FROM_EMAIL = env("NEODB_EMAIL_FROM")
_parsed_email_url = env.url("NEODB_EMAIL_URL")
if _parsed_email_url.scheme == "anymail":
    # "anymail://<anymail_backend_name>?<anymail_args>"
    # see https://anymail.dev/
    from urllib import parse

    EMAIL_BACKEND = _parsed_email_url.hostname
    ANYMAIL = dict(parse.parse_qsl(_parsed_email_url.query))
    ENABLE_LOGIN_EMAIL = True
elif DEBUG and _parsed_email_url.scheme == "console":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    ENABLE_LOGIN_EMAIL = True
elif _parsed_email_url.scheme:
    _parsed_email_config = env.email("NEODB_EMAIL_URL")
    EMAIL_TIMEOUT = 5
    vars().update(_parsed_email_config)
    ENABLE_LOGIN_EMAIL = True
else:
    ENABLE_LOGIN_EMAIL = False


THREADS_APP_ID = env("THREADS_APP_ID")
THREADS_APP_SECRET = env("THREADS_APP_SECRET")

ENABLE_LOGIN_BLUESKY = env("NEODB_ENABLE_LOGIN_BLUESKY")
ENABLE_LOGIN_THREADS = env("NEODB_ENABLE_LOGIN_THREADS")

SITE_DOMAIN = env("NEODB_SITE_DOMAIN").lower()
SITE_INFO = {
    "neodb_version": NEODB_VERSION,
    "site_name": env("NEODB_SITE_NAME"),
    "site_domain": SITE_DOMAIN,
    "site_url": env("NEODB_SITE_URL", default="https://" + SITE_DOMAIN),
    "site_logo": env("NEODB_SITE_LOGO"),
    "site_icon": env("NEODB_SITE_ICON"),
    "user_icon": env("NEODB_USER_ICON"),
    "site_intro": env("NEODB_SITE_INTRO"),
    "site_description": env("NEODB_SITE_DESCRIPTION"),
    "site_head": env("NEODB_SITE_HEAD"),
    "site_links": [{"title": k, "url": v} for k, v in env("NEODB_SITE_LINKS").items()],
    "cdn_url": "https://cdn.jsdelivr.net" if DEBUG else "/jsdelivr",
    # "cdn_url": "https://cdn.jsdelivr.net",
    # "cdn_url": "https://fastly.jsdelivr.net",
}

SETUP_ADMIN_USERNAMES = env("NEODB_ADMIN_USERNAMES")

INVITE_ONLY = env("NEODB_INVITE_ONLY")

# By default, NeoDB will relay with relay.neodb.net so that public user ratings/etc can be shared across instances
# If you are running a development server, set this to True to disable this behavior
DISABLE_DEFAULT_RELAY = env("NEODB_DISABLE_DEFAULT_RELAY", default=DEBUG)

MIN_MARKS_FOR_DISCOVER = env("NEODB_MIN_MARKS_FOR_DISCOVER")

DISCOVER_UPDATE_INTERVAL = env("NEODB_DISCOVER_UPDATE_INTERVAL")
DISCOVER_FILTER_LANGUAGE = env("NEODB_DISCOVER_FILTER_LANGUAGE")
DISCOVER_SHOW_LOCAL_ONLY = env("NEODB_DISCOVER_SHOW_LOCAL_ONLY")
DISCOVER_SHOW_POPULAR_POSTS = env("NEODB_DISCOVER_SHOW_POPULAR_POSTS")

MASTODON_ALLOWED_SITES = env("NEODB_LOGIN_MASTODON_WHITELIST")

# Allow user to login via any Mastodon/Pleroma sites
MASTODON_ALLOW_ANY_SITE = len(MASTODON_ALLOWED_SITES) == 0

ALTERNATIVE_DOMAINS = [d.lower() for d in env("NEODB_ALTERNATIVE_DOMAINS", default=[])]  # type: ignore

SITE_DOMAINS = [SITE_DOMAIN] + ALTERNATIVE_DOMAINS

# ALLOWED_HOSTS = SITE_DOMAINS + ["127.0.0.1"]
ALLOWED_HOSTS = ["*"]

ENABLE_LOCAL_ONLY = env("NEODB_ENABLE_LOCAL_ONLY")

# Timeout of requests to Mastodon, in seconds
MASTODON_TIMEOUT = env("NEODB_LOGIN_MASTODON_TIMEOUT", default=5)  # type: ignore
THREADS_TIMEOUT = 30  # Threads is really slow when publishing post
TAKAHE_REMOTE_TIMEOUT = MASTODON_TIMEOUT

NEODB_USER_AGENT = f"NeoDB/{NEODB_VERSION} (+{SITE_INFO.get('site_url', 'undefined')})"
TAKAHE_USER_AGENT = NEODB_USER_AGENT

# Scope when creating Mastodon apps
# Alternatively, use "read write follow" to avoid re-authorize when migrating to a future version with more features
MASTODON_CLIENT_SCOPE = env(
    "NEODB_MASTODON_CLIENT_SCOPE",
    default="read:accounts read:follows read:search read:blocks read:mutes write:statuses write:media",  # type: ignore
)

# some Mastodon-compatible software like Pixelfed does not support granular scopes
MASTODON_LEGACY_CLIENT_SCOPE = "read write follow"

# Emoji code in mastodon
STAR_SOLID = ":star_solid:"
STAR_HALF = ":star_half:"
STAR_EMPTY = ":star_empty:"

DISCORD_WEBHOOKS = env("DISCORD_WEBHOOKS")
SPOTIFY_CREDENTIAL = env("SPOTIFY_API_KEY")
TMDB_API3_KEY = env("TMDB_API_V3_KEY")
# TMDB_API4_KEY = env('TMDB_API_V4_KEY')
# GOOGLE_API_KEY = env('GOOGLE_API_KEY')
DISCOGS_API_KEY = env("DISCOGS_API_KEY")
IGDB_CLIENT_ID = env("IGDB_API_CLIENT_ID")
IGDB_CLIENT_SECRET = env("IGDB_API_CLIENT_SECRET")
SLACK_TOKEN = env("SLACK_API_TOKEN")
SLACK_CHANNEL = "alert"

DOWNLOADER_PROXY_LIST = env("NEODB_DOWNLOADER_PROXY_LIST")
DOWNLOADER_BACKUP_PROXY = env("NEODB_DOWNLOADER_BACKUP_PROXY", default="")  # type: ignore
DOWNLOADER_REQUEST_TIMEOUT = env("NEODB_DOWNLOADER_REQUEST_TIMEOUT")
DOWNLOADER_CACHE_TIMEOUT = env("NEODB_DOWNLOADER_CACHE_TIMEOUT")
DOWNLOADER_RETRIES = env("NEODB_DOWNLOADER_RETRIES")

DISABLE_CRON_JOBS = env("NEODB_DISABLE_CRON_JOBS")
SEARCH_PEERS = env("NEODB_SEARCH_PEERS")

FANOUT_LIMIT_DAYS = env("NEODB_FANOUT_LIMIT_DAYS")
# ====== USER CONFIGUTRATION END ======

DATABASE_ROUTERS = ["takahe.db_routes.TakaheRouter"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# for legacy deployment:
# DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# To allow debug in template context
# https://docs.djangoproject.com/en/3.1/ref/settings/#internal-ips
INTERNAL_IPS = ["127.0.0.1"]

# Application definition

INSTALLED_APPS = [
    # "maintenance_mode",  # this has to be first if enabled
    "django.contrib.admin",
    "hijack",
    "hijack.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "django_rq",
    "django_bleach",
    "django_jsonform",
    "tz_detect",
    "sass_processor",
    "auditlog",
    "markdownx",
    "polymorphic",
    "easy_thumbnails",
    "user_messages",
    "corsheaders",
    "anymail",
    # "silk",
]

INSTALLED_APPS += [
    "mastodon.apps.MastodonConfig",
    "common.apps.CommonConfig",
    "users.apps.UsersConfig",
    "catalog.apps.CatalogConfig",
    "journal.apps.JournalConfig",
    "social.apps.SocialConfig",
    "takahe.apps.TakaheConfig",
    "legacy.apps.LegacyConfig",
]

for app in env("NEODB_EXTRA_APPS"):
    INSTALLED_APPS.append(app)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # "silk.middleware.SilkyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    # "django.middleware.locale.LocaleMiddleware",
    "users.middlewares.LanguageMiddleware",
    "tz_detect.middleware.TimezoneMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    # "maintenance_mode.middleware.MaintenanceModeMiddleware",  # this should be last if enabled
]

ROOT_URLCONF = "boofilsic.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                # 'django.contrib.messages.context_processors.messages',
                "user_messages.context_processors.messages",
                "boofilsic.context_processors.site_info",
            ],
        },
    },
]

WSGI_APPLICATION = "boofilsic.wsgi.application"

SESSION_COOKIE_NAME = "neodbsid"
SESSION_COOKIE_AGE = 90 * 24 * 60 * 60  # 90 days

AUTHENTICATION_BACKENDS = [
    "mastodon.auth.OAuth2Backend",
]

LOG_LEVEL = env("NEODB_LOG_LEVEL", default="DEBUG" if DEBUG else "INFO")  # type:ignore

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        },
    },
}

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

if SLACK_TOKEN:
    INSTALLED_APPS += [
        "django_slack",
    ]
    LOGGING["handlers"]["slack"] = {
        "level": "ERROR",
        "class": "django_slack.log.SlackExceptionHandler",
    }
    LOGGING["loggers"]["django"] = {"handlers": ["slack"], "level": "ERROR"}

MARKDOWNX_MARKDOWNIFY_FUNCTION = "journal.models.render_md"

SUPPORTED_UI_LANGUAGES = {
    "en": _("English"),
    "zh-hans": _("Simplified Chinese"),
    "zh-hant": _("Traditional Chinese"),
    "da": _("Danish"),
}

LANGUAGES = SUPPORTED_UI_LANGUAGES.items()


def _init_language_settings(preferred_lanugages_env):
    default_language = None
    preferred_lanugages = []
    for pl in preferred_lanugages_env:
        lang = pl.strip().lower()
        if not default_language:
            if lang in SUPPORTED_UI_LANGUAGES:
                default_language = lang
            elif lang == "zh":
                default_language = "zh-hans"
        if lang.startswith("zh-"):
            lang = "zh"
        if lang not in preferred_lanugages:
            preferred_lanugages.append(lang)
    return default_language or "en", preferred_lanugages or ["en"]


LANGUAGE_CODE, PREFERRED_LANGUAGES = _init_language_settings(
    env("NEODB_PREFERRED_LANGUAGES")
)

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

TIME_ZONE = env("NEODB_TIMEZONE", default="Asia/Shanghai")  # type: ignore

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SSL_ONLY = env("SSL_ONLY")
SECURE_SSL_REDIRECT = SSL_ONLY
SECURE_HSTS_PRELOAD = SSL_ONLY
SECURE_HSTS_INCLUDE_SUBDOMAINS = SSL_ONLY
SECURE_HSTS_SECONDS = 2592000 if SSL_ONLY else 0

STATIC_URL = "/s/"
STATIC_ROOT = env("NEODB_STATIC_ROOT", default=os.path.join(BASE_DIR, "static/"))  # type: ignore

if DEBUG:
    # django-sass-processor will generate neodb.css on-the-fly when DEBUG
    # NEODB_STATIC_ROOT is readonly in docker mode, so we give it a writable place
    SASS_PROCESSOR_ROOT = "/tmp"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
]

AUTH_USER_MODEL = "users.User"

SILENCED_SYSTEM_CHECKS = [
    "admin.E404",  # Required by django-user-messages
    "models.W035",  # Required by takahe: identical table name in different database
    "fields.W344",  # Required by takahe: identical table name in different database
]

TAKAHE_SESSION_COOKIE_NAME = "sessionid"

MEDIA_URL = "/m/"
MEDIA_ROOT = env("NEODB_MEDIA_ROOT", default=os.path.join(BASE_DIR, "media"))  # type: ignore

TAKAHE_MEDIA_URL = env("TAKAHE_MEDIA_URL", default="/media/")  # type: ignore
TAKAHE_MEDIA_ROOT = env("TAKAHE_MEDIA_ROOT", default="media")  # type: ignore

STORAGES = {  # TODO: support S3
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
    "takahe": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": TAKAHE_MEDIA_ROOT,
            "base_url": TAKAHE_MEDIA_URL,
        },
    },
}

DEFAULT_ITEM_COVER = "item/default.svg"
SITE_INFO["default_cover_url"] = MEDIA_URL + DEFAULT_ITEM_COVER

CSRF_TRUSTED_ORIGINS = [SITE_INFO["site_url"]]
if DEBUG:
    CSRF_TRUSTED_ORIGINS += ["http://127.0.0.1:8000", "http://localhost:8000"]

# Path to save report related images, ends with slash
REPORT_MEDIA_PATH_ROOT = "report/"
MARKDOWNX_MEDIA_PATH = "review/"
BOOK_MEDIA_PATH_ROOT = "book/"
DEFAULT_BOOK_IMAGE = os.path.join(BOOK_MEDIA_PATH_ROOT, "default.svg")
MOVIE_MEDIA_PATH_ROOT = "movie/"
DEFAULT_MOVIE_IMAGE = os.path.join(MOVIE_MEDIA_PATH_ROOT, "default.svg")
SONG_MEDIA_PATH_ROOT = "song/"
DEFAULT_SONG_IMAGE = os.path.join(SONG_MEDIA_PATH_ROOT, "default.svg")
ALBUM_MEDIA_PATH_ROOT = "album/"
DEFAULT_ALBUM_IMAGE = os.path.join(ALBUM_MEDIA_PATH_ROOT, "default.svg")
GAME_MEDIA_PATH_ROOT = "game/"
DEFAULT_GAME_IMAGE = os.path.join(GAME_MEDIA_PATH_ROOT, "default.svg")
COLLECTION_MEDIA_PATH_ROOT = "collection/"
DEFAULT_COLLECTION_IMAGE = os.path.join(COLLECTION_MEDIA_PATH_ROOT, "default.svg")
SYNC_FILE_PATH_ROOT = "sync/"
EXPORT_FILE_PATH_ROOT = "export/"

# Default redirect loaction when access login required view
LOGIN_URL = "/account/login"

ADMIN_ENABLED = DEBUG
ADMIN_URL = "neodb-admin"

BLEACH_STRIP_COMMENTS = True
BLEACH_STRIP_TAGS = True

# Thumbnail setting
# It is possible to optimize the image size even more: https://easy-thumbnails.readthedocs.io/en/latest/ref/optimize/
THUMBNAIL_ALIASES = {
    "": {
        "normal": {
            "size": (200, 200),
            "crop": "scale",
            "autocrop": True,
        },
    },
}
# THUMBNAIL_PRESERVE_EXTENSIONS = ('svg',)
THUMBNAIL_DEBUG = DEBUG

DJANGO_REDIS_IGNORE_EXCEPTIONS = not DEBUG

RQ_SHOW_ADMIN_LINK = DEBUG

SEARCH_INDEX_NEW_ONLY = False

DOWNLOADER_SAVEDIR = env("NEODB_DOWNLOADER_SAVE_DIR", default="/tmp")  # type: ignore

DISABLE_MODEL_SIGNAL = False  # disable index and social feeds during importing/etc

# MAINTENANCE_MODE = False
# MAINTENANCE_MODE_IGNORE_ADMIN_SITE = True
# MAINTENANCE_MODE_IGNORE_SUPERUSER = True
# MAINTENANCE_MODE_IGNORE_ANONYMOUS_USER = True
# MAINTENANCE_MODE_IGNORE_URLS = (r"^/users/connect/", r"^/users/OAuth2_login/")

# SILKY_AUTHENTICATION = True  # User must login
# SILKY_AUTHORISATION = True  # User must have permissions
# SILKY_PERMISSIONS = lambda user: user.is_superuser
# SILKY_MAX_RESPONSE_BODY_SIZE = 1024  # If response body>1024 bytes, ignore
# SILKY_INTERCEPT_PERCENT = 10

NINJA_PAGINATION_PER_PAGE = 20

# https://github.com/adamchainz/django-cors-headers#configuration
# CORS_ALLOWED_ORIGINS = []
# CORS_ALLOWED_ORIGIN_REGEXES = []
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r"^/(api|nodeinfo)/.*$"
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    # "PATCH",
    "POST",
    # "PUT",
)

DEACTIVATE_AFTER_UNREACHABLE_DAYS = 365

DEFAULT_RELAY_SERVER = "https://relay.neodb.net/inbox"

SENTRY_DSN = env("NEODB_SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.loguru import LoguruIntegration

    sentry_env = sys.argv[0].split("/")[-1]
    if len(sys.argv) > 1 and sentry_env in ("manage.py", "django-admin"):
        sentry_env = sys.argv[1]
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=sentry_env or "unknown",
        integrations=[
            DjangoIntegration(),
            LoguruIntegration(event_format="{name}:{function}:{line} - {message}"),
        ],
        release=NEODB_VERSION,
        send_default_pii=True,
        traces_sample_rate=env("NEODB_SENTRY_SAMPLE_RATE"),
    )
