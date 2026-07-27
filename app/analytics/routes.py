"""Analytics dashboard route."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.analytics.services import (
    get_study_hours_series, get_quiz_score_series, get_subject_distribution,
    get_flashcard_difficulty_breakdown, get_notes_created_series,
    get_planned_vs_actual, get_summary_stats,
)

analytics_bp = Blueprint("analytics", __name__, template_folder="../templates/analytics")


@analytics_bp.route("/")
@login_required
def index():
    data = {
        "study_hours": get_study_hours_series(current_user.id),
        "quiz_scores": get_quiz_score_series(current_user.id),
        "subject_distribution": get_subject_distribution(current_user.id),
        "flashcard_difficulty": get_flashcard_difficulty_breakdown(current_user.id),
        "notes_created": get_notes_created_series(current_user.id),
        "planned_vs_actual": get_planned_vs_actual(current_user.id),
    }
    summary = get_summary_stats(current_user.id)

    return render_template("analytics/index.html", data=data, summary=summary)