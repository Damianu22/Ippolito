"""Blueprint routes for the IppolitoPisaniApp."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import (
	Blueprint,
	Response,
	current_app,
	flash,
	g,
	redirect,
	render_template,
	request,
	session,
	url_for,
)

import pyodbc

from .db import fetch_user_by_username, get_clients


main_bp = Blueprint("main", __name__)


def login_required(view: Callable[..., Response]) -> Callable[..., Response]:
	"""Simple decorator to ensure a user is authenticated."""

	@wraps(view)
	def wrapped_view(*args: Any, **kwargs: Any) -> Response:
		if session.get("user") is None:
			flash("Effettua il login per continuare.", "warning")
			return redirect(url_for("main.login"))
		return view(*args, **kwargs)

	return wrapped_view


@main_bp.before_app_request
def load_logged_in_user() -> None:
	"""Store the current logged user in the global request context."""

	g.user = session.get("user")


@main_bp.route("/", methods=["GET", "POST"])
def login() -> Response:
	"""Render and process the login form."""

	if session.get("user"):
		return redirect(url_for("main.dashboard"))

	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "").strip()

		if username and password:
			try:
				user_record = fetch_user_by_username(username)
			except pyodbc.Error:
				current_app.logger.exception("Errore durante il recupero dell'operatore '%s'", username)
				flash("Servizio di autenticazione momentaneamente non disponibile.", "error")
				return render_template("login.html", title="Accesso"), 503

			if user_record and password == user_record.get("Password"):
				session.clear()
				session["user"] = user_record.get("Nome")
				session["user_id"] = user_record.get("ID")
				session["user_fullname"] = user_record.get("Nome")
				flash("Accesso eseguito con successo.", "success")
				return redirect(url_for("main.dashboard"))
			flash("Credenziali non valide.", "error")
		else:
			flash("Inserisci nome utente e password.", "error")

	return render_template("login.html", title="Accesso")


@main_bp.route("/dashboard")
@login_required
def dashboard() -> Response:
	"""Simple stub dashboard after login."""

	return render_template("dashboard.html", title="Dashboard", user=g.user)


@main_bp.route("/clienti")
@login_required
def vista_clienti() -> Response:
	"""Render clients listing - shows only active clients (Rifconto prefix '01').

	Query parameters:
	- q: search text (optional)
	"""

	# Get search text from query string
	search_text = request.args.get("q", "").strip()

	try:
		# Always show only clients (prefix '01'), exclude deactivated, match anywhere
		clients = get_clients(
			filtro_mastro="01",  # Hardcoded for clienti only
			mostra_disattivati=False,  # Always exclude deactivated
			pattern_ricerca=search_text if search_text else None,
			match_anywhere=True  # Always match anywhere in search
		)
	except pyodbc.Error:
		current_app.logger.exception("Errore durante il caricamento dei clienti")
		clients = []
		flash("Impossibile recuperare i clienti in questo momento.", "error")

	return render_template(
		"vista_clienti.html",
		title="Clienti",
		clients=clients,
		search_text=search_text
	)


@main_bp.route("/logout")
@login_required
def logout() -> Response:
	"""Terminate the user session and redirect to the login page."""

	session.clear()
	flash("Sei stato disconnesso.", "info")
	return redirect(url_for("main.login"))
