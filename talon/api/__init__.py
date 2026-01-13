"""API blueprint and routes."""

from flask import Blueprint
from flask_restx import Api

from talon.api.notifications import notifications_ns
from talon.api.scans import scans_ns
from talon.api.vulnerabilities import vulnerabilities_ns

# Create blueprint
api_blueprint = Blueprint("api", __name__)

# Create API
api = Api(
    api_blueprint,
    title="Talon API",
    version="1.0",
    description="Threat Intelligence Hub API",
    doc="/docs",
)

# Register namespaces
api.add_namespace(scans_ns, path="/scans")
api.add_namespace(vulnerabilities_ns, path="/vulnerabilities")
api.add_namespace(notifications_ns, path="/notifications")
