from datetime import datetime
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
#from datetime import datetime
#import pytz

# -------------------------
# App and db setup (the economy district lol)
# -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///article_sharing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'  


# -------------------------
# da Models housing market
# -------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user') 

    articles = db.relationship('Article', backref='author', cascade='all, delete-orphan', lazy=True)
    comments = db.relationship('Comment', backref='commenter', cascade='all, delete-orphan', lazy=True)

    def is_admin(self):
        return self.role == 'admin'


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    #calgary_tz = pytz.timezone('America/Edmonton')
    #imestamp = db.Column(db.DateTime, default=lambda: datetime.now(calgary_tz), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comments = db.relationship('Comment', backref='article', cascade='all, delete-orphan', lazy=True)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# -------------------------
# Login manager hook (basically the bouncer)
# -------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------
# First-run DB + hardcoded admin (this took me way too long to figure out, you gonna mess this up later too,relearn it)
# -------------------------
def init_db_with_admin():
    db.create_all()
    admin_email = "admin@gmail.com"
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        admin = User(
            username="admin",
            email=admin_email,
            password_hash=generate_password_hash("admin9999"),  # change before submitting
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        print(" Seeded admin user with email ")


# -------------------------
# Routes: pages (welcome to the neighborhood)
# -------------------------
@app.route('/')
def home():
    # new first
    articles = Article.query.order_by(Article.timestamp.desc()).all()
    return render_template('home.html', articles=articles)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        email = (request.form.get('email') or "").strip().lower()
        password = request.form.get('password') or ""

        # basic validation (the "good enough" kind)
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for('register'))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "error")
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        password = request.form.get('password') or ""
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for('home'))

@app.route('/new_article', methods=['GET', 'POST'])
@login_required
def new_article():
    if request.method == 'POST':
        title = (request.form.get('title') or "").strip()
        body = (request.form.get('body') or "").strip()

        if not title or not body:
            flash("Title and body are required.", "error")
            return redirect(url_for('new_article'))

        article = Article(title=title, body=body, author_id=current_user.id)
        db.session.add(article)
        db.session.commit()
        flash("Article published.", "success")
        return redirect(url_for('home'))
    return render_template('new_article.html')

@app.route('/comment/<int:article_id>', methods=['POST'])
@login_required
def comment(article_id):
    body = (request.form.get('body') or "").strip()
    if not body:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for('home'))

    article = Article.query.get_or_404(article_id)
    c = Comment(body=body, article_id=article.id, author_id=current_user.id)
    db.session.add(c)
    db.session.commit()
    flash("Comment added.", "success")
    return redirect(url_for('home'))

@app.route('/delete_article/<int:article_id>', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    if (article.author_id == current_user.id) or current_user.is_admin():
        db.session.delete(article)
        db.session.commit()
        flash("Article deleted.", "success")
        return redirect(url_for('home'))
    flash("Not authorized to delete this article.", "error")
    return redirect(url_for('home'))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if (comment.author_id == current_user.id) or current_user.is_admin():
        db.session.delete(comment)
        db.session.commit()
        flash("Comment deleted.", "success")
        return redirect(url_for('home'))
    flash("Not authorized to delete this comment.", "error")
    return redirect(url_for('home'))


# -------------------------
# Main (run )
# -------------------------
if __name__ == '__main__':
    if not os.path.exists('article_sharing.db'):
        with app.app_context():
            init_db_with_admin()
    else:
        with app.app_context():
            db.create_all()
    app.run(debug=True)
