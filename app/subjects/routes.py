"""Subject CRUD routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.subject import Subject
from app.subjects.forms import SubjectForm
from app.subjects.services import get_user_subjects, get_subject_or_404, SORT_OPTIONS, DEFAULT_SORT

subjects_bp = Blueprint("subjects", __name__, template_folder="../templates/subjects")


@subjects_bp.route("/")
@login_required
def list_subjects():
    search = request.args.get("search", "").strip()
    color = request.args.get("color", "").strip()
    sort = request.args.get("sort", DEFAULT_SORT)

    subjects = get_user_subjects(
        user_id=current_user.id,
        search=search or None,
        color=color or None,
        sort=sort,
    )

    return render_template(
        "subjects/list.html",
        subjects=subjects,
        search=search,
        selected_color=color,
        sort=sort,
        sort_options=SORT_OPTIONS,
    )


@subjects_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_subject():
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(
            user_id=current_user.id,
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            color=form.color.data,
        )
        db.session.add(subject)
        db.session.commit()
        flash(f'Subject "{subject.name}" created.', "success")
        return redirect(url_for("subjects.list_subjects"))

    return render_template("subjects/form.html", form=form, mode="create")


@subjects_bp.route("/<int:subject_id>")
@login_required
def view_subject(subject_id):
    subject = get_subject_or_404(subject_id, current_user.id)
    return render_template("subjects/detail.html", subject=subject)


@subjects_bp.route("/<int:subject_id>/edit", methods=["GET", "POST"])
@login_required
def edit_subject(subject_id):
    subject = get_subject_or_404(subject_id, current_user.id)
    form = SubjectForm(obj=subject)

    if form.validate_on_submit():
        subject.name = form.name.data.strip()
        subject.description = form.description.data.strip() if form.description.data else None
        subject.color = form.color.data
        db.session.commit()
        flash(f'Subject "{subject.name}" updated.', "success")
        return redirect(url_for("subjects.view_subject", subject_id=subject.id))

    return render_template("subjects/form.html", form=form, mode="edit", subject=subject)


@subjects_bp.route("/<int:subject_id>/delete", methods=["POST"])
@login_required
def delete_subject(subject_id):
    subject = get_subject_or_404(subject_id, current_user.id)
    name = subject.name
    db.session.delete(subject)
    db.session.commit()
    flash(f'Subject "{name}" deleted.', "info")
    return redirect(url_for("subjects.list_subjects"))