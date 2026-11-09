# Blog API

Django 5.2 blog with a seed command and an admin panel built with [Django Unfold](https://unfoldadmin.com).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```

Admin: http://127.0.0.1:8000/admin/

## Seeding

`python manage.py seed` fills users, categories, tags, posts and comments with fake data (Faker).
All users get the same password: `SeedPass123!` (constant `SEED_PASSWORD`).

| Argument     | Default | Description                                              |
|--------------|---------|----------------------------------------------------------|
| `--users`    | 20      | Number of users to create                                |
| `--posts`    | 100     | Number of posts to create                                |
| `--comments` | 500     | Number of comments to create                             |
| `--clear`    | off     | Delete existing data first (superusers are kept)         |

```
$ python manage.py seed --users 50 --posts 300 --comments 1500
Users: 50 created
Categories: 8 created
Tags: 20 created
Posts: 300 created
Comments: 1500 created
Done in 0.58 seconds
```

Running it twice is safe: categories/tags that exist are skipped, emails and slugs stay unique.

## Admin

Features: custom sidebar with badge, environment badge, Cmd/Ctrl+K search, tabs on the post list,
dashboard (cards, bar chart, progress bars, top authors), filters, row/list/detail/submit-line actions,
WYSIWYG body editor, inline comments, unsaved-changes warning.

Screenshots (`docs/screenshots/`):

- Dashboard: `docs/screenshots/dashboard.png`
- Post list with filters open: `docs/screenshots/post-list.png`
- Post edit page: `docs/screenshots/post-edit.png`
- User list: `docs/screenshots/user-list.png`

To check for N+1 queries set `SQL_LOGGING = True` in `config/settings/local.py`.
