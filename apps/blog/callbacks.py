"""Callbacks used by the UNFOLD settings (environment, badge, tabs, dashboard)."""

import json
from typing import Any

from django.conf import settings
from django.db.models import Count
from django.http import HttpRequest

from .models import Category, Comment, Post, User

TOP_AUTHORS_LIMIT = 5
PERCENT = 100
PRODUCTION_ENV_ID = "production"


def environment_callback(request: HttpRequest) -> list[str]:
    """Badge in the header: Local (orange) or Production (red)."""
    if settings.BLOG_ENV_ID == PRODUCTION_ENV_ID:
        return ["Production", "danger"]
    return ["Local", "warning"]


def drafts_badge(request: HttpRequest) -> str:
    """Number of drafts shown next to the Posts menu item."""
    return str(Post.objects.filter(status=Post.Status.DRAFT).count())


def is_superuser(request: HttpRequest) -> bool:
    return bool(request.user.is_superuser)


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    """Add the data of the admin home page to the template context."""
    published = Post.objects.filter(status=Post.Status.PUBLISHED).count()
    drafts = Post.objects.filter(status=Post.Status.DRAFT).count()
    total_posts = published + drafts

    per_category = list(
        Category.objects.annotate(posts_count=Count("posts")).order_by("-posts_count", "name")
    )
    chart = {
        "labels": [category.name for category in per_category],
        "datasets": [
            {
                "label": "Posts",
                "data": [category.posts_count for category in per_category],
                "backgroundColor": "rgb(20, 184, 166)",
                "borderRadius": 4,
            }
        ],
    }

    top_authors = User.objects.annotate(posts_count=Count("posts")).order_by(
        "-posts_count", "email"
    )[:TOP_AUTHORS_LIMIT]
    table = {
        "headers": ["Author", "Email", "Posts"],
        "rows": [
            [user.get_full_name() or user.email, user.email, user.posts_count]
            for user in top_authors
        ],
    }

    context.update(
        {
            "cards": [
                {"title": "Users", "value": User.objects.count(), "icon": "group"},
                {"title": "Published posts", "value": published, "icon": "article"},
                {"title": "Drafts", "value": drafts, "icon": "edit_note"},
                {"title": "Comments", "value": Comment.objects.count(), "icon": "chat_bubble"},
            ],
            "posts_chart": json.dumps(chart),
            "top_authors_table": table,
            "published_percent": round(published / total_posts * PERCENT) if total_posts else 0,
            "drafts_percent": round(drafts / total_posts * PERCENT) if total_posts else 0,
        }
    )
    return context
