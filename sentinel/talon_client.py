"""Talon API client for posting scan results."""

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from sentinel.config import config
from shared.logging import get_logger

logger = get_logger(__name__)


class TalonClient:
    """Client for communicating with the Talon API."""

    def __init__(self) -> None:
        self.config = config.talon
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "TalonClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.config.api_url,
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
            "Content-Type": "application/json",
            "User-Agent": "Sentinel-Scanner/1.0",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def post_scan_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Post scan results to the Talon API.

        Args:
            result: Scan result dictionary

        Returns:
            API response
        """
        async with httpx.AsyncClient(
            base_url=self.config.api_url,
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._get_headers(),
        ) as client:
            logger.info(f"Posting scan results to Talon API: {self.config.api_url}")

            try:
                response = await client.post("/api/v1/scans", json=result)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Successfully posted scan results, ID: {data.get('id')}")
                return data

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error posting to Talon: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Error posting to Talon: {e}")
                raise

    async def get_scan(self, scan_id: str) -> dict[str, Any] | None:
        """
        Get scan details from Talon.

        Args:
            scan_id: Scan UUID

        Returns:
            Scan details or None
        """
        async with httpx.AsyncClient(
            base_url=self.config.api_url,
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._get_headers(),
        ) as client:
            try:
                response = await client.get(f"/api/v1/scans/{scan_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise

    async def get_vulnerability(self, cve_id: str) -> dict[str, Any] | None:
        """
        Get vulnerability details from Talon.

        Args:
            cve_id: CVE identifier

        Returns:
            Vulnerability details or None
        """
        async with httpx.AsyncClient(
            base_url=self.config.api_url,
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._get_headers(),
        ) as client:
            try:
                response = await client.get(f"/api/v1/vulnerabilities/{cve_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise

    async def health_check(self) -> bool:
        """Check if Talon API is healthy."""
        async with httpx.AsyncClient(
            base_url=self.config.api_url,
            timeout=httpx.Timeout(5),
        ) as client:
            try:
                response = await client.get("/health")
                return response.status_code == 200
            except Exception:
                return False
