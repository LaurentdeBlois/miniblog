from flask import Flask, render_template, redirect, url_for, flash, request
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import markdown
from datetime import datetime
import os
from dotenv import load_dotenv
import bleach
from bleach.linkifier import LinkifyFilter
from urllib.parse import urlparse, urljoin
from functools import wraps

# Chargement des variables d'environnement
load_dotenv()

# Initialisation de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default-key-please-change')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limite de 10MB pour les requêtes

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configuration de Bleach pour le Markdown
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
    'p', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
}

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def safe_redirect(target):
    if not is_safe_url(target):
        target = url_for('home')
    return redirect(target)

# Modèle pour l'utilisateur admin
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modèle pour les articles
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tags = db.Column(db.String(200))

    def clean_tags(self):
        if self.tags:
            # Nettoyer et valider les tags
            tags = [bleach.clean(tag.strip()) for tag in self.tags.split(',')]
            tags = [tag for tag in tags if tag and len(tag) <= 50]  # Max 50 caractères par tag
            self.tags = ','.join(tags[:10])  # Maximum 10 tags

    def html_content(self):
        # Convertir le Markdown en HTML et nettoyer
        html = markdown.markdown(self.content)
        clean_html = bleach.clean(
            html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
        return clean_html

# Modèle pour la configuration du blog
class BlogConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default="Mon Blog")
    baseline = db.Column(db.String(500), nullable=True)

    @staticmethod
    def get_config():
        config = BlogConfig.query.first()
        if config is None:
            config = BlogConfig(title="Mon Blog")
            db.session.add(config)
            db.session.commit()
        return config

# Context processor pour rendre la config disponible partout
@app.context_processor
def inject_blog_config():
    return dict(blog_config=BlogConfig.get_config())

# Routes
@app.route('/')
def home():
    articles = Article.query.order_by(Article.created_date.desc()).all()
    return render_template('home.html', articles=articles)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('home'))
        flash('Nom d\'utilisateur ou mot de passe invalide')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/article/new', methods=['GET', 'POST'])
@login_required
def new_article():
    if request.method == 'POST':
        title = bleach.clean(request.form.get('title', '').strip())
        content = request.form.get('content', '').strip()
        tags = request.form.get('tags', '').strip()
        
        if not title or not content or len(title) > 200 or len(content) > 50000:
            flash('Le titre et le contenu sont requis. Le titre doit faire moins de 200 caractères et le contenu moins de 50000.')
            return redirect(url_for('new_article'))
        
        article = Article(title=title, content=content, tags=tags)
        article.clean_tags()
        
        db.session.add(article)
        db.session.commit()
        flash('Article créé avec succès!')
        return redirect(url_for('home'))
    
    return render_template('edit_article.html')

@app.route('/article/<int:id>')
def view_article(id):
    article = Article.query.get_or_404(id)
    return render_template('article.html', article=article)

@app.route('/article/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.get_or_404(id)
    
    if request.method == 'POST':
        article.title = bleach.clean(request.form.get('title', '').strip())
        article.content = request.form.get('content', '').strip()
        article.tags = request.form.get('tags', '').strip()
        
        if not article.title or not article.content or len(article.title) > 200 or len(article.content) > 50000:
            flash('Le titre et le contenu sont requis. Le titre doit faire moins de 200 caractères et le contenu moins de 50000.')
            return redirect(url_for('edit_article', id=id))
        
        article.clean_tags()
        db.session.commit()
        flash('Article modifié avec succès!')
        return redirect(url_for('view_article', id=id))
    
    return render_template('edit_article.html', article=article)

@app.route('/article/<int:id>/delete', methods=['POST'])
@login_required
def delete_article(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    flash('Article supprimé avec succès!')
    return redirect(url_for('home'))

@app.route('/config', methods=['GET', 'POST'])
@login_required
def edit_config():
    config = BlogConfig.get_config()
    if request.method == 'POST':
        # Nettoyage et validation des entrées
        title = bleach.clean(request.form.get('title', '').strip())[:200]
        baseline = bleach.clean(request.form.get('baseline', '').strip())[:500]
        
        if not title:
            flash('Le titre ne peut pas être vide.', 'error')
            return render_template('edit_config.html', config=config)
        
        config.title = title
        config.baseline = baseline
        db.session.commit()
        flash('Configuration mise à jour avec succès !', 'success')
        return redirect(url_for('home'))
    
    return render_template('edit_config.html', config=config)

# Création de la base de données et de l'utilisateur admin
def init_db():
    with app.app_context():
        db.create_all()
        # Créer un utilisateur admin si aucun n'existe
        if not User.query.first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123'))
            )
            db.session.add(admin)
            db.session.commit()
        
        # Créer la configuration par défaut si elle n'existe pas
        BlogConfig.get_config()

if __name__ == '__main__':
    init_db()
    app.run(debug=os.getenv('FLASK_ENV') == 'development')
