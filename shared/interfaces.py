"""
Abstract base classes defining component interfaces.

These ABCs ensure consistent behavior across implementations:
- All scanners implement ScannerInterface
- All notification channels implement NotificationInterface
- All data processors implement ProcessorInterface
- All repositories implement RepositoryInterface
- All threat analyzers implement ThreatAnalyzerInterface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar, Optional
from uuid import UUID

from .types import (
    Vulnerability,
    ScanResult,
    Grant,
    Milestone,
    Notification,
    Dependency,
    NonprofitOrganization,
    Severity,
    NotificationChannel,
)

T = TypeVar("T")
ID = TypeVar("ID", str, UUID, int)


# =============================================================================
# Scanner Interfaces
# =============================================================================


class ScannerInterface(ABC):
    """Abstract base class for vulnerability scanners."""

    @abstractmethod
    def scan_project(self, project_path: Path) -> ScanResult:
        """
        Scan project and return vulnerabilities.

        Args:
            project_path: Path to the project directory

        Returns:
            ScanResult containing discovered vulnerabilities
        """
        pass

    @abstractmethod
    def generate_sbom(self, project_path: Path, format: str = "cyclonedx") -> dict[str, Any]:
        """
        Generate Software Bill of Materials.

        Args:
            project_path: Path to the project directory
            format: SBOM format (cyclonedx, spdx)

        Returns:
            SBOM document as dictionary
        """
        pass

    @abstractmethod
    def get_supported_ecosystems(self) -> list[str]:
        """
        Get list of supported package ecosystems.

        Returns:
            List of ecosystem names (npm, pypi, composer, etc.)
        """
        pass


class DependencyParserInterface(ABC):
    """Abstract base class for dependency file parsers."""

    @property
    @abstractmethod
    def ecosystem(self) -> str:
        """Return the package ecosystem name."""
        pass

    @property
    @abstractmethod
    def supported_files(self) -> list[str]:
        """Return list of supported manifest filenames."""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> list[Dependency]:
        """
        Parse dependency manifest file.

        Args:
            file_path: Path to the manifest file

        Returns:
            List of discovered dependencies
        """
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to check

        Returns:
            True if parser supports this file
        """
        pass


class VulnerabilityDatabaseInterface(ABC):
    """Abstract base class for vulnerability database clients."""

    @abstractmethod
    def search_by_package(
        self,
        package_name: str,
        ecosystem: str,
        version: Optional[str] = None,
    ) -> list[Vulnerability]:
        """
        Search vulnerabilities by package.

        Args:
            package_name: Name of the package
            ecosystem: Package ecosystem (npm, pypi, etc.)
            version: Optional specific version

        Returns:
            List of matching vulnerabilities
        """
        pass

    @abstractmethod
    def get_by_cve(self, cve_id: str) -> Optional[Vulnerability]:
        """
        Get vulnerability by CVE ID.

        Args:
            cve_id: CVE identifier (e.g., CVE-2023-12345)

        Returns:
            Vulnerability if found, None otherwise
        """
        pass

    @abstractmethod
    def search_by_severity(
        self,
        min_severity: Severity,
        limit: int = 100,
    ) -> list[Vulnerability]:
        """
        Search vulnerabilities by minimum severity.

        Args:
            min_severity: Minimum severity level
            limit: Maximum results to return

        Returns:
            List of vulnerabilities meeting criteria
        """
        pass


# =============================================================================
# Notification Interfaces
# =============================================================================


