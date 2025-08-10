# app/__init__.py
import os
from datetime import datetime, timedelta
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_session import Session
from dotenv import load_dotenv

from .extensions import db

migrate = Migrate()

# --- Carrega .env da RAIZ do projeto (um nível acima de app/) ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)  # garante que carrega mesmo fora do cwd

# Filtros Jinja
def register_jinja_filters(app):
    @app.template_filter('getattr')
    def jinja_getattr(obj, attr_name):
        return getattr(obj, attr_name, None)

    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%Y-%m-%d'):
        if value:
            return value.strftime(format)
        return ''


def create_app() -> Flask:
    app = Flask(__name__, static_folder='../static', template_folder='../templates')

    # --- Config principais ---
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "Aninha_pitukinha")
    app.permanent_session_lifetime = timedelta(hours=6)
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True  # se estiver sem HTTPS local, pode desabilitar temporário

    # DB
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Sessão
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)

    # Bunny (espelha envs no config)
    app.config.from_mapping(
        BUNNY_STORAGE_URL=os.environ.get("BUNNY_STORAGE_URL"),
        BUNNY_STORAGE_KEY=os.environ.get("BUNNY_STORAGE_KEY"),
        BUNNY_PUBLIC_BASE=os.environ.get("BUNNY_PUBLIC_BASE"),
    )

    # Extensões
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Jinja
    app.jinja_env.globals['now'] = datetime.now
    register_jinja_filters(app)

    # --- IMPORTAR BLUEPRINTS AQUI, após config pronta ---
    from app.auth.routes import auth_bp
    from app.imoveis.routes import imoveis_bp
    from app.obras.routes import obras_bp
    from app.atendimento.routes import atendimento_bp
    from app.fotos.routes import fotos_bp

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(imoveis_bp, url_prefix='/imoveis')
    app.register_blueprint(obras_bp)
    app.register_blueprint(atendimento_bp, url_prefix="/atendimento")
    app.register_blueprint(fotos_bp)

    # Banco
    with app.app_context():
        db.create_all()

    return app
