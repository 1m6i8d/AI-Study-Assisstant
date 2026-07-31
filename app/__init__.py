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
    _register_cli_commands(app)
    _register_before_request(app)
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
    from app.library.routes import library_bp
    from app.analytics.routes import analytics_bp
    from app.search.routes import search_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(subjects_bp, url_prefix="/subjects")
    app.register_blueprint(notes_bp, url_prefix="/notes")
    app.register_blueprint(flashcards_bp, url_prefix="/flashcards")
    app.register_blueprint(study_bp, url_prefix="/study")
    app.register_blueprint(quizzes_bp, url_prefix="/quizzes")
    app.register_blueprint(tutor_bp, url_prefix="/tutor")
    app.register_blueprint(timetable_bp, url_prefix="/timetable")
    app.register_blueprint(library_bp, url_prefix="/library")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(search_bp, url_prefix="/search")
    app.register_blueprint(admin_bp, url_prefix="/admin")


def _register_cli_commands(app):
    import click
    from app.extensions import db, bcrypt
    from app.models.user import User

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(email, username, password):
        """Create a new admin, or promote an existing account to admin by email."""
        existing = User.query.filter_by(email=email.lower().strip()).first()
        if existing:
            existing.role = "admin"
            existing.status = "approved"
            db.session.commit()
            click.echo(f"Promoted existing user '{existing.username}' to admin.")
            return

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        admin = User(
            username=username.strip(),
            email=email.lower().strip(),
            password_hash=hashed_pw,
            role="admin",
            status="approved",
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Created new admin account '{username}'.")

def _register_before_request(app):
    from flask import request, redirect, url_for
    from flask_login import current_user

    @app.before_request
    def restrict_admin_to_admin_area():
        if not current_user.is_authenticated or not current_user.is_admin():
            return
        if request.endpoint == "static":
            return
        if request.blueprint in ("admin", "auth"):
            return
        return redirect(url_for("admin.overview"))