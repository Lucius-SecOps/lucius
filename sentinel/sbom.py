"""SBOM (Software Bill of Materials) generator."""

import json
import uuid
from datetime import datetime
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


class SBOMGenerator:
    """Generate SBOM in various formats."""

    def generate(
        self,
        scan_result: dict[str, Any],
        format: str = "cyclonedx",
    ) -> str:
        """
        Generate SBOM from scan results.

        Args:
            scan_result: Scan results containing dependencies
            format: Output format (cyclonedx or spdx)

        Returns:
            SBOM as JSON string
        """
        if format == "cyclonedx":
            return self._generate_cyclonedx(scan_result)
        elif format == "spdx":
            return self._generate_spdx(scan_result)
        else:
            raise ValueError(f"Unknown SBOM format: {format}")

    def _generate_cyclonedx(self, scan_result: dict[str, Any]) -> str:
        """Generate CycloneDX format SBOM."""
        components = []
        
        for dep in scan_result.get("dependencies", []):
            component = {
                "type": "library",
                "name": dep.get("name", ""),
                "version": dep.get("version", ""),
                "purl": self._create_purl(dep),
            }
            
            # Add ecosystem-specific info
            ecosystem = dep.get("ecosystem", "")
            if ecosystem:
                component["properties"] = [
                    {"name": "ecosystem", "value": ecosystem}
                ]
            
            components.append(component)
        
        # Find vulnerabilities for components
        vulnerabilities = []
        for vuln in scan_result.get("vulnerabilities", []):
            vuln_entry = {
                "id": vuln.get("cve_id", ""),
                "source": {
                    "name": "NVD",
                    "url": f"https://nvd.nist.gov/vuln/detail/{vuln.get('cve_id', '')}",
                },
                "ratings": [],
                "description": vuln.get("description", ""),
                "affects": [
                    {
                        "ref": self._create_purl({
                            "name": vuln.get("package_name", ""),
                            "ecosystem": scan_result.get("package_manager", ""),
                            "version": vuln.get("installed_version", ""),
                        }),
                    }
                ],
            }
            
            if vuln.get("cvss_score"):
                vuln_entry["ratings"].append({
                    "source": {"name": "NVD"},
                    "score": vuln.get("cvss_score"),
                    "severity": vuln.get("severity", "").lower(),
                    "method": "CVSSv3",
                    "vector": vuln.get("cvss_vector", ""),
                })
            
            vulnerabilities.append(vuln_entry)
        
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tools": [
                    {
                        "vendor": "Lucius",
                        "name": "Sentinel",
                        "version": "1.0.0",
                    }
                ],
                "component": {
                    "type": "application",
                    "name": scan_result.get("project_name", "unknown"),
                    "version": "1.0.0",
                },
            },
            "components": components,
        }
        
        if vulnerabilities:
            sbom["vulnerabilities"] = vulnerabilities
        
        return json.dumps(sbom, indent=2)

    def _generate_spdx(self, scan_result: dict[str, Any]) -> str:
        """Generate SPDX format SBOM."""
        packages = []
        relationships = []
        
        document_namespace = f"https://lucius.io/spdx/{uuid.uuid4()}"
        document_spdx_id = "SPDXRef-DOCUMENT"
        root_package_id = "SPDXRef-RootPackage"
        
        # Root package
        packages.append({
            "SPDXID": root_package_id,
            "name": scan_result.get("project_name", "unknown"),
            "versionInfo": "1.0.0",
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
        })
        
        # Dependencies
        for i, dep in enumerate(scan_result.get("dependencies", [])):
            pkg_id = f"SPDXRef-Package-{i}"
            
            packages.append({
                "SPDXID": pkg_id,
                "name": dep.get("name", ""),
                "versionInfo": dep.get("version", ""),
                "downloadLocation": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": self._create_purl(dep),
                    }
                ],
                "filesAnalyzed": False,
            })
            
            relationships.append({
                "spdxElementId": root_package_id,
                "relatedSpdxElement": pkg_id,
                "relationshipType": "DEPENDS_ON",
            })
        
        # Document relationship
        relationships.append({
            "spdxElementId": document_spdx_id,
            "relatedSpdxElement": root_package_id,
            "relationshipType": "DESCRIBES",
        })
        
        sbom = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": document_spdx_id,
            "name": f"SBOM for {scan_result.get('project_name', 'unknown')}",
            "documentNamespace": document_namespace,
            "creationInfo": {
                "created": datetime.utcnow().isoformat() + "Z",
                "creators": ["Tool: Sentinel-1.0.0"],
            },
            "packages": packages,
            "relationships": relationships,
        }
        
        return json.dumps(sbom, indent=2)

    def _create_purl(self, dep: dict[str, Any]) -> str:
        """Create Package URL (purl) for a dependency."""
        ecosystem = dep.get("ecosystem", "").lower()
        name = dep.get("name", "")
        version = dep.get("version", "")
        
        purl_type_map = {
            "npm": "npm",
            "pip": "pypi",
            "composer": "composer",
        }
        
        purl_type = purl_type_map.get(ecosystem, "generic")
        
        # Handle scoped npm packages
        if purl_type == "npm" and name.startswith("@"):
            namespace, pkg_name = name.split("/", 1)
            return f"pkg:{purl_type}/{namespace}/{pkg_name}@{version}"
        
        # Handle composer packages (vendor/package)
        if purl_type == "composer" and "/" in name:
            namespace, pkg_name = name.split("/", 1)
            return f"pkg:{purl_type}/{namespace}/{pkg_name}@{version}"
        
        return f"pkg:{purl_type}/{name}@{version}"
