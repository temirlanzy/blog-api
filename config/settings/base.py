"""Base settings for the Blog API project."""

import os
from pathlib import Path

from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = False
ALLOWED_HOSTS: list[str] = ["*"]

BLOG_ENV_ID = os.environ.get("BLOG_ENV_ID", "local")
GITHUB_REPO_URL = "https://github.com/your-login/blog-api"
UNFOLD_DOCS_URL = "https://unfoldadmin.com/docs/"

INSTALLED_APPS = [
    "unfold",  # must be above django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.blog",
]

AUTH_USER_MODEL = "blog.User"

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
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Tailwind "teal" palette (shades 50-950), RGB triplets
UNFOLD = {
    "SITE_TITLE": "Blog API",
    "SITE_HEADER": "Blog API",
    "SITE_SUBHEADER": "Content management",
    "SITE_SYMBOL": "edit_note",
    "SITE_URL": "/admin/",
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
    "COMMAND": {"search_models": True, "show_history": True},
    "SITE_DROPDOWN": [
        {"icon": "code", "title": _("GitHub repository"), "link": GITHUB_REPO_URL},
        {"icon": "menu_book", "title": _("Unfold docs"), "link": UNFOLD_DOCS_URL},
    ],
    "COLORS": {
        "primary": {
            "50": "240 253 250",
            "100": "204 251 241",
            "200": "153 246 228",
            "300": "94 234 212",
            "400": "45 212 191",
            "500": "20 184 166",
            "600": "13 148 136",
            "700": "15 118 110",
            "800": "17 94 89",
            "900": "19 78 74",
            "950": "4 47 46",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Overview"),
                "separator": True,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Content"),
                "separator": True,
                "items": [
                    {
                        "title": _("Posts"),
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_post_changelist"),
                        "badge": "apps.blog.callbacks.drafts_badge",
                    },
                    {
                        "title": _("Comments"),
                        "icon": "chat_bubble",
                        "link": reverse_lazy("admin:blog_comment_changelist"),
                    },
                    {
                        "title": _("Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                    },
                    {
                        "title": _("Tags"),
                        "icon": "sell",
                        "link": reverse_lazy("admin:blog_tag_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Access"),
                "separator": True,
                "permission": "apps.blog.callbacks.is_superuser",
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:blog_user_changelist"),
                        "permission": "apps.blog.callbacks.is_superuser",
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": "apps.blog.callbacks.is_superuser",
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {
                    "title": _("All"),
                    "link": lambda request: reverse("admin:blog_post_changelist"),
                },
                {
                    "title": _("Published"),
                    "link": lambda request: (
                        reverse("admin:blog_post_changelist") + "?status__exact=published"
                    ),
                },
                {
                    "title": _("Drafts"),
                    "link": lambda request: (
                        reverse("admin:blog_post_changelist") + "?status__exact=draft"
                    ),
                },
            ],
        },
    ],
}
