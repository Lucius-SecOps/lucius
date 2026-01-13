"""Flask extensions initialization."""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions (without app binding)
db = SQLAlchemy()
migrate = Migrate()
