"""Application configuration module."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from the .env file located at the project root.
load_dotenv(BASE_DIR / ".env")


class Config:
	"""Base configuration loaded from environment variables."""

	SECRET_KEY: str = os.getenv("SECRET_KEY", "unsafe-development-secret")

	DB_DRIVER: str = os.getenv("DB_DRIVER", "")
	DB_SERVER: str = os.getenv("DB_SERVER", "")
	DB_PORT: str = os.getenv("DB_PORT", "1433")
	DB_NAME: str = os.getenv("DB_NAME", "")
	DB_USER: str = os.getenv("DB_USER", "")
	DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
	DB_ENCRYPT: str = os.getenv("DB_ENCRYPT", "Yes")
	DB_TRUST_SERVER_CERTIFICATE: str = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "Yes")
	DB_LOGIN_TIMEOUT: str = os.getenv("DB_LOGIN_TIMEOUT", "5")

	SESSION_COOKIE_HTTPONLY: bool = True
	SESSION_COOKIE_SAMESITE: str = "Lax"

	@classmethod
	def database_options(cls) -> Dict[str, str]:
		"""Return the database credentials/options as a dictionary."""

		return {
			"driver": cls.DB_DRIVER,
			"server": cls.DB_SERVER,
			"port": cls.DB_PORT,
			"database": cls.DB_NAME,
			"user": cls.DB_USER,
			"password": cls.DB_PASSWORD,
			"encrypt": cls.DB_ENCRYPT,
			"trust_server_certificate": cls.DB_TRUST_SERVER_CERTIFICATE,
			"timeout": cls.DB_LOGIN_TIMEOUT,
		}

	@classmethod
	def pyodbc_connection_string(cls) -> str:
		"""Build a pyodbc connection string using SQL Server authentication."""

		options = cls.database_options()
		server = options["server"]
		port = options["port"]
		database = options["database"]
		user = options["user"]
		password = options["password"]
		encrypt = options["encrypt"]
		trust_cert = options["trust_server_certificate"]

		return (
			f"DRIVER={{{options['driver']}}};"
			f"SERVER={server},{port};"
			f"DATABASE={database};"
			f"UID={user};"
			f"PWD={password};"
			f"Encrypt={encrypt};"
			f"TrustServerCertificate={trust_cert};"
			f"Connection Timeout={options['timeout']};"
		)

