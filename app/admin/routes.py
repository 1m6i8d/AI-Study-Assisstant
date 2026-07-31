"""Admin routes: platform overview + user management."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.auth.decorators import admin_required
from app.admin.services import (
    get_pending_users, get_all_users, get_user_stats, get_platform_stats,
    set_user_status, delete_user,
)

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    return redirect(url_for("admin.overview"))


@admin_bp.route("/overview")
@login_required
@admin_required
def overview():
    stats = get_platform_stats()
    user_stats = get_user_stats()
    return render_template("admin/overview.html", stats=stats, user_stats=user_stats)


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    search = request.args.get("q", "").strip()
    sort = request.args.get("sort", "created_at")
    direction = request.args.get("dir", "desc")

    pending = get_pending_users()
    all_users = get_all_users(search=search or None, sort=sort, direction=direction)
    stats = get_user_stats()

    return render_template(
        "admin/users.html", pending=pending, all_users=all_users, stats=stats,
        search=search, sort=sort, direction=direction,
    )


@admin_bp.route("/users/<int:user_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve(user_id):
    user = set_user_status(user_id, "approved")
    flash(f'"{user.username}" approved.', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject(user_id):
    user = set_user_status(user_id, "rejected")
    flash(f'"{user.username}" rejected.', "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@login_required
@admin_required
def suspend(user_id):
    if user_id == current_user.id:
        flash("You cannot suspend your own account.", "error")
        return redirect(url_for("admin.users"))
    user = set_user_status(user_id, "suspended")
    flash(f'"{user.username}" suspended.', "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reactivate", methods=["POST"])
@login_required
@admin_required
def reactivate(user_id):
    user = set_user_status(user_id, "approved")
    flash(f'"{user.username}" reactivated.', "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin.users"))
    delete_user(user_id)
    flash("User and all their data permanently deleted.", "info")
    return redirect(url_for("admin.users"))