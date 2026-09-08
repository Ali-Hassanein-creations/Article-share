# Article Share

A small Flask web app for sharing articles. Users can register, log in, publish articles, and comment on other people's articles. Authors and admins can delete articles/comments.

## Features

- User registration and login (Flask-Login, hashed passwords via Werkzeug)
- Publish articles (title + body)
- Comment on articles
- Delete your own articles/comments (or any, if you're an admin)
- SQLite database, auto-created on first run with a seeded admin account

## Tech stack

- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite

## Setup

```bash
pip install -r requirements.txt
python app.py
```

The app runs at `http://127.0.0.1:5000` by default.

On first run (no `article_sharing.db` present), the database is created and seeded with an admin account:

- **email:** admin@gmail.com
- **password:** admin9999

> Change or remove this admin account before deploying anywhere public.

## Project structure

```
app.py                  # Flask app, models, and routes
templates/               # Jinja2 templates
  base.html
  home.html
  login.html
  register.html
  new_article.html
static/style.css         # Styling
requirements.txt
```

## Routes

| Route | Method(s) | Description |
|---|---|---|
| `/` | GET | Home feed, newest articles first |
| `/register` | GET, POST | Create an account |
| `/login` | GET, POST | Log in |
| `/logout` | GET | Log out |
| `/new_article` | GET, POST | Publish a new article (login required) |
| `/comment/<article_id>` | POST | Add a comment (login required) |
| `/delete_article/<article_id>` | POST | Delete an article (author or admin only) |
| `/delete_comment/<comment_id>` | POST | Delete a comment (author or admin only) |
