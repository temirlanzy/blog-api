"""Fill the database with fake data: python manage.py seed."""

import random
import time
from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from apps.blog.models import Category, Comment, Post, Tag, User

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

SEED_PASSWORD = "SeedPass123!"

INACTIVE_USERS_RATIO = 0.15
STAFF_USERS_RATIO = 0.10
PUBLISHED_POSTS_RATIO = 0.70
POSTS_WITHOUT_CATEGORY_RATIO = 0.10

MIN_TAGS_PER_POST = 0
MAX_TAGS_PER_POST = 5
MIN_PARAGRAPHS = 3
MAX_PARAGRAPHS = 6
MIN_TITLE_WORDS = 3
MAX_TITLE_WORDS = 8
MIN_COMMENT_SENTENCES = 1
MAX_COMMENT_SENTENCES = 3
TITLE_MAX_LENGTH = 200
SLUG_MAX_LENGTH = 270
BULK_BATCH_SIZE = 500

CATEGORY_NAMES = [
    "Python",
    "Django",
    "DevOps",
    "Databases",
    "Frontend",
    "Testing",
    "Security",
    "Career",
]

TAG_NAMES = [
    "api",
    "rest",
    "orm",
    "docker",
    "postgresql",
    "redis",
    "celery",
    "git",
    "linux",
    "ci-cd",
    "performance",
    "tutorial",
    "best-practices",
    "async",
    "typing",
    "pytest",
    "deployment",
    "caching",
    "authentication",
    "tips",
]


