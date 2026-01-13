"""ML-based threat scoring service."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np

from talon.models import Vulnerability
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ThreatFactors:
    """Factors contributing to threat score."""
    
    cvss_score: float
    severity_weight: float
    exploit_likelihood: float
    age_factor: float
    affected_scope: float
    
    def to_dict(self) -> dict[str, float]:
        return {
            "cvss_score": self.cvss_score,
            "severity_weight": self.severity_weight,
            "exploit_likelihood": self.exploit_likelihood,
            "age_factor": self.age_factor,
            "affected_scope": self.affected_scope,
        }


class ThreatScoringService:
    """
    ML-based threat scoring for vulnerabilities.
    
    Combines multiple factors to produce a 0-100 threat score
    that helps prioritize remediation efforts.
    """

    # Severity weights
    SEVERITY_WEIGHTS = {
        "CRITICAL": 1.0,
        "HIGH": 0.8,
        "MEDIUM": 0.5,
        "LOW": 0.2,
        "UNKNOWN": 0.3,
    }

    # CVSS vector components that increase exploit likelihood
    EXPLOIT_INDICATORS = [
        "AV:N",   # Network attack vector
        "AC:L",   # Low attack complexity
        "PR:N",   # No privileges required
        "UI:N",   # No user interaction
    ]

    def calculate_threat_score(
        self,
        vulnerability: Vulnerability,
    ) -> tuple[float, dict[str, float]]:
        """
        Calculate threat score for a vulnerability.

        Args:
            vulnerability: Vulnerability to score

        Returns:
            Tuple of (score, factors)
        """
        factors = ThreatFactors(
            cvss_score=self._normalize_cvss(vulnerability.cvss_score),
            severity_weight=self._get_severity_weight(vulnerability.severity),
            exploit_likelihood=self._calculate_exploit_likelihood(vulnerability),
            age_factor=self._calculate_age_factor(vulnerability.published_date),
            affected_scope=self._calculate_affected_scope(vulnerability),
        )
        
        # Weighted combination of factors
        weights = {
            "cvss_score": 0.35,
            "severity_weight": 0.20,
            "exploit_likelihood": 0.25,
            "age_factor": 0.10,
            "affected_scope": 0.10,
        }
        
        score = (
            factors.cvss_score * weights["cvss_score"] +
            factors.severity_weight * weights["severity_weight"] +
            factors.exploit_likelihood * weights["exploit_likelihood"] +
            factors.age_factor * weights["age_factor"] +
            factors.affected_scope * weights["affected_scope"]
        ) * 100
        
        # Clamp to 0-100
        score = max(0, min(100, score))
        
        logger.debug(f"Calculated threat score for {vulnerability.cve_id}: {score:.2f}")
        
        return round(score, 2), factors.to_dict()

    def _normalize_cvss(self, cvss_score: Optional[float]) -> float:
        """Normalize CVSS score to 0-1 range."""
        if cvss_score is None:
            return 0.5  # Default for unknown
        return float(cvss_score) / 10.0

    def _get_severity_weight(self, severity: str) -> float:
        """Get weight for severity level."""
        return self.SEVERITY_WEIGHTS.get(severity.upper(), 0.3)

    def _calculate_exploit_likelihood(self, vulnerability: Vulnerability) -> float:
        """
        Calculate likelihood of exploitation based on CVSS vector.
        
        Higher scores indicate easier exploitation.
        """
        cvss_vector = vulnerability.cvss_vector or ""
        
        # Count exploit indicators present
        indicator_count = sum(
            1 for indicator in self.EXPLOIT_INDICATORS
            if indicator in cvss_vector
        )
        
        # Normalize to 0-1
        return indicator_count / len(self.EXPLOIT_INDICATORS)

    def _calculate_age_factor(self, published_date: Optional[datetime]) -> float:
        """
        Calculate age factor - newer vulnerabilities get higher scores.
        
        Returns higher values for more recent vulnerabilities.
        """
        if not published_date:
            return 0.5  # Default for unknown age
        
        now = datetime.utcnow()
        if published_date.tzinfo:
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        
        age_days = (now - published_date).days
        
        # Newer vulnerabilities (< 30 days) get higher scores
        if age_days < 30:
            return 1.0
        elif age_days < 90:
            return 0.8
        elif age_days < 180:
            return 0.6
        elif age_days < 365:
            return 0.4
        else:
            return 0.2

    def _calculate_affected_scope(self, vulnerability: Vulnerability) -> float:
        """
        Calculate affected scope based on number of affected packages.
        
        More affected packages = higher threat.
        """
        affected = vulnerability.affected_packages or []
        count = len(affected)
        
        # Use logarithmic scale
        if count == 0:
            return 0.2
        elif count <= 5:
            return 0.4
        elif count <= 20:
            return 0.6
        elif count <= 50:
            return 0.8
        else:
            return 1.0

    def batch_calculate(
        self,
        vulnerabilities: list[Vulnerability],
    ) -> list[tuple[str, float]]:
        """Calculate threat scores for multiple vulnerabilities."""
        results = []
        
        for vuln in vulnerabilities:
            score, _ = self.calculate_threat_score(vuln)
            results.append((vuln.cve_id, score))
        
        return sorted(results, key=lambda x: x[1], reverse=True)

    def get_high_threat_vulnerabilities(
        self,
        threshold: float = 70.0,
    ) -> list[Vulnerability]:
        """Get vulnerabilities with threat scores above threshold."""
        return Vulnerability.query.filter(
            Vulnerability.threat_score >= threshold
        ).order_by(
            Vulnerability.threat_score.desc()
        ).all()
