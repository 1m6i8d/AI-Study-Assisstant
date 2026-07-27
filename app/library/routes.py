from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.library.forms import AddVideoForm, AddBookForm
from app.library.services import (
    get_library_shelves, get_shelf_items, add_manual_video, add_manual_book, delete_library_item
)

library_bp = Blueprint("library", __name__, template_folder="../templates/library")


@library_bp.route("/")
@login_required
def shelves():
    shelf_data = get_library_shelves(current_user.id)
    return render_template("library/shelves.html", shelf_data=shelf_data)


@library_bp.route("/subject/<int:subject_id>")
@login_required
def shelf(subject_id):
    subject, videos, books = get_shelf_items(subject_id, current_user.id)
    video_form = AddVideoForm()
    book_form = AddBookForm()
    return render_template(
        "library/shelf.html", subject=subject, videos=videos, books=books,
        video_form=video_form, book_form=book_form,
    )


@library_bp.route("/subject/<int:subject_id>/add-video", methods=["POST"])
@login_required
def add_video(subject_id):
    form = AddVideoForm()
    if form.validate_on_submit():
        result = add_manual_video(current_user.id, subject_id, form.youtube_url.data.strip())
        if result == "duplicate":
            flash("That video is already saved to this shelf.", "info")
        elif result:
            flash("Video added.", "success")
        else:
            flash("Couldn't find that video — check the URL.", "error")
    return redirect(url_for("library.shelf", subject_id=subject_id))


@library_bp.route("/subject/<int:subject_id>/add-book", methods=["POST"])
@login_required
def add_book(subject_id):
    form = AddBookForm()
    if form.validate_on_submit():
        result = add_manual_book(current_user.id, subject_id, form.title_query.data.strip())
        if result == "duplicate":
            flash("That book is already saved to this shelf.", "info")
        elif result:
            flash("Book added.", "success")
        else:
            flash("Couldn't find a matching book.", "error")
    return redirect(url_for("library.shelf", subject_id=subject_id))


@library_bp.route("/item/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    delete_library_item(item_id, current_user.id)
    flash("Removed from library.", "info")
    return redirect(request.referrer or url_for("library.shelves"))