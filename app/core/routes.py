from flask import Blueprint, render_template
from flask_login import current_user

from app.dashboard.services import get_dashboard_data

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
def index():
    if current_user.is_authenticated:
        data = get_dashboard_data(current_user.id, current_user.daily_goal_minutes)
        return render_template("core/dashboard.html", data=data)
    return render_template("core/landing.html")