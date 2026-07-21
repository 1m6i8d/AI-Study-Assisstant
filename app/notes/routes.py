"""Note CRUD routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.note import Note
from app.models.subject import Subject
from app.notes.forms import NoteForm
from app.notes.services import (
    get_user_notes, get_note_or_404, get_subject_choices, SORT_OPTIONS, DEFAULT_SORT
)
from app.subjects.services import get_subject_or_404

notes_bp = Blueprint("notes", __name__, template_folder="../templates/notes")


@notes_bp.route("/")
@login_required
def list_notes():
    search = request.args.get("search", "").strip()
    subject_id = request.args.get("subject_id", type=int)
    tag = request.args.get("tag", "").strip()
    sort = request.args.get("sort", DEFAULT_SORT)

    notes = get_user_notes(
        user_id=current_user.id,
        search=search or None,
        subject_id=subject_id,
        tag=tag or None,
        sort=sort,
    )
    subjects = get_subject_choices(current_user.id)

    return render_template(
        "notes/list.html",
        notes=notes,
        subjects=subjects,
        search=search,
        selected_subject_id=subject_id,
        selected_tag=tag,
        sort=sort,
        sort_options=SORT_OPTIONS,
    )


@notes_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_note():
    # Optional pre-selected subject when arriving from a subject's detail page
    preselected_subject_id = request.args.get("subject_id", type=int)

    form = NoteForm()
    form.subject_id.choices = get_subject_choices(current_user.id)

    if not form.subject_id.choices:
        flash("Create a subject before adding notes.", "info")
        return redirect(url_for("subjects.create_subject"))

    if request.method == "GET" and preselected_subject_id:
        form.subject_id.data = preselected_subject_id

    if form.validate_on_submit():
        # Defense in depth: confirm the selected subject actually belongs to this user
        get_subject_or_404(form.subject_id.data, current_user.id)

        note = Note(
            subject_id=form.subject_id.data,
            title=form.title.data.strip(),
            content=form.content.data.strip(),
            tags=form.tags.data.strip() if form.tags.data else None,
        )
        db.session.add(note)
        db.session.commit()
        flash(f'Note "{note.title}" created.', "success")
        return redirect(url_for("notes.view_note", note_id=note.id))

    return render_template("notes/form.html", form=form, mode="create")


@notes_bp.route("/<int:note_id>")
@login_required
def view_note(note_id):
    note = get_note_or_404(note_id, current_user.id)
    return render_template("notes/detail.html", note=note)


@notes_bp.route("/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def edit_note(note_id):
    note = get_note_or_404(note_id, current_user.id)
    form = NoteForm(obj=note)
    form.subject_id.choices = get_subject_choices(current_user.id)

    if request.method == "GET":
        form.subject_id.data = note.subject_id

    if form.validate_on_submit():
        get_subject_or_404(form.subject_id.data, current_user.id)

        note.subject_id = form.subject_id.data
        note.title = form.title.data.strip()
        note.content = form.content.data.strip()
        note.tags = form.tags.data.strip() if form.tags.data else None
        db.session.commit()
        flash(f'Note "{note.title}" updated.', "success")
        return redirect(url_for("notes.view_note", note_id=note.id))

    return render_template("notes/form.html", form=form, mode="edit", note=note)


@notes_bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    note = get_note_or_404(note_id, current_user.id)
    title = note.title
    db.session.delete(note)
    db.session.commit()
    flash(f'Note "{title}" deleted.', "info")
    return redirect(url_for("notes.list_notes"))