class NotificationInterface(ABC):
    """Abstract base class for notification channels."""

    @property
    @abstractmethod
    def channel(self) -> NotificationChannel:
        """Return the notification channel type."""
        pass

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """
        Send a notification.

        Args:
            notification: Notification to send

        Returns:
            True if sent successfully
        """
        pass

    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient address/number.

        Args:
            recipient: Recipient identifier

        Returns:
            True if valid
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if channel is properly configured and available.

        Returns:
            True if channel can send notifications
        """
        pass


class NotificationDispatcherInterface(ABC):
    """Abstract base class for notification routing."""

    @abstractmethod
    def dispatch(self, notification: Notification) -> bool:
        """
        Dispatch notification through appropriate channel.

        Args:
            notification: Notification to dispatch

        Returns:
            True if dispatched successfully
        """
        pass

    @abstractmethod
    def register_channel(self, channel: NotificationInterface) -> None:
        """
        Register a notification channel.

        Args:
            channel: Channel implementation to register
        """
        pass

    @abstractmethod
    def get_available_channels(self) -> list[NotificationChannel]:
        """
        Get list of available notification channels.

        Returns:
            List of configured channel types
        """
        pass


# =============================================================================
# Data Processing Interfaces
# =============================================================================


class ProcessorInterface(ABC):
    """Abstract base class for data processors."""

    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Process input data.

        Args:
            data: Input data to process

        Returns:
            Processed data
        """
        pass

    @abstractmethod
    def validate(self, data: Any) -> tuple[bool, list[str]]:
        """
        Validate input data.

        Args:
            data: Data to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        pass


class DataCleanerInterface(ABC):
    """Abstract base class for data cleaning services."""

    @abstractmethod
    def clean(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Clean and normalize data.

        Args:
            data: Raw data dictionary

        Returns:
            Cleaned data dictionary
        """
        pass

    @abstractmethod
    def calculate_quality_score(self, data: dict[str, Any]) -> float:
        """
        Calculate data quality score.

        Args:
            data: Data to score

        Returns:
            Quality score (0-100)
        """
        pass

    @abstractmethod
    def get_validation_errors(self, data: dict[str, Any]) -> list[str]:
        """
        Get list of validation errors in data.

        Args:
            data: Data to validate

        Returns:
            List of error messages
        """
        pass


# =============================================================================
# Repository Interfaces (Data Access Layer)
# =============================================================================


