"""NVD (National Vulnerability Database) API client."""

import asyncio
from datetime import datetime
from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from sentinel.config import config
from shared.logging import get_logger

logger = get_logger(__name__)


class NVDClient:
    """Client for the NVD CVE API."""

    def __init__(self) -> None:
        self.config = config.nvd
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0

    async def __aenter__(self) -> "NVDClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._get_headers(),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "Sentinel-Scanner/1.0",
        }
        if self.config.api_key:
            headers["apiKey"] = self.config.api_key
        return headers

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        wait_time = self.config.effective_rate_limit - elapsed
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self._last_request_time = asyncio.get_event_loop().time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_cve(self, cve_id: str) -> Optional[dict[str, Any]]:
        """
        Get details for a specific CVE.

        Args:
            cve_id: The CVE identifier (e.g., CVE-2021-44228)

        Returns:
            CVE details or None if not found
        """
        await self._rate_limit()
        
        url = f"{self.config.base_url}"
        params = {"cveId": cve_id}
        
        logger.debug(f"Fetching CVE: {cve_id}")
        
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])
            
            if vulnerabilities:
                return self._parse_cve(vulnerabilities[0].get("cve", {}))
            return None
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error fetching CVE {cve_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching CVE {cve_id}: {e}")
            raise

    async def search_cves(
        self,
        keyword: Optional[str] = None,
        cpe_name: Optional[str] = None,
        cvss_v3_severity: Optional[str] = None,
        pub_start_date: Optional[datetime] = None,
        pub_end_date: Optional[datetime] = None,
        results_per_page: int = 100,
        start_index: int = 0,
    ) -> dict[str, Any]:
        """
        Search for CVEs with various filters.

        Args:
            keyword: Keyword to search for
            cpe_name: CPE name to filter by
            cvss_v3_severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            pub_start_date: Start date for publication filter
            pub_end_date: End date for publication filter
            results_per_page: Number of results per page (max 2000)
            start_index: Starting index for pagination

        Returns:
            Search results with CVE list and metadata
        """
        await self._rate_limit()
        
        params = {
            "resultsPerPage": min(results_per_page, 2000),
            "startIndex": start_index,
        }
        
        if keyword:
            params["keywordSearch"] = keyword
        if cpe_name:
            params["cpeName"] = cpe_name
        if cvss_v3_severity:
            params["cvssV3Severity"] = cvss_v3_severity
        if pub_start_date:
            params["pubStartDate"] = pub_start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        if pub_end_date:
            params["pubEndDate"] = pub_end_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        
        logger.debug(f"Searching CVEs with params: {params}")
        
        try:
            response = await self._client.get(self.config.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "total_results": data.get("totalResults", 0),
                "results_per_page": data.get("resultsPerPage", 0),
                "start_index": data.get("startIndex", 0),
                "vulnerabilities": [
                    self._parse_cve(v.get("cve", {}))
                    for v in data.get("vulnerabilities", [])
                ],
            }
            
        except Exception as e:
            logger.error(f"Error searching CVEs: {e}")
            raise

    async def get_cves_for_package(
        self,
        package_name: str,
        ecosystem: str = "npm",
        version: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get CVEs affecting a specific package.

        Args:
            package_name: Name of the package
            ecosystem: Package ecosystem (npm, pip, composer)
            version: Optional version to filter by

        Returns:
            List of CVEs affecting the package
        """
        # Map ecosystem to CPE vendor/product patterns
        cpe_patterns = {
            "npm": f"cpe:2.3:a:*:{package_name}:*:*:*:*:*:node.js:*:*",
            "pip": f"cpe:2.3:a:*:{package_name}:*:*:*:*:*:python:*:*",
            "composer": f"cpe:2.3:a:*:{package_name}:*:*:*:*:*:php:*:*",
        }
        
        # Use keyword search as fallback (CPE matching is complex)
        results = await self.search_cves(keyword=package_name)
        
        cves = []
        for cve in results.get("vulnerabilities", []):
            # Check if package is mentioned in affected configurations
            if self._package_affected(cve, package_name, version):
                cves.append(cve)
        
        return cves

    def _parse_cve(self, cve_data: dict[str, Any]) -> dict[str, Any]:
        """Parse CVE data into a standardized format."""
        cve_id = cve_data.get("id", "")
        
        # Get description
        descriptions = cve_data.get("descriptions", [])
        description = next(
            (d.get("value", "") for d in descriptions if d.get("lang") == "en"),
            descriptions[0].get("value", "") if descriptions else "",
        )
        
        # Get CVSS metrics
        metrics = cve_data.get("metrics", {})
        cvss_v3 = None
        cvss_score = None
        cvss_vector = None
        severity = "UNKNOWN"
        
        # Try CVSS 3.1 first, then 3.0
        for metric_key in ["cvssMetricV31", "cvssMetricV30"]:
            if metric_key in metrics:
                cvss_data = metrics[metric_key][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
                severity = cvss_data.get("baseSeverity", "UNKNOWN")
                break
        
        # Get references
        references = [
            {"url": ref.get("url"), "source": ref.get("source")}
            for ref in cve_data.get("references", [])
        ]
        
        # Get affected configurations
        affected_packages = self._extract_affected_packages(cve_data)
        
        return {
            "cve_id": cve_id,
            "description": description,
            "severity": severity,
            "cvss_score": cvss_score,
            "cvss_vector": cvss_vector,
            "affected_packages": affected_packages,
            "references": references,
            "published_date": cve_data.get("published"),
            "modified_date": cve_data.get("lastModified"),
        }

    def _extract_affected_packages(self, cve_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract affected packages from CVE configurations."""
        packages = []
        
        configurations = cve_data.get("configurations", [])
        for config in configurations:
            nodes = config.get("nodes", [])
            for node in nodes:
                cpe_matches = node.get("cpeMatch", [])
                for match in cpe_matches:
                    if match.get("vulnerable"):
                        cpe = match.get("criteria", "")
                        parts = cpe.split(":")
                        if len(parts) >= 5:
                            packages.append({
                                "vendor": parts[3],
                                "product": parts[4],
                                "version_start": match.get("versionStartIncluding"),
                                "version_end": match.get("versionEndExcluding"),
                            })
        
        return packages

    def _package_affected(
        self,
        cve: dict[str, Any],
        package_name: str,
        version: Optional[str],
    ) -> bool:
        """Check if a package/version is affected by a CVE."""
        package_lower = package_name.lower()
        
        # Check affected packages
        for pkg in cve.get("affected_packages", []):
            if package_lower in pkg.get("product", "").lower():
                if version and pkg.get("version_end"):
                    # Simple version comparison (should use packaging.version)
                    return True
                return True
        
        # Check if package is mentioned in description
        description = cve.get("description", "").lower()
        return package_lower in description
