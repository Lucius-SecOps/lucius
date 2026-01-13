"""Threat scoring Celery tasks."""

from talon.celery_app import celery
from talon.extensions import db
from talon.models import Vulnerability
from talon.services.threat_scoring import ThreatScoringService
from shared.logging import get_logger

logger = get_logger(__name__)


@celery.task
def update_threat_scores() -> dict:
    """
    Update threat scores for all vulnerabilities.

    This task runs periodically to recalculate scores
    based on age and other time-sensitive factors.

    Returns:
        Summary of updated scores
    """
    service = ThreatScoringService()
    
    # Get vulnerabilities that need score updates
    # Focus on those without scores or older than 24 hours
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    vulnerabilities = Vulnerability.query.filter(
        db.or_(
            Vulnerability.threat_score.is_(None),
            Vulnerability.updated_at < cutoff,
        )
    ).limit(500).all()
    
    if not vulnerabilities:
        return {"updated": 0}
    
    logger.info(f"Updating threat scores for {len(vulnerabilities)} vulnerabilities")
    
    updated = 0
    for vuln in vulnerabilities:
        try:
            score, _ = service.calculate_threat_score(vuln)
            vuln.threat_score = score
            updated += 1
        except Exception as e:
            logger.error(f"Error calculating score for {vuln.cve_id}: {e}")
    
    db.session.commit()
    
    logger.info(f"Updated {updated} threat scores")
    
    return {"updated": updated}


@celery.task
def calculate_single_threat_score(cve_id: str) -> dict:
    """
    Calculate threat score for a single vulnerability.

    Args:
        cve_id: CVE identifier

    Returns:
        Score result
    """
    vulnerability = Vulnerability.query.filter_by(cve_id=cve_id).first()
    
    if not vulnerability:
        return {"status": "error", "message": f"Vulnerability {cve_id} not found"}
    
    service = ThreatScoringService()
    score, factors = service.calculate_threat_score(vulnerability)
    
    vulnerability.threat_score = score
    db.session.commit()
    
    return {
        "status": "success",
        "cve_id": cve_id,
        "score": score,
        "factors": factors,
    }


@celery.task
def identify_high_threat_vulnerabilities(threshold: float = 70.0) -> dict:
    """
    Identify vulnerabilities above threat threshold.

    Args:
        threshold: Minimum threat score

    Returns:
        List of high-threat CVEs
    """
    high_threat = Vulnerability.query.filter(
        Vulnerability.threat_score >= threshold
    ).order_by(
        Vulnerability.threat_score.desc()
    ).limit(100).all()
    
    return {
        "count": len(high_threat),
        "vulnerabilities": [
            {
                "cve_id": v.cve_id,
                "severity": v.severity,
                "threat_score": float(v.threat_score) if v.threat_score else None,
            }
            for v in high_threat
        ],
    }
