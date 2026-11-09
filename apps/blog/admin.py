"""Admin configuration based on Django Unfold."""

from typing import Any

from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, Prefetch, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.sections import TableSection
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    BooleanRadioFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import Category, Comment, Post, Tag, User

COMMENT_BODY_LENGTH = 60
COMMENTS_PER_PAGE = 10
SECTION_ROWS_LIMIT = 10
INITIALS_LENGTH = 2

admin.site.unregister(Group)


# --------------------------------------------------------------------- Group
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


# ----------------------------------------------------------- Category and Tag
class PostsTableSection(TableSection):
    verbose_name = "Posts"
    height = 300
    related_name = "posts"
    fields = ["title", "status", "created_at"]


class PostsCountMixin:
    """Adds a sortable `posts_count` column counted in the DB with one query."""

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).annotate(_posts_count=Count("posts"))  # type: ignore[misc]

    @display(description="Posts", ordering="_posts_count")
    def posts_count(self, obj: Category | Tag) -> int:
        return obj._posts_count  # type: ignore[union-attr]


@admin.register(Category)
class CategoryAdmin(PostsCountMixin, ModelAdmin):
    list_display = ["name", "slug", "posts_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    list_sections = [PostsTableSection]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        # the expandable row reads category.posts -> prefetch to avoid N+1
        return super().get_queryset(request).prefetch_related("posts")


@admin.register(Tag)
class TagAdmin(PostsCountMixin, ModelAdmin):
    list_display = ["name", "slug", "posts_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


# ------------------------------------------------------------------- Comment
@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ["post_title", "author", "short_body", "created_at"]
    list_select_related = ["post", "author"]
    list_filter = [
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ["body", "author__email", "post__title"]
    autocomplete_fields = ["post", "author"]

    @display(description="Post", ordering="post__title")
    def post_title(self, obj: Comment) -> str:
        return obj.post.title

    @display(description="Comment")
    def short_body(self, obj: Comment) -> str:
        if len(obj.body) <= COMMENT_BODY_LENGTH:
            return obj.body
        return f"{obj.body[:COMMENT_BODY_LENGTH]}…"


# ---------------------------------------------------------------------- User
class UserAdminCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")


class UserAdminChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ["display_header", "display_active", "display_staff", "posts_count"]
    list_filter = [
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    ]
    list_filter_submit = True
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    filter_horizontal = ["groups", "user_permissions"]
    actions = ["activate_users", "deactivate_users"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name"), "classes": ["tab"]}),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                "classes": ["tab"],
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined"), "classes": ["tab"]}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).annotate(_posts_count=Count("posts"))

    @display(description="User", header=True)
    def display_header(self, obj: User) -> list[Any]:
        full_name = obj.get_full_name() or obj.email
        initials = "".join(part[0] for part in full_name.split()[:INITIALS_LENGTH]).upper()
        return [full_name, obj.email, initials or "?"]

    @display(
        description="Active",
        label={True: "success", False: "danger"},
        ordering="is_active",
    )
    def display_active(self, obj: User) -> tuple[bool, str]:
        return obj.is_active, "Active" if obj.is_active else "Inactive"

    @display(
        description="Staff",
        label={True: "info", False: "warning"},
        ordering="is_staff",
    )
    def display_staff(self, obj: User) -> tuple[bool, str]:
        return obj.is_staff, "Staff" if obj.is_staff else "User"

    @display(description="Posts", ordering="_posts_count")
    def posts_count(self, obj: User) -> int:
        return obj._posts_count  # type: ignore[attr-defined]

    @action(description="Activate selected users", permissions=["change"])
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated: {updated}", messages.SUCCESS)

    @action(description="Deactivate selected users", permissions=["change"])
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated: {updated}", messages.SUCCESS)


# ---------------------------------------------------------------------- Post
class PostCommentsSection(TableSection):
    verbose_name = "Comments"
    height = 300
    related_name = "comments"
    fields = ["author", "body", "created_at"]


class CommentInline(TabularInline):
    model = Comment
    tab = True
    per_page = COMMENTS_PER_PAGE
    extra = 0
    autocomplete_fields = ["author"]
    fields = ["author", "body", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = [
        "display_header",
        "status_label",
        "category",
        "tags_dropdown",
        "comments_count",
        "created_at",
    ]
    list_select_related = ["author", "category"]
    list_filter = [
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ["title", "body", "author__email"]
    list_sections = [PostCommentsSection]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["author", "category", "tags"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [CommentInline]
    warn_unsaved_form = True
    formfield_overrides = {
        Post._meta.get_field("body").__class__: {"widget": WysiwygWidget},
    }

    actions = ["make_published", "make_drafts"]
    actions_row = ["toggle_status"]
    actions_list = ["publish_all_drafts"]
    actions_detail = ["open_comments"]
    actions_submit_line = ["save_and_publish"]

    fieldsets = (
        ("Content", {"fields": ("title", "slug", "body"), "classes": ["tab"]}),
        ("Classification", {"fields": ("category", "tags", "status"), "classes": ["tab"]}),
        ("Meta", {"fields": ("author", "created_at", "updated_at"), "classes": ["tab"]}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        return (
            super()
            .get_queryset(request)
            .annotate(_comments_count=Count("comments", distinct=True))
            .prefetch_related(
                "tags",
                Prefetch("comments", queryset=Comment.objects.select_related("author")),
            )
        )

    # ---- columns
    @display(description="Post", header=True, ordering="title")
    def display_header(self, obj: Post) -> list[str]:
        return [obj.title, obj.author.email]

    @display(
        description="Status",
        ordering="status",
        label={Post.Status.PUBLISHED: "success", Post.Status.DRAFT: "warning"},
    )
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict[str, Any]:
        tags = list(obj.tags.all())  # uses prefetch, no extra query
        return {
            "title": f"{len(tags)} tags",
            "items": [{"title": tag.name} for tag in tags],
        }

    @display(description="Comments", ordering="_comments_count")
    def comments_count(self, obj: Post) -> int:
        return obj._comments_count  # type: ignore[attr-defined]

    # ---- bulk actions
    @action(description="Publish selected", permissions=["change"])
    def make_published(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(request, f"Published: {updated}", messages.SUCCESS)

    @action(description="Move to drafts", permissions=["change"])
    def make_drafts(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f"Moved to drafts: {updated}", messages.SUCCESS)

    # ---- row action
    @action(description="Publish / unpublish", permissions=["change"])
    def toggle_status(self, request: HttpRequest, object_id: int) -> HttpResponse:
        post = Post.objects.get(pk=object_id)
        post.status = (
            Post.Status.DRAFT if post.status == Post.Status.PUBLISHED else Post.Status.PUBLISHED
        )
        post.save(update_fields=["status", "updated_at"])
        self.message_user(request, f"'{post.title}' is now {post.get_status_display()}")
        return redirect(reverse("admin:blog_post_changelist"))

    # ---- list action
    @action(description="Publish all drafts", permissions=["change"], icon="publish")
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponse:
        updated = Post.objects.filter(status=Post.Status.DRAFT).update(status=Post.Status.PUBLISHED)
        self.message_user(request, f"Published drafts: {updated}", messages.SUCCESS)
        return redirect(reverse("admin:blog_post_changelist"))

    # ---- detail action
    @action(description="Open comments", permissions=["view"], icon="chat_bubble")
    def open_comments(self, request: HttpRequest, object_id: int) -> HttpResponse:
        url = reverse("admin:blog_comment_changelist")
        return redirect(f"{url}?post__id__exact={object_id}")

    # ---- submit line action (runs after the object is saved)
    @action(description="Save & publish")
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status", "updated_at"])
        self.message_user(request, "Post saved and published", messages.SUCCESS)
