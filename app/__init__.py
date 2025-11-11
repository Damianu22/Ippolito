"""Application factory for IppolitoPisaniApp."""

from __future__ import annotations

from flask import Flask

from config import Config


def create_app() -> Flask:
	"""Create and configure the Flask application instance."""

	app = Flask(
		__name__,
		template_folder="templates",
		static_folder="static",
	)

	app.config.from_object(Config)

	# Apply small Jinja tweaks for cleaner templates.
	app.jinja_env.trim_blocks = True
	app.jinja_env.lstrip_blocks = True

	from .routes import main_bp

	app.register_blueprint(main_bp)

	return app