class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--users", type=int, default=DEFAULT_USERS, help="Number of users to create"
        )
        parser.add_argument(
            "--posts", type=int, default=DEFAULT_POSTS, help="Number of posts to create"
        )
        parser.add_argument(
            "--comments", type=int, default=DEFAULT_COMMENTS, help="Number of comments to create"
        )
        parser.add_argument(
            "--clear", action="store_true", help="Delete existing data before seeding"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        self._validate(users_count, posts_count, comments_count, clear)

        started = time.monotonic()
        fake = Faker()

        with transaction.atomic():
            if clear:
                self._clear()

            users_created = self._create_users(fake, users_count)
            self._validate_dependencies(posts_count, comments_count)
            categories_created = self._create_named(Category, CATEGORY_NAMES)
            tags_created = self._create_named(Tag, TAG_NAMES)
            posts_created = self._create_posts(fake, posts_count)
            self._validate_published_posts(comments_count)
            comments_created = self._create_comments(fake, comments_count)

        elapsed = time.monotonic() - started
        self.stdout.write(f"Users: {users_created} created")
        self.stdout.write(f"Categories: {categories_created} created")
        self.stdout.write(f"Tags: {tags_created} created")
        self.stdout.write(f"Posts: {posts_created} created")
        self.stdout.write(f"Comments: {comments_created} created")
        self.stdout.write(self.style.SUCCESS(f"Done in {elapsed:.2f} seconds"))

    # ------------------------------------------------------------------ checks
    def _validate(self, users: int, posts: int, comments: int, clear: bool) -> None:
        for name, value in (("users", users), ("posts", posts), ("comments", comments)):
            if value < 0:
                raise CommandError(f"--{name} must not be negative (got {value}).")

    def _validate_dependencies(self, posts: int, comments: int) -> None:
        if (posts > 0 or comments > 0) and not User.objects.exists():
            raise CommandError(
                "Posts or comments requested, but there are no users. "
                "Use --users to create some."
            )

    def _validate_published_posts(self, comments: int) -> None:
        if comments > 0 and not Post.objects.filter(status=Post.Status.PUBLISHED).exists():
            raise CommandError(
                "Comments requested, but there are no published posts. "
                "Use --posts to create some."
            )

    # ------------------------------------------------------------------- clear
    def _clear(self) -> None:
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write("Existing data deleted (superusers kept).")

    # ------------------------------------------------------------------- users
    def _create_users(self, fake: Faker, count: int) -> int:
        if count == 0:
            return 0

        used_emails = set(User.objects.values_list("email", flat=True))
        password = make_password(SEED_PASSWORD)  # hash once, not per user
        users: list[User] = []

        for _ in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = self._unique_email(first_name, last_name, used_emails)
            users.append(
                User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    is_active=random.random() >= INACTIVE_USERS_RATIO,
                    is_staff=random.random() < STAFF_USERS_RATIO,
                )
            )

        User.objects.bulk_create(users, batch_size=BULK_BATCH_SIZE)
        return len(users)

    @staticmethod
    def _unique_email(first_name: str, last_name: str, used: set[str]) -> str:
        base = slugify(f"{first_name}.{last_name}").replace("-", ".") or "user"
        email = f"{base}@example.com"
        suffix = 1
        while email in used:
            suffix += 1
            email = f"{base}{suffix}@example.com"
        used.add(email)
        return email

    # --------------------------------------------------- categories and tags
    def _create_named(self, model: type[Category] | type[Tag], names: list[str]) -> int:
        existing = set(model.objects.values_list("slug", flat=True))
        new_objects = [
            model(name=name, slug=slugify(name))
            for name in names
            if slugify(name) not in existing
        ]
        model.objects.bulk_create(new_objects)
        return len(new_objects)

    # ------------------------------------------------------------------- posts
    def _create_posts(self, fake: Faker, count: int) -> int:
        if count == 0:
            return 0

        user_ids = list(User.objects.values_list("id", flat=True))
        category_ids = list(Category.objects.values_list("id", flat=True))
        tags = list(Tag.objects.all())
        used_slugs = set(Post.objects.values_list("slug", flat=True))

        posts: list[Post] = []
        for _ in range(count):
            title = fake.sentence(
                nb_words=random.randint(MIN_TITLE_WORDS, MAX_TITLE_WORDS)
            ).rstrip(".")[:TITLE_MAX_LENGTH]
            has_category = bool(category_ids) and random.random() >= POSTS_WITHOUT_CATEGORY_RATIO
            posts.append(
                Post(
                    title=title,
                    slug=self._unique_slug(title, used_slugs),
                    body="\n\n".join(
                        fake.paragraphs(nb=random.randint(MIN_PARAGRAPHS, MAX_PARAGRAPHS))
                    ),
                    author_id=random.choice(user_ids),
                    category_id=random.choice(category_ids) if has_category else None,
                    status=(
                        Post.Status.PUBLISHED
                        if random.random() < PUBLISHED_POSTS_RATIO
                        else Post.Status.DRAFT
                    ),
                )
            )

        created = Post.objects.bulk_create(posts, batch_size=BULK_BATCH_SIZE)
        for post in created:
            tags_number = random.randint(MIN_TAGS_PER_POST, min(MAX_TAGS_PER_POST, len(tags)))
            post.tags.set(random.sample(tags, tags_number))
        return len(created)

    @staticmethod
    def _unique_slug(title: str, used: set[str]) -> str:
        base = slugify(title)[:SLUG_MAX_LENGTH] or "post"
        slug = base
        suffix = 1
        while slug in used:
            suffix += 1
            slug = f"{base}-{suffix}"
        used.add(slug)
        return slug

    # ---------------------------------------------------------------- comments
    def _create_comments(self, fake: Faker, count: int) -> int:
        if count == 0:
            return 0

        user_ids = list(User.objects.values_list("id", flat=True))
        post_ids = list(
            Post.objects.filter(status=Post.Status.PUBLISHED).values_list("id", flat=True)
        )
        comments = [
            Comment(
                post_id=random.choice(post_ids),
                author_id=random.choice(user_ids),
                body=" ".join(
                    fake.sentences(nb=random.randint(MIN_COMMENT_SENTENCES, MAX_COMMENT_SENTENCES))
                ),
            )
            for _ in range(count)
        ]
        Comment.objects.bulk_create(comments, batch_size=BULK_BATCH_SIZE)
        return len(comments)
