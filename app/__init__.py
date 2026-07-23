"""Application factory."""
import os
import logging
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

from config import config_by_name
from app.extensions import db, bcrypt, csrf, migrate, login_manager, limiter


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name[config_name])

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _configure_logging(app)

    return app


def _init_extensions(app):
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)


def _register_blueprints(app):
    from app.core.routes import core_bp
    app.register_blueprint(core_bp)

    # Registered as each module is built:
    # from app.auth.routes import auth_bp
    # app.register_blueprint(auth_bp, url_prefix="/auth")


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template("errors/429.html"), 429


def _configure_logging(app):
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

def _register_blueprints(app):
    from app.core.routes import core_bp
    from app.auth.routes import auth_bp
    from app.subjects.routes import subjects_bp
    from app.notes.routes import notes_bp
    from app.flashcards.routes import flashcards_bp
    from app.study.routes import study_bp
    from app.quizzes.routes import quizzes_bp
    from app.tutor.routes import tutor_bp
    from app.timetable.routes import timetable_bp
    from app.resources.routes import resources_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(subjects_bp, url_prefix="/subjects")
    app.register_blueprint(notes_bp, url_prefix="/notes")
    app.register_blueprint(flashcards_bp, url_prefix="/flashcards")
    app.register_blueprint(study_bp, url_prefix="/study")
    app.register_blueprint(quizzes_bp, url_prefix="/quizzes")
    app.register_blueprint(tutor_bp, url_prefix="/tutor")
    app.register_blueprint(timetable_bp, url_prefix="/timetable")
    app.register_blueprint(resources_bp, url_prefix="/resources")