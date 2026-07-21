from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.incidents import incidents_bp
    from app.routes.iocs import iocs_bp
    from app.routes.vulns import vulns_bp
    from app.routes.playbooks import playbooks_bp
    from app.routes.webhooks import webhooks_bp
    from app.routes.frontend import frontend_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(incidents_bp, url_prefix="/api/incidents")
    app.register_blueprint(iocs_bp, url_prefix="/api/iocs")
    app.register_blueprint(vulns_bp, url_prefix="/api/vulnerabilities")
    app.register_blueprint(playbooks_bp, url_prefix="/api/playbooks")
    app.register_blueprint(webhooks_bp, url_prefix="/api/webhooks")
    app.register_blueprint(frontend_bp)

    with app.app_context():
        db.create_all()
        from app.services.seed import seed_database

        seed_database()

    return app
