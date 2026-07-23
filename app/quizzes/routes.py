"""Quiz generation, taking, and results routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request

from flask_login import login_required, current_user

from app.extensions import limiter
from app.quizzes.forms import QuizGenerateForm
from app.quizzes.ai_service import generate_quiz
from app.quizzes.services import (
    get_subject_notes_content, create_quiz, get_user_quizzes, get_quiz_or_404, submit_quiz_answers
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
@limiter.limit("10 per hour")  # separate, tighter limit — this route costs real API quota
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
            questions_data = generate_quiz(
                content, form.question_types.data, form.question_count.data
            )
        except ValueError as exc:
            flash(f"Quiz generation failed: {exc}", "error")
            return render_template("quizzes/form.html", form=form)

        quiz = create_quiz(subject.id, f"{subject.name} Quiz", questions_data)
        flash("Quiz generated.", "success")
        return redirect(url_for("quizzes.take_quiz", quiz_id=quiz.id))

    return render_template("quizzes/form.html", form=form)


@quizzes_bp.route("/<int:quiz_id>")
@login_required
def take_quiz(quiz_id):
    quiz = get_quiz_or_404(quiz_id, current_user.id)
    if quiz.completed_at:
        return redirect(url_for("quizzes.results", quiz_id=quiz.id))
    return render_template("quizzes/take.html", quiz=quiz)


@quizzes_bp.route("/<int:quiz_id>/submit", methods=["POST"])
@login_required
def submit(quiz_id):
    quiz = get_quiz_or_404(quiz_id, current_user.id)
    answers = {
        key.replace("question_", ""): value
        for key, value in request.form.items()
        if key.startswith("question_")
    }
    submit_quiz_answers(quiz_id, current_user.id, answers)
    flash("Quiz submitted.", "success")
    return redirect(url_for("quizzes.results", quiz_id=quiz.id))


@quizzes_bp.route("/<int:quiz_id>/results")
@login_required
def results(quiz_id):
    quiz = get_quiz_or_404(quiz_id, current_user.id)
    if not quiz.completed_at:
        return redirect(url_for("quizzes.take_quiz", quiz_id=quiz.id))
    return render_template("quizzes/results.html", quiz=quiz)