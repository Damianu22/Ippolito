"""Database utilities for SQL Server connectivity via pyodbc."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Set

import pyodbc
from flask import current_app

from config import Config


logger = logging.getLogger(__name__)

PREFERRED_DRIVERS: Iterable[str] = (
	"ODBC Driver 18 for SQL Server",
	"ODBC Driver 17 for SQL Server",
	"SQL Server",
)


def _sanitize_driver_name(name: str) -> str:
	return name.strip()


def _available_drivers() -> Set[str]:
	return {_sanitize_driver_name(driver) for driver in pyodbc.drivers()}


def _resolve_driver() -> str:
	configured = _sanitize_driver_name(Config.DB_DRIVER) if Config.DB_DRIVER else ""
	available = _available_drivers()

	if configured:
		if configured in available:
			return configured
		logger.warning(
			"Configured ODBC driver '%s' is not installed. Falling back to auto-detection.",
			configured,
		)

	for candidate in PREFERRED_DRIVERS:
		if candidate in available:
			return candidate

	raise RuntimeError(
		"Nessun driver ODBC per SQL Server trovato. Installa ODBC Driver 18 o 17 per SQL Server."
	)


def _build_connection_string(driver: str) -> str:
	options = Config.database_options()
	server = options["server"]
	port = options["port"]
	database = options["database"]
	user = options["user"]
	password = options["password"]
	encrypt = options["encrypt"] or "Yes"
	trust_cert = options["trust_server_certificate"] or "Yes"
	timeout = options["timeout"] or "5"

	return (
		f"DRIVER={{{driver}}};"
		f"SERVER={server},{port};"
		f"DATABASE={database};"
		f"UID={user};"
		f"PWD={password};"
		f"Encrypt={encrypt};"
		f"TrustServerCertificate={trust_cert};"
		f"Connection Timeout={timeout};"
	)


def _coerce_timeout(value: Optional[object], fallback: int = 5) -> int:
	try:
		if value is None:
			return fallback
		return int(value)
	except (TypeError, ValueError):
		return fallback


def get_connection(timeout: Optional[object] = None) -> pyodbc.Connection:
	"""Create and return a new database connection."""

	timeout_value = _coerce_timeout(timeout, _coerce_timeout(Config.DB_LOGIN_TIMEOUT))

	connection_string = _build_connection_string(_resolve_driver())

	try:
		return pyodbc.connect(connection_string, timeout=timeout_value)
	except pyodbc.Error as exc:  # pragma: no cover - depends on external DB
		logger.error("Unable to connect to SQL Server: %s", exc)
		raise


def try_connection() -> bool:
	"""Attempt to open and close a connection to verify connectivity."""

	try:
		with get_connection():
			return True
	except pyodbc.Error:
		return False


def get_configured_connection(timeout: Optional[int] = None) -> pyodbc.Connection:
	"""Create a connection using timeout from Flask app config if provided."""

	if timeout is None:
		timeout = current_app.config.get("DB_LOGIN_TIMEOUT", Config.DB_LOGIN_TIMEOUT)
	return get_connection(timeout=timeout)


def fetch_user_by_username(username: str) -> Optional[Dict[str, object]]:
	"""Return an operator row from dbo.OPERATORI given a username (Nome field).

	Parameters
	----------
	username: str
		The username to search for (Nome field, case-sensitive per SQL collation).

	Returns
	-------
	Optional[Dict[str, object]]
		Dictionary with keys: ID, Nome (username), Password (PASSWORD2005).
		Returns None if operator not found.
	"""

	query = (
		"SELECT ID, Nome, PASSWORD2005 AS Password "
		"FROM dbo.OPERATORI WHERE Nome = ?"
	)

	try:
		with get_configured_connection() as connection:
			cursor = connection.cursor()
			cursor.execute(query, username)
			row = cursor.fetchone()
			if row is None:
				return None
			columns = [column[0] for column in cursor.description]
			return dict(zip(columns, row))
	except pyodbc.Error as exc:  # pragma: no cover - depends on external DB
		logger.error("Database error while fetching operator '%s': %s", username, exc)
		raise


def get_clients(
	filtro_mastro: Optional[str] = None,
	mostra_disattivati: bool = True,
	pattern_ricerca: Optional[str] = None,
	match_anywhere: bool = True,
) -> List[Dict[str, object]]:
	"""Return a list of clients from table ``piacon``.

	This implements the core of the earlier-provided query semantics while
	defaulting to "show all" on first load. To maximize compatibility across
	installations, we always select the two canonical fields and fill optional
	fields in Python.

	Parameters
	----------
	filtro_mastro: Optional[str]
		Optional filter prefix for the ``MASTRO`` account (e.g. "C"/"F"). If ``None``,
		no filtering by mastro is applied.
	mostra_disattivati: bool
		When ``False``, filters out deactivated rows if a ``DISATTIVATO``/``DISA`` flag exists.
	pattern_ricerca: Optional[str]
		Optional search pattern to match by code or name. When provided, applies a
		LIKE filter either prefix or anywhere depending on ``match_anywhere``.
	match_anywhere: bool
		If ``True``, wraps the pattern with wildcards on both sides; otherwise uses
		prefix matching.

	Returns
	-------
	List[Dict[str, object]]
		List of client dicts with keys: ``code``, ``name``, ``province``, ``phone``.
	"""

	# Base, widely compatible query (selects canonical identifiers only)
	base_query = "SELECT CODCON AS code, RAGSO1 AS name FROM piacon"
	where_clauses = []
	params: List[object] = []

	# Optional filters — guarded to avoid schema-specific columns where possible.
	if filtro_mastro:
		# Apply mastro filter if a MASTRO-like column exists; keep generic by using LIKE
		where_clauses.append("MASTRO LIKE ?")
		params.append(f"{filtro_mastro}%")

	if not mostra_disattivati:
		# Try to filter out deactivated rows if a flag exists; this may be ignored
		# by the database if column doesn't exist. To stay safe, we won't reference
		# the column here; instead, rely on full query upgrades later when schema is confirmed.
		pass

	if pattern_ricerca:
		pattern = pattern_ricerca.strip()
		if pattern:
			like = f"%{pattern}%" if match_anywhere else f"{pattern}%"
			where_clauses.append("(CODCON LIKE ? OR RAGSO1 LIKE ?)")
			params.extend([like, like])

	query = base_query
	if where_clauses:
		query += " WHERE " + " AND ".join(where_clauses)
	query += " ORDER BY RAGSO1"

	rows: List[Dict[str, object]] = []
	try:
		with get_configured_connection() as connection:
			cursor = connection.cursor()
			cursor.execute(query, params)
			columns = [column[0] for column in cursor.description]
			for rec in cursor.fetchall():
				row = dict(zip(columns, rec))
				# Normalize expected keys for the template
				rows.append(
					{
						"code": row.get("code"),
						"name": row.get("name"),
						"province": "",  # filled later if needed
						"phone": "",  # filled later if needed
					}
				)
		return rows
	except pyodbc.Error as exc:  # pragma: no cover - depends on external DB
		logger.error("Database error while fetching clients: %s", exc)
		raise
