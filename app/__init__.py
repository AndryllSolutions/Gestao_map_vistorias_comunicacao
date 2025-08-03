import os
from datetime import datetime, timedelta

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Instâncias globais

db = SQLAlchemy()
migrate = Migrate()


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.jinja_env.globals['now'] = datetime.now
    app.secret_key = "Aninha_pitukinha"  # Em produção utilize algo seguro
    app.permanent_session_lifetime = timedelta(minutes=30)
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True

    CORS(app)

    # Configuração do banco de dados
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

    # Registrar Blueprints
    from .auth.routes import auth_bp
    from .imoveis.routes import imoveis_bp
    from .obras.routes import obras_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(imoveis_bp, url_prefix='/imoveis')
    app.register_blueprint(obras_bp)

    return app