class RepositoryInterface(ABC, Generic[T, ID]):
    """Abstract base class for data repositories."""

    @abstractmethod
    def get_by_id(self, id: ID) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """
        Get all entities with pagination.

        Args:
            limit: Maximum results
            offset: Number of results to skip

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Create new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID
        """
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Update existing entity.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        pass

    @abstractmethod
    def delete(self, id: ID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity identifier

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    def exists(self, id: ID) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity identifier

        Returns:
            True if exists
        """
        pass


class VulnerabilityRepositoryInterface(RepositoryInterface[Vulnerability, str]):
    """Repository interface for vulnerabilities."""

    @abstractmethod
    def find_by_severity(self, severity: Severity) -> list[Vulnerability]:
        """Find vulnerabilities by severity level."""
        pass

    @abstractmethod
    def find_by_package(self, package_name: str) -> list[Vulnerability]:
        """Find vulnerabilities affecting a package."""
        pass

    @abstractmethod
    def find_unresolved(self) -> list[Vulnerability]:
        """Find all unresolved vulnerabilities."""
        pass


class GrantRepositoryInterface(RepositoryInterface[Grant, UUID]):
    """Repository interface for grants."""

    @abstractmethod
    def find_by_organization(self, org_name: str) -> list[Grant]:
        """Find grants by organization name."""
        pass

    @abstractmethod
    def find_by_status(self, status: str) -> list[Grant]:
        """Find grants by pipeline status."""
        pass

    @abstractmethod
    def find_approaching_deadline(self, days: int) -> list[Grant]:
        """Find grants with deadline within specified days."""
        pass


# =============================================================================
# Threat Analysis Interfaces
# =============================================================================


class ThreatAnalyzerInterface(ABC):
    """Abstract base class for threat analysis."""

    @abstractmethod
    def analyze(self, vulnerability: Vulnerability) -> dict[str, Any]:
        """
        Analyze threat posed by vulnerability.

        Args:
            vulnerability: Vulnerability to analyze

        Returns:
            Analysis results dictionary
        """
        pass

    @abstractmethod
    def calculate_risk_score(self, vulnerability: Vulnerability) -> float:
        """
        Calculate risk score for vulnerability.

        Args:
            vulnerability: Vulnerability to score

        Returns:
            Risk score (0.0-10.0)
        """
        pass

    @abstractmethod
    def get_remediation_priority(self, vulnerabilities: list[Vulnerability]) -> list[Vulnerability]:
        """
        Sort vulnerabilities by remediation priority.

        Args:
            vulnerabilities: List to prioritize

        Returns:
            Sorted list, highest priority first
        """
        pass


class ThreatScoringModelInterface(ABC):
    """Abstract base class for ML-based threat scoring."""

    @abstractmethod
    def train(self, training_data: list[dict[str, Any]]) -> None:
        """
        Train the scoring model.

        Args:
            training_data: Historical vulnerability data
        """
        pass

    @abstractmethod
    def predict(self, features: dict[str, Any]) -> float:
        """
        Predict threat score.

        Args:
            features: Feature dictionary

        Returns:
            Predicted score
        """
        pass

    @abstractmethod
    def get_feature_importance(self) -> dict[str, float]:
        """
        Get feature importance rankings.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        pass

    @abstractmethod
    def save_model(self, path: Path) -> None:
        """Save trained model to file."""
        pass

    @abstractmethod
    def load_model(self, path: Path) -> None:
        """Load trained model from file."""
        pass


# =============================================================================
# Service Interfaces
# =============================================================================


class GrantServiceInterface(ABC):
    """Abstract base class for grant management services."""

    @abstractmethod
    def create_grant(self, data: dict[str, Any]) -> Grant:
        """Create a new grant."""
        pass

    @abstractmethod
    def update_status(self, grant_id: UUID, status: str) -> Grant:
        """Update grant pipeline status."""
        pass

    @abstractmethod
    def add_milestone(self, grant_id: UUID, milestone: Milestone) -> Milestone:
        """Add milestone to grant."""
        pass

    @abstractmethod
    def complete_milestone(self, milestone_id: UUID) -> Milestone:
        """Mark milestone as complete."""
        pass

    @abstractmethod
    def get_upcoming_deadlines(self, days: int = 7) -> list[Grant]:
        """Get grants with upcoming deadlines."""
        pass


class ScanServiceInterface(ABC):
    """Abstract base class for scan orchestration services."""

    @abstractmethod
    def submit_scan(self, scan_data: dict[str, Any]) -> str:
        """Submit scan results for processing."""
        pass

    @abstractmethod
    def get_scan_status(self, scan_id: str) -> dict[str, Any]:
        """Get scan processing status."""
        pass

    @abstractmethod
    def get_scan_results(self, scan_id: str) -> ScanResult:
        """Get completed scan results."""
        pass

    @abstractmethod
    def aggregate_vulnerabilities(self, scan_ids: list[str]) -> list[Vulnerability]:
        """Aggregate vulnerabilities from multiple scans."""
        pass


# =============================================================================
# Event Interfaces (Observer Pattern)
# =============================================================================


class EventHandlerInterface(ABC):
    """Abstract base class for event handlers."""

    @abstractmethod
    def handle(self, event_type: str, payload: dict[str, Any]) -> None:
        """
        Handle an event.

        Args:
            event_type: Type of event
            payload: Event data
        """
        pass

    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """
        Check if handler can process event type.

        Args:
            event_type: Type to check

        Returns:
            True if handler supports this event type
        """
        pass


class EventEmitterInterface(ABC):
    """Abstract base class for event emitters."""

    @abstractmethod
    def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        """
        Emit an event.

        Args:
            event_type: Type of event
            payload: Event data
        """
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandlerInterface) -> None:
        """
        Subscribe handler to event type.

        Args:
            event_type: Event type to subscribe to
            handler: Handler to invoke
        """
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandlerInterface) -> None:
        """
        Unsubscribe handler from event type.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        pass
