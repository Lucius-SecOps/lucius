"""Dependency parsers for different package managers."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import toml

from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Dependency:
    """Represents a project dependency."""

    name: str
    version: str
    ecosystem: str  # npm, pip, composer
    is_dev: bool = False
    is_direct: bool = True
    source: str | None = None
    dependencies: list["Dependency"] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "ecosystem": self.ecosystem,
            "is_dev": self.is_dev,
            "is_direct": self.is_direct,
            "source": self.source,
        }


class BaseParser(ABC):
    """Abstract base class for dependency parsers."""

    ecosystem: str = ""

    def __init__(self, project_path: Path) -> None:
        self.project_path = project_path

    @abstractmethod
    async def parse(self, include_dev: bool = False) -> list[Dependency]:
        """Parse dependencies from the project."""
        pass

    @abstractmethod
    def can_parse(self) -> bool:
        """Check if this parser can handle the project."""
        pass


class NPMParser(BaseParser):
    """Parser for npm/Node.js projects."""

    ecosystem = "npm"

    def can_parse(self) -> bool:
        """Check for package.json or package-lock.json."""
        return (self.project_path / "package.json").exists() or (
            self.project_path / "package-lock.json"
        ).exists()

    async def parse(self, include_dev: bool = False) -> list[Dependency]:
        """Parse npm dependencies."""
        dependencies = []

        # Try package-lock.json first for accurate versions
        lock_file = self.project_path / "package-lock.json"
        if lock_file.exists():
            dependencies = await self._parse_lock_file(lock_file, include_dev)
        else:
            # Fall back to package.json
            package_file = self.project_path / "package.json"
            if package_file.exists():
                dependencies = await self._parse_package_json(package_file, include_dev)

        logger.info(f"Parsed {len(dependencies)} npm dependencies")
        return dependencies

    async def _parse_lock_file(
        self,
        lock_file: Path,
        include_dev: bool,
    ) -> list[Dependency]:
        """Parse package-lock.json for dependencies."""
        dependencies = []

        content = json.loads(lock_file.read_text())
        packages = content.get("packages", {})

        # Get direct dependencies from package.json
        package_json = self.project_path / "package.json"
        direct_deps = set()
        direct_dev_deps = set()

        if package_json.exists():
            pkg_content = json.loads(package_json.read_text())
            direct_deps = set(pkg_content.get("dependencies", {}).keys())
            direct_dev_deps = set(pkg_content.get("devDependencies", {}).keys())

        for pkg_path, pkg_info in packages.items():
            if not pkg_path or pkg_path == "":
                continue

            # Extract package name from path
            name = pkg_path.replace("node_modules/", "")
            if "/" in name and not name.startswith("@"):
                continue  # Skip nested dependencies for now

            is_dev = pkg_info.get("dev", False)
            if is_dev and not include_dev:
                continue

            version = pkg_info.get("version", "")
            if not version:
                continue

            is_direct = name in direct_deps or name in direct_dev_deps

            dependencies.append(
                Dependency(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    is_dev=is_dev,
                    is_direct=is_direct,
                    source=str(lock_file),
                )
            )

        return dependencies

    async def _parse_package_json(
        self,
        package_file: Path,
        include_dev: bool,
    ) -> list[Dependency]:
        """Parse package.json for dependencies."""
        dependencies = []

        content = json.loads(package_file.read_text())

        # Production dependencies
        for name, version in content.get("dependencies", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._normalize_version(version),
                    ecosystem=self.ecosystem,
                    is_dev=False,
                    is_direct=True,
                    source=str(package_file),
                )
            )

        # Dev dependencies
        if include_dev:
            for name, version in content.get("devDependencies", {}).items():
                dependencies.append(
                    Dependency(
                        name=name,
                        version=self._normalize_version(version),
                        ecosystem=self.ecosystem,
                        is_dev=True,
                        is_direct=True,
                        source=str(package_file),
                    )
                )

        return dependencies

    def _normalize_version(self, version: str) -> str:
        """Normalize npm version specifier."""
        # Remove semver prefixes
        return version.lstrip("^~>=<")


class PipParser(BaseParser):
    """Parser for pip/Python projects."""

    ecosystem = "pip"

    def can_parse(self) -> bool:
        """Check for requirements.txt, Pipfile, or pyproject.toml."""
        return (
            (self.project_path / "requirements.txt").exists()
            or (self.project_path / "requirements-lock.txt").exists()
            or (self.project_path / "Pipfile.lock").exists()
            or (self.project_path / "pyproject.toml").exists()
            or (self.project_path / "poetry.lock").exists()
        )

    async def parse(self, include_dev: bool = False) -> list[Dependency]:
        """Parse Python dependencies."""
        dependencies = []

        # Try different sources in order of preference
        if (self.project_path / "poetry.lock").exists():
            dependencies = await self._parse_poetry_lock(include_dev)
        elif (self.project_path / "Pipfile.lock").exists():
            dependencies = await self._parse_pipfile_lock(include_dev)
        elif (self.project_path / "requirements-lock.txt").exists():
            dependencies = await self._parse_requirements(
                self.project_path / "requirements-lock.txt",
                is_dev=False,
            )
        elif (self.project_path / "requirements.txt").exists():
            dependencies = await self._parse_requirements(
                self.project_path / "requirements.txt",
                is_dev=False,
            )
            if include_dev and (self.project_path / "requirements-dev.txt").exists():
                dev_deps = await self._parse_requirements(
                    self.project_path / "requirements-dev.txt",
                    is_dev=True,
                )
                dependencies.extend(dev_deps)
        elif (self.project_path / "pyproject.toml").exists():
            dependencies = await self._parse_pyproject(include_dev)

        logger.info(f"Parsed {len(dependencies)} pip dependencies")
        return dependencies

    async def _parse_requirements(
        self,
        req_file: Path,
        is_dev: bool,
    ) -> list[Dependency]:
        """Parse requirements.txt file."""
        dependencies = []

        for line in req_file.read_text().splitlines():
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Parse package==version format
            name, version = self._parse_requirement_line(line)
            if name and version:
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem,
                        is_dev=is_dev,
                        is_direct=True,
                        source=str(req_file),
                    )
                )

        return dependencies

    def _parse_requirement_line(self, line: str) -> tuple[str | None, str | None]:
        """Parse a single requirements line."""
        # Remove extras
        if "[" in line:
            line = line[: line.index("[")]

        # Handle different operators
        for op in ["==", ">=", "<=", "~=", "!=", ">", "<"]:
            if op in line:
                parts = line.split(op)
                return parts[0].strip(), parts[1].strip().split(",")[0]

        # No version specified
        return line.strip(), "*"

    async def _parse_poetry_lock(self, include_dev: bool) -> list[Dependency]:
        """Parse poetry.lock file."""
        dependencies = []
        lock_file = self.project_path / "poetry.lock"

        content = toml.loads(lock_file.read_text())

        for package in content.get("package", []):
            is_dev = package.get("category", "main") == "dev"
            if is_dev and not include_dev:
                continue

            dependencies.append(
                Dependency(
                    name=package.get("name", ""),
                    version=package.get("version", ""),
                    ecosystem=self.ecosystem,
                    is_dev=is_dev,
                    is_direct=False,  # Can't determine from lock file alone
                    source=str(lock_file),
                )
            )

        return dependencies

    async def _parse_pipfile_lock(self, include_dev: bool) -> list[Dependency]:
        """Parse Pipfile.lock file."""
        dependencies = []
        lock_file = self.project_path / "Pipfile.lock"

        content = json.loads(lock_file.read_text())

        # Default packages
        for name, info in content.get("default", {}).items():
            version = info.get("version", "").removeprefix("==")
            dependencies.append(
                Dependency(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    is_dev=False,
                    is_direct=True,
                    source=str(lock_file),
                )
            )

        # Dev packages
        if include_dev:
            for name, info in content.get("develop", {}).items():
                version = info.get("version", "").removeprefix("==")
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem,
                        is_dev=True,
                        is_direct=True,
                        source=str(lock_file),
                    )
                )

        return dependencies

    async def _parse_pyproject(self, include_dev: bool) -> list[Dependency]:
        """Parse pyproject.toml file."""
        dependencies = []
        pyproject_file = self.project_path / "pyproject.toml"

        content = toml.loads(pyproject_file.read_text())

        # PEP 621 dependencies
        project = content.get("project", {})
        for dep in project.get("dependencies", []):
            name, version = self._parse_requirement_line(dep)
            if name:
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version or "*",
                        ecosystem=self.ecosystem,
                        is_dev=False,
                        is_direct=True,
                        source=str(pyproject_file),
                    )
                )

        # Optional dependencies (often includes dev deps)
        if include_dev:
            optional = project.get("optional-dependencies", {})
            for _group, deps in optional.items():
                for dep in deps:
                    name, version = self._parse_requirement_line(dep)
                    if name:
                        dependencies.append(
                            Dependency(
                                name=name,
                                version=version or "*",
                                ecosystem=self.ecosystem,
                                is_dev=True,
                                is_direct=True,
                                source=str(pyproject_file),
                            )
                        )

        # Poetry dependencies
        poetry = content.get("tool", {}).get("poetry", {})
        for name, info in poetry.get("dependencies", {}).items():
            if name == "python":
                continue
            version = info if isinstance(info, str) else info.get("version", "*")
            dependencies.append(
                Dependency(
                    name=name,
                    version=version.lstrip("^~"),
                    ecosystem=self.ecosystem,
                    is_dev=False,
                    is_direct=True,
                    source=str(pyproject_file),
                )
            )

        if include_dev:
            for name, info in poetry.get("dev-dependencies", {}).items():
                version = info if isinstance(info, str) else info.get("version", "*")
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version.lstrip("^~"),
                        ecosystem=self.ecosystem,
                        is_dev=True,
                        is_direct=True,
                        source=str(pyproject_file),
                    )
                )

        return dependencies


class ComposerParser(BaseParser):
    """Parser for Composer/PHP projects."""

    ecosystem = "composer"

    def can_parse(self) -> bool:
        """Check for composer.json or composer.lock."""
        return (self.project_path / "composer.json").exists() or (
            self.project_path / "composer.lock"
        ).exists()

    async def parse(self, include_dev: bool = False) -> list[Dependency]:
        """Parse Composer dependencies."""
        dependencies = []

        # Try composer.lock first
        lock_file = self.project_path / "composer.lock"
        if lock_file.exists():
            dependencies = await self._parse_lock_file(lock_file, include_dev)
        else:
            # Fall back to composer.json
            composer_file = self.project_path / "composer.json"
            if composer_file.exists():
                dependencies = await self._parse_composer_json(composer_file, include_dev)

        logger.info(f"Parsed {len(dependencies)} composer dependencies")
        return dependencies

    async def _parse_lock_file(
        self,
        lock_file: Path,
        include_dev: bool,
    ) -> list[Dependency]:
        """Parse composer.lock file."""
        dependencies = []

        content = json.loads(lock_file.read_text())

        # Production packages
        for package in content.get("packages", []):
            dependencies.append(
                Dependency(
                    name=package.get("name", ""),
                    version=package.get("version", "").lstrip("v"),
                    ecosystem=self.ecosystem,
                    is_dev=False,
                    is_direct=True,
                    source=str(lock_file),
                )
            )

        # Dev packages
        if include_dev:
            for package in content.get("packages-dev", []):
                dependencies.append(
                    Dependency(
                        name=package.get("name", ""),
                        version=package.get("version", "").lstrip("v"),
                        ecosystem=self.ecosystem,
                        is_dev=True,
                        is_direct=True,
                        source=str(lock_file),
                    )
                )

        return dependencies

    async def _parse_composer_json(
        self,
        composer_file: Path,
        include_dev: bool,
    ) -> list[Dependency]:
        """Parse composer.json file."""
        dependencies = []

        content = json.loads(composer_file.read_text())

        # Production dependencies
        for name, version in content.get("require", {}).items():
            if name.startswith("php") or name.startswith("ext-"):
                continue
            dependencies.append(
                Dependency(
                    name=name,
                    version=version.lstrip("^~>=<"),
                    ecosystem=self.ecosystem,
                    is_dev=False,
                    is_direct=True,
                    source=str(composer_file),
                )
            )

        # Dev dependencies
        if include_dev:
            for name, version in content.get("require-dev", {}).items():
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version.lstrip("^~>=<"),
                        ecosystem=self.ecosystem,
                        is_dev=True,
                        is_direct=True,
                        source=str(composer_file),
                    )
                )

        return dependencies


class ParserFactory:
    """Factory for creating dependency parsers."""

    _parsers = [NPMParser, PipParser, ComposerParser]

    @classmethod
    def create(cls, package_manager: str, project_path: Path) -> BaseParser:
        """
        Create a parser for the given package manager.

        Args:
            package_manager: Package manager type or 'auto'
            project_path: Path to the project

        Returns:
            Appropriate parser instance

        Raises:
            ValueError: If no suitable parser found
        """
        if package_manager == "auto":
            return cls._auto_detect(project_path)

        parser_map = {
            "npm": NPMParser,
            "pip": PipParser,
            "composer": ComposerParser,
        }

        parser_class = parser_map.get(package_manager)
        if not parser_class:
            raise ValueError(f"Unknown package manager: {package_manager}")

        return parser_class(project_path)

    @classmethod
    def _auto_detect(cls, project_path: Path) -> BaseParser:
        """Auto-detect the package manager from project files."""
        for parser_class in cls._parsers:
            parser = parser_class(project_path)
            if parser.can_parse():
                logger.info(f"Auto-detected parser: {parser_class.__name__}")
                return parser

        raise ValueError(
            f"Could not auto-detect package manager for {project_path}. "
            "Please specify --package-manager explicitly."
        )
