# MiniBlog

Un blog minimaliste créé avec Flask, permettant la création et la gestion d'articles avec support Markdown.

## Fonctionnalités

- ✨ Interface minimaliste et élégante
- 🔒 Authentification administrateur
- 📝 Édition d'articles en Markdown
- 🏷️ Système de tags
- ⚙️ Configuration personnalisable (titre, baseline)
- 🛡️ Sécurité renforcée (protection XSS, validation des entrées)

## Installation

1. Cloner le dépôt :
```bash
git clone [URL_DU_DEPOT]
cd miniblog
```

2. Créer un environnement virtuel et l'activer :
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Créer le fichier .env :
```bash
FLASK_SECRET_KEY=votre-clé-secrète
ADMIN_PASSWORD=votre-mot-de-passe
FLASK_ENV=development
```

5. Lancer l'application :
```bash
python app.py
```

L'application sera accessible à l'adresse : http://localhost:5000

## Utilisation

1. Connectez-vous avec :
   - Utilisateur : admin
   - Mot de passe : (celui défini dans .env)

2. Vous pouvez alors :
   - Créer/modifier/supprimer des articles
   - Gérer les tags
   - Configurer le titre et la baseline du blog

## Sécurité

- Protection contre les injections XSS
- Validation des entrées utilisateur
- Nettoyage des données HTML
- Gestion sécurisée des mots de passe
- Protection des données sensibles

## Technologies utilisées

- Python 3.x
- Flask 3.0.0
- SQLite
- Flask-SQLAlchemy
- Flask-Login
- Markdown
- Bleach

## Licence

MIT
