"""Timetable routes: weekly grid view, CRUD."""
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.timetable_entry import TimetableEntry
from app.timetable.services import build_week_grid, get_week_start, get_entry_or_404, GRID_START_HOUR, GRID_END_HOUR
from app.timetable.forms import TimetableEntryForm
from app.notes.services import get_subject_choices

timetable_bp = Blueprint("timetable", __name__, template_folder="../templates/timetable")


@timetable_bp.route("/")
@login_required
def grid():
    week_param = request.args.get("week")
    if week_param:
        try:
            reference = datetime.strptime(week_param, "%Y-%m-%d").date()
        except ValueError:
            reference = date.today()
    else:
        reference = date.today()

    week_start = get_week_start(reference)
    days = build_week_grid(current_user.id, week_start)
    hours = list(range(GRID_START_HOUR, GRID_END_HOUR + 1))

    return render_template(
        "timetable/grid.html",
        days=days,
        hours=hours,
        week_start=week_start,
        prev_week=(week_start - timedelta(days=7)).isoformat(),
        next_week=(week_start + timedelta(days=7)).isoformat(),
        today=date.today(),
    )


@timetable_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_entry():
    form = TimetableEntryForm()
    subject_choices = [(0, "No subject")] + get_subject_choices(current_user.id)
    form.subject_id.choices = subject_choices

    if form.validate_on_submit():
        entry = TimetableEntry(
            user_id=current_user.id,
            title=form.title.data.strip(),
            subject_id=form.subject_id.data if form.subject_id.data != 0 else None,
            entry_type=form.entry_type.data,
            day_of_week=int(form.day_of_week.data) if form.entry_type.data == "recurring" else None,
            specific_date=form.specific_date.data if form.entry_type.data == "one_off" else None,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Timetable entry added.", "success")
        return redirect(url_for("timetable.grid"))

    return render_template("timetable/form.html", form=form, mode="create")


@timetable_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = get_entry_or_404(entry_id, current_user.id)
    form = TimetableEntryForm(obj=entry)
    subject_choices = [(0, "No subject")] + get_subject_choices(current_user.id)
    form.subject_id.choices = subject_choices

    if request.method == "GET":
        form.subject_id.data = entry.subject_id or 0
        form.day_of_week.data = str(entry.day_of_week) if entry.day_of_week is not None else "0"

    if form.validate_on_submit():
        entry.title = form.title.data.strip()
        entry.subject_id = form.subject_id.data if form.subject_id.data != 0 else None
        entry.entry_type = form.entry_type.data
        entry.day_of_week = int(form.day_of_week.data) if form.entry_type.data == "recurring" else None
        entry.specific_date = form.specific_date.data if form.entry_type.data == "one_off" else None
        entry.start_time = form.start_time.data
        entry.end_time = form.end_time.data
        db.session.commit()
        flash("Timetable entry updated.", "success")
        return redirect(url_for("timetable.grid"))

    return render_template("timetable/form.html", form=form, mode="edit", entry=entry)


@timetable_bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    entry = get_entry_or_404(entry_id, current_user.id)
    db.session.delete(entry)
    db.session.commit()
    flash("Timetable entry deleted.", "info")
    return redirect(url_for("timetable.grid"))