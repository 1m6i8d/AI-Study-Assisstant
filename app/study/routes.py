"""Study timer, session tracking, and goals routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.study.forms import StudyGoalForm
from app.study.services import start_session, complete_session, cancel_session, get_study_stats
from app.notes.services import get_subject_choices
from app.subjects.services import get_subject_or_404

study_bp = Blueprint("study", __name__, template_folder="../templates/study")

DURATION_PRESETS = [25, 50]
MAX_CUSTOM_MINUTES = 240


@study_bp.route("/")
@login_required
def timer():
    subjects = get_subject_choices(current_user.id)
    stats = get_study_stats(current_user.id)
    return render_template(
        "study/timer.html",
        subjects=subjects,
        stats=stats,
        presets=DURATION_PRESETS,
        max_custom=MAX_CUSTOM_MINUTES,
        daily_goal=current_user.daily_goal_minutes,
        weekly_goal=current_user.weekly_goal_minutes,
    )


@study_bp.route("/sessions/start", methods=["POST"])
@login_required
def start():
    data = request.get_json(silent=True) or {}
    planned_minutes = data.get("planned_minutes")
    subject_id = data.get("subject_id")

    if not isinstance(planned_minutes, int) or not (1 <= planned_minutes <= MAX_CUSTOM_MINUTES):
        return jsonify({"error": "Invalid duration."}), 400

    if subject_id:
        get_subject_or_404(subject_id, current_user.id)  # 404s if not owned

    session = start_session(current_user.id, planned_minutes, subject_id)
    return jsonify({"session_id": session.id})


@study_bp.route("/sessions/<int:session_id>/complete", methods=["POST"])
@login_required
def complete(session_id):
    session = complete_session(session_id, current_user.id)
    if session is None:
        return jsonify({"error": "Session not found or already completed."}), 404

    stats = get_study_stats(current_user.id)
    return jsonify({"completed": True, "stats": stats})


@study_bp.route("/sessions/<int:session_id>/cancel", methods=["POST"])
@login_required
def cancel(session_id):
    cancelled = cancel_session(session_id, current_user.id)
    return jsonify({"cancelled": cancelled})


@study_bp.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    form = StudyGoalForm(obj=current_user)
    if form.validate_on_submit():
        current_user.daily_goal_minutes = form.daily_goal_minutes.data
        current_user.weekly_goal_minutes = form.weekly_goal_minutes.data
        db.session.commit()
        flash("Study goals updated.", "success")
        return redirect(url_for("study.timer"))

    return render_template("study/goals.html", form=form)