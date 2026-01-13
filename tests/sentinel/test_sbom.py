"""Tests for Sentinel SBOM generation."""

import json
import tempfile
from pathlib import Path

import pytest

from sentinel.parsers import Dependency
from sentinel.sbom import CycloneDXGenerator, SBOMGenerator, SPDXGenerator


class TestSBOMGenerator:
    """Tests for base SBOM generator."""

    @pytest.fixture
    def dependencies(self):
        """Sample dependencies."""
        return [
            Dependency(name="lodash", version="4.17.21", ecosystem="npm"),
            Dependency(name="express", version="4.18.2", ecosystem="npm"),
            Dependency(name="flask", version="2.3.0", ecosystem="pypi"),
        ]

    def test_get_cyclonedx_generator(self):
        """Test getting CycloneDX generator."""
        generator = SBOMGenerator.get_generator("cyclonedx")
        assert isinstance(generator, CycloneDXGenerator)

    def test_get_spdx_generator(self):
        """Test getting SPDX generator."""
        generator = SBOMGenerator.get_generator("spdx")
        assert isinstance(generator, SPDXGenerator)

    def test_unsupported_format(self):
        """Test unsupported format."""
        with pytest.raises(ValueError, match="Unsupported SBOM format"):
            SBOMGenerator.get_generator("unknown")


class TestCycloneDXGenerator:
    """Tests for CycloneDX generator."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return CycloneDXGenerator()

    @pytest.fixture
    def dependencies(self):
        """Sample dependencies."""
        return [
            Dependency(name="lodash", version="4.17.21", ecosystem="npm"),
            Dependency(name="flask", version="2.3.0", ecosystem="pypi"),
        ]

    def test_generate_sbom(self, generator, dependencies):
        """Test generating CycloneDX SBOM."""
        sbom = generator.generate(
            dependencies=dependencies, project_name="test-project", project_version="1.0.0"
        )

        assert sbom["bomFormat"] == "CycloneDX"
        assert sbom["specVersion"] == "1.5"
        assert len(sbom["components"]) == 2

    def test_component_format(self, generator, dependencies):
        """Test component format."""
        sbom = generator.generate(
            dependencies=dependencies, project_name="test", project_version="1.0.0"
        )

        lodash = next(c for c in sbom["components"] if c["name"] == "lodash")
        assert lodash["type"] == "library"
        assert lodash["version"] == "4.17.21"
        assert "purl" in lodash

    def test_save_to_file(self, generator, dependencies):
        """Test saving SBOM to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        generator.save(
            dependencies=dependencies,
            project_name="test",
            project_version="1.0.0",
            output_path=output_path,
        )

        with open(output_path) as f:
            saved = json.load(f)

        assert saved["bomFormat"] == "CycloneDX"


class TestSPDXGenerator:
    """Tests for SPDX generator."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return SPDXGenerator()

    @pytest.fixture
    def dependencies(self):
        """Sample dependencies."""
        return [
            Dependency(name="requests", version="2.28.0", ecosystem="pypi"),
        ]

    def test_generate_sbom(self, generator, dependencies):
        """Test generating SPDX SBOM."""
        sbom = generator.generate(
            dependencies=dependencies, project_name="test-project", project_version="1.0.0"
        )

        assert sbom["spdxVersion"] == "SPDX-2.3"
        assert "packages" in sbom

    def test_package_format(self, generator, dependencies):
        """Test package format."""
        sbom = generator.generate(
            dependencies=dependencies, project_name="test", project_version="1.0.0"
        )

        pkg = sbom["packages"][0]
        assert pkg["name"] == "requests"
        assert pkg["versionInfo"] == "2.28.0"
        assert "SPDXID" in pkg

    def test_save_to_file(self, generator, dependencies):
        """Test saving SBOM to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        generator.save(
            dependencies=dependencies,
            project_name="test",
            project_version="1.0.0",
            output_path=output_path,
        )

        with open(output_path) as f:
            saved = json.load(f)

        assert saved["spdxVersion"] == "SPDX-2.3"
