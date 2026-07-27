"""Global search route."""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.search.services import global_search

search_bp = Blueprint("search", __name__, template_folder="../templates/search")


@search_bp.route("/")
@login_required
def results():
    query = request.args.get("q", "")
    data = global_search(current_user.id, query)
    return render_template("search/results.html", data=data)