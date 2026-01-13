"""Vulnerabilities API endpoints."""

from uuid import UUID

from flask import request
from flask_restx import Namespace, Resource, fields

from talon.extensions import db
from talon.models import Vulnerability
from talon.services.threat_scoring import ThreatScoringService
from shared.logging import get_logger

logger = get_logger(__name__)

vulnerabilities_ns = Namespace("vulnerabilities", description="Vulnerability management")

# API Models
vulnerability_model = vulnerabilities_ns.model("Vulnerability", {
    "id": fields.String(description="Vulnerability ID"),
    "cve_id": fields.String(required=True, description="CVE identifier"),
    "description": fields.String(description="Vulnerability description"),
    "severity": fields.String(description="Severity level"),
    "cvss_score": fields.Float(description="CVSS score"),
    "cvss_vector": fields.String(description="CVSS vector string"),
    "affected_packages": fields.List(fields.Raw, description="Affected packages"),
    "references": fields.List(fields.Raw, description="Reference links"),
    "threat_score": fields.Float(description="ML-based threat score"),
    "published_date": fields.DateTime(description="Publication date"),
    "modified_date": fields.DateTime(description="Last modification date"),
})


@vulnerabilities_ns.route("")
class VulnerabilityList(Resource):
    """Vulnerability collection resource."""

    @vulnerabilities_ns.doc("list_vulnerabilities")
    @vulnerabilities_ns.param("severity", "Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)")
    @vulnerabilities_ns.param("min_cvss", "Minimum CVSS score", type=float)
    @vulnerabilities_ns.param("search", "Search in CVE ID or description")
    @vulnerabilities_ns.param("limit", "Maximum results", type=int, default=50)
    @vulnerabilities_ns.param("offset", "Result offset", type=int, default=0)
    @vulnerabilities_ns.marshal_list_with(vulnerability_model)
    def get(self):
        """List vulnerabilities with filtering."""
        severity = request.args.get("severity")
        min_cvss = request.args.get("min_cvss", type=float)
        search = request.args.get("search")
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        query = Vulnerability.query
        
        if severity:
            query = query.filter(Vulnerability.severity == severity.upper())
        if min_cvss is not None:
            query = query.filter(Vulnerability.cvss_score >= min_cvss)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Vulnerability.cve_id.ilike(search_term),
                    Vulnerability.description.ilike(search_term),
                )
            )
        
        query = query.order_by(Vulnerability.cvss_score.desc().nullslast())
        vulns = query.offset(offset).limit(limit).all()
        
        return [v.to_dict() for v in vulns]


@vulnerabilities_ns.route("/<string:cve_id>")
@vulnerabilities_ns.param("cve_id", "CVE identifier (e.g., CVE-2021-44228)")
class VulnerabilityResource(Resource):
    """Single vulnerability resource."""

    @vulnerabilities_ns.doc("get_vulnerability")
    @vulnerabilities_ns.marshal_with(vulnerability_model)
    def get(self, cve_id: str):
        """Get vulnerability details by CVE ID."""
        vuln = Vulnerability.query.filter_by(cve_id=cve_id.upper()).first()
        if not vuln:
            vulnerabilities_ns.abort(404, f"Vulnerability {cve_id} not found")
        
        return vuln.to_dict()

    @vulnerabilities_ns.doc("update_vulnerability")
    @vulnerabilities_ns.expect(vulnerability_model)
    @vulnerabilities_ns.marshal_with(vulnerability_model)
    def put(self, cve_id: str):
        """Update vulnerability details."""
        vuln = Vulnerability.query.filter_by(cve_id=cve_id.upper()).first()
        if not vuln:
            vulnerabilities_ns.abort(404, f"Vulnerability {cve_id} not found")
        
        data = request.json
        
        for field in ["description", "severity", "cvss_score", "cvss_vector", 
                      "affected_packages", "references"]:
            if field in data:
                setattr(vuln, field, data[field])
        
        db.session.commit()
        logger.info(f"Updated vulnerability: {cve_id}")
        
        return vuln.to_dict()


@vulnerabilities_ns.route("/<string:cve_id>/threat-score")
@vulnerabilities_ns.param("cve_id", "CVE identifier")
class VulnerabilityThreatScore(Resource):
    """Vulnerability threat score resource."""

    @vulnerabilities_ns.doc("get_threat_score")
    def get(self, cve_id: str):
        """Get ML-based threat score for a vulnerability."""
        vuln = Vulnerability.query.filter_by(cve_id=cve_id.upper()).first()
        if not vuln:
            vulnerabilities_ns.abort(404, f"Vulnerability {cve_id} not found")
        
        scoring_service = ThreatScoringService()
        score, factors = scoring_service.calculate_threat_score(vuln)
        
        return {
            "cve_id": vuln.cve_id,
            "threat_score": score,
            "factors": factors,
            "severity": vuln.severity,
            "cvss_score": float(vuln.cvss_score) if vuln.cvss_score else None,
        }

    @vulnerabilities_ns.doc("recalculate_threat_score")
    def post(self, cve_id: str):
        """Recalculate and update threat score."""
        vuln = Vulnerability.query.filter_by(cve_id=cve_id.upper()).first()
        if not vuln:
            vulnerabilities_ns.abort(404, f"Vulnerability {cve_id} not found")
        
        scoring_service = ThreatScoringService()
        score, factors = scoring_service.calculate_threat_score(vuln)
        
        vuln.threat_score = score
        db.session.commit()
        
        logger.info(f"Updated threat score for {cve_id}: {score}")
        
        return {
            "cve_id": vuln.cve_id,
            "threat_score": score,
            "factors": factors,
        }


@vulnerabilities_ns.route("/stats")
class VulnerabilityStats(Resource):
    """Vulnerability statistics resource."""

    @vulnerabilities_ns.doc("get_vulnerability_stats")
    def get(self):
        """Get vulnerability statistics."""
        from sqlalchemy import func
        
        total = Vulnerability.query.count()
        
        by_severity = db.session.query(
            Vulnerability.severity,
            func.count(Vulnerability.id).label("count")
        ).group_by(Vulnerability.severity).all()
        
        avg_cvss = db.session.query(
            func.avg(Vulnerability.cvss_score)
        ).scalar()
        
        high_threat = Vulnerability.query.filter(
            Vulnerability.threat_score >= 80
        ).count()
        
        return {
            "total_vulnerabilities": total,
            "by_severity": {sev: count for sev, count in by_severity},
            "average_cvss_score": round(float(avg_cvss), 2) if avg_cvss else 0,
            "high_threat_count": high_threat,
        }
