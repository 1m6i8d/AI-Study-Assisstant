"""Flashcard CRUD + review mode routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.flashcard import Flashcard, DIFFICULTY_LEVELS
from app.flashcards.forms import FlashcardForm
from app.flashcards.services import (
    get_user_flashcards, get_flashcard_or_404, get_review_queue, record_review
)
from app.notes.services import get_subject_choices
from app.subjects.services import get_subject_or_404

flashcards_bp = Blueprint("flashcards", __name__, template_folder="../templates/flashcards")


@flashcards_bp.route("/")
@login_required
def list_flashcards():
    subject_id = request.args.get("subject_id", type=int)
    difficulty = request.args.get("difficulty", "").strip() or None

    cards = get_user_flashcards(current_user.id, subject_id=subject_id, difficulty=difficulty)
    subjects = get_subject_choices(current_user.id)

    return render_template(
        "flashcards/list.html",
        cards=cards,
        subjects=subjects,
        selected_subject_id=subject_id,
        selected_difficulty=difficulty,
        difficulty_levels=DIFFICULTY_LEVELS,
    )


@flashcards_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_flashcard():
    preselected_subject_id = request.args.get("subject_id", type=int)

    form = FlashcardForm()
    form.subject_id.choices = get_subject_choices(current_user.id)

    if not form.subject_id.choices:
        flash("Create a subject before adding flashcards.", "info")
        return redirect(url_for("subjects.create_subject"))

    if request.method == "GET" and preselected_subject_id:
        form.subject_id.data = preselected_subject_id

    if form.validate_on_submit():
        get_subject_or_404(form.subject_id.data, current_user.id)

        card = Flashcard(
            subject_id=form.subject_id.data,
            front=form.front.data.strip(),
            back=form.back.data.strip(),
        )
        db.session.add(card)
        db.session.commit()
        flash("Flashcard created.", "success")
        return redirect(url_for("flashcards.list_flashcards"))

    return render_template("flashcards/form.html", form=form, mode="create")


@flashcards_bp.route("/<int:flashcard_id>/edit", methods=["GET", "POST"])
@login_required
def edit_flashcard(flashcard_id):
    card = get_flashcard_or_404(flashcard_id, current_user.id)
    form = FlashcardForm(obj=card)
    form.subject_id.choices = get_subject_choices(current_user.id)

    if request.method == "GET":
        form.subject_id.data = card.subject_id

    if form.validate_on_submit():
        get_subject_or_404(form.subject_id.data, current_user.id)

        card.subject_id = form.subject_id.data
        card.front = form.front.data.strip()
        card.back = form.back.data.strip()
        db.session.commit()
        flash("Flashcard updated.", "success")
        return redirect(url_for("flashcards.list_flashcards"))

    return render_template("flashcards/form.html", form=form, mode="edit", card=card)


@flashcards_bp.route("/<int:flashcard_id>/delete", methods=["POST"])
@login_required
def delete_flashcard(flashcard_id):
    card = get_flashcard_or_404(flashcard_id, current_user.id)
    db.session.delete(card)
    db.session.commit()
    flash("Flashcard deleted.", "info")
    return redirect(url_for("flashcards.list_flashcards"))


@flashcards_bp.route("/review/<int:subject_id>")
@login_required
def review(subject_id):
    import json
    subject = get_subject_or_404(subject_id, current_user.id)
    queue = get_review_queue(subject_id, current_user.id)

    if not queue:
        flash("This subject has no flashcards to review yet.", "info")
        return redirect(url_for("subjects.view_subject", subject_id=subject_id))

    cards_json = json.dumps([{"id": c.id, "front": c.front, "back": c.back} for c in queue])
    return render_template("flashcards/review.html", subject=subject, cards=queue, cards_json=cards_json)


@flashcards_bp.route("/<int:flashcard_id>/rate", methods=["POST"])
@login_required
def rate_flashcard(flashcard_id):
    """JSON endpoint called by review-mode JS after each card is rated."""
    difficulty = request.json.get("difficulty") if request.is_json else None
    card = record_review(flashcard_id, current_user.id, difficulty)

    if card is None:
        return jsonify({"error": "Invalid difficulty or card not found."}), 400

    return jsonify({
        "id": card.id,
        "difficulty": card.difficulty,
        "review_count": card.review_count,
    })