"""Resource recommendation routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import limiter
from app.resources.services import get_resources_for_subject
from app.subjects.services import get_subject_or_404

resources_bp = Blueprint("resources", __name__, template_folder="../templates/resources")


@resources_bp.route("/subject/<int:subject_id>")
@login_required
@limiter.limit("30 per hour")  # protects daily YouTube/Books quota from accidental hammering
def subject_resources(subject_id):
    subject = get_subject_or_404(subject_id, current_user.id)
    force_refresh = request.args.get("refresh") == "1"

    data = get_resources_for_subject(subject_id, current_user.id, force_refresh=force_refresh)

    if not data["keywords"] and not data["videos"] and not data["books"]:
        flash(f'"{subject.name}" has no notes yet — add some before finding resources.', "info")
        return redirect(url_for("subjects.view_subject", subject_id=subject_id))

    return render_template("resources/subject.html", subject=subject, data=data)