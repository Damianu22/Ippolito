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
			rifconto_expr = "piacon.Rifconto"

			# Desktop query includes LEFT JOINs but we only need piacon for ragsoc/citta/rifconto
			query = f"""
				SELECT {ragsoc_expr}, {citta_expr}, {rifconto_expr}
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
					"citta": rec[1] if rec[1] else "",
					"rifconto": rec[2] if rec[2] else ""
				})

			return results

	except pyodbc.Error as exc:  # pragma: no cover - depends on external DB
		logger.error("Database error while fetching clients (desktop-compatible query): %s", exc)
		raise


def get_cliente_nome(rifconto: str) -> Optional[str]:
	"""Get client name (Ragsoc) by Rifconto code.

	Parameters
	----------
	rifconto: str
		Client's Rifconto code from piacon table.

	Returns
	-------
	Optional[str]
		Client's Ragsoc (company name) or None if not found.
	"""

	try:
		with get_configured_connection() as connection:
			cursor = connection.cursor()
			query = """
				SELECT CONCAT(Ragsoc, ' ', denominazione) AS NomeCliente
				FROM piacon
				WHERE Rifconto = ?
			"""
			cursor.execute(query, rifconto)
			row = cursor.fetchone()
			return row[0] if row else None
	except pyodbc.Error as exc:
		logger.error("Database error while fetching client name for rifconto '%s': %s", rifconto, exc)
		return None


def get_ordini_cliente(codcf: str) -> List[Dict[str, object]]:
	"""Fetch orders for a specific client from tabfat02 with article descriptions.

	Query logic:
	- FROM tabfat02 INNER JOIN ARTICOLI ON tabfat02.CODART = ARTICOLI.CODART
	- WHERE tipdoc = 'OC' AND codcf = ?
	- ORDER BY Datdoc DESC (most recent first)

	Parameters
	----------
	codcf: str
		Client's Rifconto code (from piacon.Rifconto).

	Returns
	-------
	List[Dict[str, object]]
		Each dict has: numdoc, datdoc, pratica_numero, codart, desart.
	"""

	results: List[Dict[str, object]] = []
	try:
		with get_configured_connection() as connection:
			cursor = connection.cursor()

			query = """
				SELECT 
					tabfat02.NUMDOC,
					tabfat02.Datdoc,
					tabfat02.PraticaNumero,
					tabfat02.CODART,
					ARTICOLI.DESART
				FROM tabfat02
				INNER JOIN ARTICOLI ON tabfat02.CODART = ARTICOLI.CODART
				WHERE tabfat02.tipdoc = 'OC'
				  AND tabfat02.codcf = ?
				ORDER BY tabfat02.Datdoc DESC
			"""

			cursor.execute(query, codcf)
			
			# Group by numdoc_raw to count articles per order
			orders_dict: Dict[str, Dict[str, object]] = {}
			
			for rec in cursor.fetchall():
				numdoc_raw = rec[0]
				datdoc = rec[1]
				
				# Format numdoc as YYNNNN (last 2 digits of year + 4-digit padded number)
				numdoc_formatted = ""
				if datdoc and numdoc_raw is not None:
					try:
						# Extract year from datdoc
						if hasattr(datdoc, 'year'):
							year_suffix = str(datdoc.year)[-2:]  # Last 2 digits
						else:
							# If datdoc is string, try to parse
							year_suffix = str(datdoc)[:4][-2:] if len(str(datdoc)) >= 4 else "00"
						
						# Pad numdoc to 4 digits
						numdoc_padded = str(int(numdoc_raw)).zfill(4)
						numdoc_formatted = f"{year_suffix}{numdoc_padded}"
					except (ValueError, AttributeError):
						numdoc_formatted = str(numdoc_raw) if numdoc_raw else ""
				else:
					numdoc_formatted = str(numdoc_raw) if numdoc_raw else ""
				
				# Use numdoc_raw as key to group
				key = str(numdoc_raw)
				
				if key not in orders_dict:
					# First time seeing this numdoc - create entry
					orders_dict[key] = {
						"numdoc": numdoc_formatted,
						"numdoc_raw": numdoc_raw,
						"datdoc": datdoc,
						"pratica_numero": rec[2] if rec[2] else "",
						"codart": rec[3] if rec[3] else "",
						"desart": rec[4] if rec[4] else "",
						"num_articoli": 1
					}
				else:
					# Already seen - increment counter
					orders_dict[key]["num_articoli"] += 1
			
			# Convert dict to list
			results = list(orders_dict.values())
			
			return results

	except pyodbc.Error as exc:  # pragma: no cover - depends on external DB
		logger.error("Database error while fetching orders for client '%s': %s", codcf, exc)
		raise


def get_articoli_ordine(codcf: str, numdoc_raw: str) -> List[Dict[str, object]]:
	"""Fetch all articles for a specific order (numdoc) of a client.

	Parameters
	----------
	codcf: str
		Client's Rifconto code.
	numdoc_raw: str
		Raw NUMDOC value (not formatted).

	Returns
	-------
	List[Dict[str, object]]
		Each dict has: numdoc, datdoc, pratica_numero, codart, desart.
	"""

	results: List[Dict[str, object]] = []
	try:
		with get_configured_connection() as connection:
			cursor = connection.cursor()

			query = """
				SELECT 
					tabfat02.NUMDOC,
					tabfat02.Datdoc,
					tabfat02.PraticaNumero,
					tabfat02.CODART,
					ARTICOLI.DESART
				FROM tabfat02
				INNER JOIN ARTICOLI ON tabfat02.CODART = ARTICOLI.CODART
				WHERE tabfat02.tipdoc = 'OC'
				  AND tabfat02.codcf = ?
				  AND tabfat02.NUMDOC = ?
				ORDER BY tabfat02.PraticaNumero
			"""

			cursor.execute(query, (codcf, numdoc_raw))
			for rec in cursor.fetchall():
				numdoc_raw_val = rec[0]
				datdoc = rec[1]
				
				# Format numdoc as YYNNNN
				numdoc_formatted = ""
				if datdoc and numdoc_raw_val is not None:
					try:
						if hasattr(datdoc, 'year'):
							year_suffix = str(datdoc.year)[-2:]
						else:
							year_suffix = str(datdoc)[:4][-2:] if len(str(datdoc)) >= 4 else "00"
						
						numdoc_padded = str(int(numdoc_raw_val)).zfill(4)
						numdoc_formatted = f"{year_suffix}{numdoc_padded}"
					except (ValueError, AttributeError):
						numdoc_formatted = str(numdoc_raw_val) if numdoc_raw_val else ""
				else:
					numdoc_formatted = str(numdoc_raw_val) if numdoc_raw_val else ""
				
				results.append({
					"numdoc": numdoc_formatted,
					"numdoc_raw": numdoc_raw_val,
					"datdoc": datdoc,
					"pratica_numero": rec[2] if rec[2] else "",
					"codart": rec[3] if rec[3] else "",
					"desart": rec[4] if rec[4] else ""
				})

			return results

	except pyodbc.Error as exc:
		logger.error("Database error while fetching articles for order '%s' of client '%s': %s", numdoc_raw, codcf, exc)
		raise
