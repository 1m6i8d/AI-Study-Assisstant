"""Quiz generation, attempts, results, and flagging routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import limiter
from app.quizzes.forms import QuizGenerateForm
from app.quizzes.ai_service import generate_quiz
from app.quizzes.services import (
    get_subject_notes_content, create_quiz, get_user_quizzes, get_quiz_or_404,
    start_attempt, submit_attempt, get_attempt_or_404, toggle_flag,
)
from app.notes.services import get_subject_choices
from app.subjects.services import get_subject_or_404

quizzes_bp = Blueprint("quizzes", __name__, template_folder="../templates/quizzes")


@quizzes_bp.route("/")
@login_required
def list_quizzes():
    subject_id = request.args.get("subject_id", type=int)
    quizzes = get_user_quizzes(current_user.id, subject_id=subject_id)
    subjects = get_subject_choices(current_user.id)
    return render_template("quizzes/list.html", quizzes=quizzes, subjects=subjects, selected_subject_id=subject_id)


@quizzes_bp.route("/new", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per hour")
def generate():
    preselected_subject_id = request.args.get("subject_id", type=int)
    form = QuizGenerateForm()
    form.subject_id.choices = get_subject_choices(current_user.id)

    if not form.subject_id.choices:
        flash("Create a subject with notes before generating a quiz.", "info")
        return redirect(url_for("subjects.create_subject"))

    if request.method == "GET" and preselected_subject_id:
        form.subject_id.data = preselected_subject_id

    if form.validate_on_submit():
        subject = get_subject_or_404(form.subject_id.data, current_user.id)
        content = get_subject_notes_content(subject.id)

        if not content.strip():
            flash(f'"{subject.name}" has no notes yet — add some before generating a quiz.', "info")
            return render_template("quizzes/form.html", form=form)

        try:
            questions_data = generate_quiz(content, form.question_types.data, form.question_count.data)
        except ValueError as exc:
            flash(f"Quiz generation failed: {exc}", "error")
            return render_template("quizzes/form.html", form=form)

        quiz = create_quiz(subject.id, f"{subject.name} Quiz", questions_data)
        flash("Quiz generated. Ready to take it.", "success")
        return redirect(url_for("quizzes.detail", quiz_id=quiz.id))

    return render_template("quizzes/form.html", form=form)


@quizzes_bp.route("/<int:quiz_id>")
@login_required
def detail(quiz_id):
    quiz = get_quiz_or_404(quiz_id, current_user.id)
    attempts = quiz.attempts.all()
    return render_template("quizzes/detail.html", quiz=quiz, attempts=attempts)


@quizzes_bp.route("/<int:quiz_id>/start", methods=["POST"])
@login_required
def start(quiz_id):
    get_quiz_or_404(quiz_id, current_user.id)  # ownership check
    attempt = start_attempt(quiz_id, current_user.id)
    return redirect(url_for("quizzes.take_attempt", attempt_id=attempt.id))


@quizzes_bp.route("/attempt/<int:attempt_id>")
@login_required
def take_attempt(attempt_id):
    attempt = get_attempt_or_404(attempt_id, current_user.id)
    if attempt.completed_at:
        return redirect(url_for("quizzes.results", attempt_id=attempt.id))
    return render_template("quizzes/take.html", attempt=attempt, quiz=attempt.quiz)


@quizzes_bp.route("/attempt/<int:attempt_id>/submit", methods=["POST"])
@login_required
def submit(attempt_id):
    get_attempt_or_404(attempt_id, current_user.id)
    answers = {
        key.replace("question_", ""): value
        for key, value in request.form.items()
        if key.startswith("question_")
    }
    submit_attempt(attempt_id, current_user.id, answers)
    flash("Quiz submitted.", "success")
    return redirect(url_for("quizzes.results", attempt_id=attempt_id))


@quizzes_bp.route("/attempt/<int:attempt_id>/results")
@login_required
def results(attempt_id):
    attempt = get_attempt_or_404(attempt_id, current_user.id)
    if not attempt.completed_at:
        return redirect(url_for("quizzes.take_attempt", attempt_id=attempt.id))
    return render_template("quizzes/results.html", attempt=attempt, quiz=attempt.quiz)


@quizzes_bp.route("/answer/<int:answer_id>/flag", methods=["POST"])
@login_required
def flag(answer_id):
    data = request.get_json(silent=True) or {}
    override = data.get("override")  # true, false, or null (flag without override)
    answer = toggle_flag(answer_id, current_user.id, override=override)
    return jsonify({"flagged": answer.flagged, "final_correctness": answer.final_correctness()})