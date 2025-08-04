import os
from datetime import datetime, timedelta
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

# ✅ Extensões e DB
from .extensions import db

# Blueprints
from app.atendimento.routes import atendimento_bp
from app.auth.routes import auth_bp
from app.imoveis.routes import imoveis_bp
from app.obras.routes import obras_bp
from app.atendimento import routes  # <-- Força o carregamento do módulo

migrate = Migrate()

# 🧩 Registra filtros Jinja customizados
def register_jinja_filters(app):
    @app.template_filter('getattr')
    def jinja_getattr(obj, attr_name):
        return getattr(obj, attr_name, "")

def create_app() -> Flask:
    app = Flask(__name__, static_folder='../static', template_folder='../templates')

    # Configurações
    app.secret_key = "Aninha_pitukinha"
    app.permanent_session_lifetime = timedelta(minutes=30)
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True

    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Extensões
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Jinja globals
    app.jinja_env.globals['now'] = datetime.now
    register_jinja_filters(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(imoveis_bp, url_prefix='/imoveis')
    app.register_blueprint(obras_bp)
    app.register_blueprint(atendimento_bp, url_prefix="/atendimento")



    # Banco
    with app.app_context():
        db.create_all()

    return app
