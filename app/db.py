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
	mostra_disattivati: bool = False,
	pattern_ricerca: Optional[str] = None,
	match_anywhere: bool = True,
) -> List[Dict[str, object]]:
	"""Fetch clients from piacon with same logic as desktop EstraiDati.

	Desktop query logic:
	- FROM piacon LEFT JOIN bancheapp ON piacon.banca = bancheapp.codice
	- LEFT JOIN PAGAMENTI ON piacon.PAGAMENTO = PAGAMENTI.Codice
	- WHERE ragsoc > ' ' AND codice <> '0000' AND Rifconto LIKE 'filtroMastro%'
	- AND (disattivato condition based on chktutte)
	- AND (search in ragsoc, denominazione, citta, partitaiva, codfisc)
	- ORDER BY Ragsoc

	For web app we only need: Ragsoc (concatenated with denominazione) and Citta.

	Parameters
	----------
	filtro_mastro: Optional[str]
		Prefix for Rifconto (e.g., "C" for clienti, "F" for fornitori).
	mostra_disattivati: bool
		If True, include deactivated records (chktutte checked in desktop).
	pattern_ricerca: Optional[str]
		Search text to filter across multiple fields.
	match_anywhere: bool
		If True, use LIKE '%text%' (chklike checked), else LIKE 'text%'.

	Returns
	-------
	List[Dict[str, object]]
		Each dict has: ragsoc (concatenated), citta.
	"""

	filtro_val = (filtro_mastro or "").strip()
	if not filtro_val:
		# If no filter provided, match all
		rifconto_like = "%"
	else:
		rifconto_like = f"{filtro_val}%"

	search_raw = (pattern_ricerca or "").strip()
	if not search_raw:
		pattern_like = "%"
	else:
		# Desktop uses [ as placeholder, then replaces with % or empty
		# chklike.Checked -> replace [ with %  (match anywhere)
		# else -> replace [ with empty (prefix match)
		pattern_like = f"%{search_raw}%" if match_anywhere else f"{search_raw}%"

	results: List[Dict[str, object]] = []
	try:
		with get_configured_connection() as connection:
			cursor = connection.cursor()

			# Build SQL matching desktop logic
			# Desktop uses CONCAT for SQL Server
			ragsoc_expr = "CONCAT(piacon.Ragsoc, ' ', piacon.denominazione) AS Ragsoc"
			citta_expr = "piacon.Citta"

			# Desktop query includes LEFT JOINs but we only need piacon for ragsoc/citta
			query = f"""
				SELECT {ragsoc_expr}, {citta_expr}
				FROM piacon
				LEFT JOIN bancheapp ON piacon.banca = bancheapp.codice
				LEFT JOIN PAGAMENTI ON piacon.PAGAMENTO = PAGAMENTI.Codice
				WHERE piacon.Ragsoc > ' '
				  AND piacon.codice <> '0000'
				  AND piacon.Rifconto LIKE ?
			"""

			params: List[object] = [rifconto_like]

			# Disattivato condition (from desktop condizione2)
			if not mostra_disattivati:
				# Desktop: " AND ISNULL(piacon.disattivato,0) = 0 "
				query += " AND ISNULL(piacon.disattivato, 0) = 0"

			# Search condition (from desktop condizione)
			# Desktop searches: ragsoc, denominazione, citta, partitaIVA, codfisc
			query += """
				  AND (
				      piacon.Ragsoc LIKE ? OR
				      piacon.denominazione LIKE ? OR
				      piacon.citta LIKE ? OR
				      piacon.partitaIVA LIKE ? OR
				      piacon.codfisc LIKE ?
				  )
			"""
			# Add pattern 5 times (one for each searchable column)
			params.extend([pattern_like] * 5)

			# Order by (desktop uses "order by Ragsoc")
			query += " ORDER BY Ragsoc"

			cursor.execute(query, params)
			for rec in cursor.fetchall():
				results.append({
					"ragsoc": rec[0] if rec[0] else "",
					"citta": rec[1] if rec[1] else ""
				})

			return results

	except pyodbc.Error as exc:  # pragma: no cover - depends on external DB
		logger.error("Database error while fetching clients (desktop-compatible query): %s", exc)
		raise
