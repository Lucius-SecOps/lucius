"""
Shared type definitions for Lucius platform.

This module defines all data structures used across components:
- Vulnerability reports from Sentinel
- Grant records from Operations
- Alert notifications to Talon
- API request/response schemas

All classes use dataclasses for immutability and type safety.
All dates use ISO 8601 format.
All IDs use UUIDv4.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from uuid import UUID, uuid4


class Severity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ScanStatus(str, Enum):
    """Scan result status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GrantStatus(str, Enum):
    """Grant pipeline status."""
    PROSPECTING = "prospecting"
    RESEARCHING = "researching"
    DRAFTING = "drafting"
    INTERNAL_REVIEW = "internal_review"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AWARDED = "awarded"
    REJECTED = "rejected"
    CLOSED = "closed"


class Priority(str, Enum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    SMS = "sms"
    EMAIL = "email"
    SLACK = "slack"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass(frozen=True)
class Dependency:
    """Represents a software dependency."""
    name: str
    version: str
    ecosystem: str  # npm, pip, composer
    is_dev: bool = False
    is_direct: bool = True
    source: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "ecosystem": self.ecosystem,
            "is_dev": self.is_dev,
            "is_direct": self.is_direct,
            "source": self.source,
        }


@dataclass(frozen=True)
class VulnerabilityReference:
    """Reference link for a vulnerability."""
    url: str
    source: Optional[str] = None


@dataclass
class Vulnerability:
    """Represents a security vulnerability (CVE)."""
    cve_id: str
    severity: Severity
    description: str = ""
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    affected_packages: List[Dict] = field(default_factory=list)
    references: List[VulnerabilityReference] = field(default_factory=list)
    published_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    threat_score: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "cve_id": self.cve_id,
            "severity": self.severity.value,
            "description": self.description,
            "cvss_score": self.cvss_score,
            "cvss_vector": self.cvss_vector,
            "affected_packages": self.affected_packages,
            "references": [{"url": r.url, "source": r.source} for r in self.references],
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "modified_date": self.modified_date.isoformat() if self.modified_date else None,
            "threat_score": self.threat_score,
        }


@dataclass
class ScanVulnerability:
    """Vulnerability instance found in a scan."""
    cve_id: str
    package_name: str
    installed_version: str
    severity: Severity
    cvss_score: Optional[float] = None
    description: Optional[str] = None
    fixed_version: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "cve_id": self.cve_id,
            "package_name": self.package_name,
            "installed_version": self.installed_version,
            "severity": self.severity.value,
            "cvss_score": self.cvss_score,
            "description": self.description,
            "fixed_version": self.fixed_version,
        }


@dataclass
class ScanResult:
    """Result of a vulnerability scan."""
    id: UUID = field(default_factory=uuid4)
    project_name: str = ""
    package_manager: str = ""
    scan_type: str = "dependency"
    status: ScanStatus = ScanStatus.PENDING
    total_dependencies: int = 0
    vulnerable_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    vulnerabilities: List[ScanVulnerability] = field(default_factory=list)
    scan_metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "project_name": self.project_name,
            "package_manager": self.package_manager,
            "scan_type": self.scan_type,
            "status": self.status.value,
            "total_dependencies": self.total_dependencies,
            "vulnerable_count": self.vulnerable_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "scan_metadata": self.scan_metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class Grant:
    """Represents a grant opportunity."""
    id: UUID = field(default_factory=uuid4)
    grant_name: str = ""
    funder: str = ""
    amount: Optional[float] = None
    currency: str = "USD"
    status: GrantStatus = GrantStatus.PROSPECTING
    priority: Priority = Priority.MEDIUM
    submission_deadline: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    description: Optional[str] = None
    requirements: Dict = field(default_factory=dict)
    contacts: List[Dict] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "grant_name": self.grant_name,
            "funder": self.funder,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "priority": self.priority.value,
            "submission_deadline": self.submission_deadline.isoformat() if self.submission_deadline else None,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "description": self.description,
            "requirements": self.requirements,
            "contacts": self.contacts,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }

    @property
    def days_until_deadline(self) -> Optional[int]:
        """Calculate days until submission deadline."""
        if not self.submission_deadline:
            return None
        delta = self.submission_deadline - datetime.utcnow()
        return delta.days


@dataclass
class Milestone:
    """Grant milestone for tracking progress."""
    id: UUID = field(default_factory=uuid4)
    grant_id: UUID = field(default_factory=uuid4)
    milestone_name: str = ""
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "pending"
    reminder_sent: bool = False
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "grant_id": str(self.grant_id),
            "milestone_name": self.milestone_name,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "reminder_sent": self.reminder_sent,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class Notification:
    """Notification to be sent through various channels."""
    id: UUID = field(default_factory=uuid4)
    notification_type: str = "alert"
    channel: NotificationChannel = NotificationChannel.SLACK
    recipient: str = ""
    subject: Optional[str] = None
    body: str = ""
    metadata: Dict = field(default_factory=dict)
    status: NotificationStatus = NotificationStatus.PENDING
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "notification_type": self.notification_type,
            "channel": self.channel.value,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "metadata": self.metadata,
            "status": self.status.value,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class NonprofitOrganization:
    """Nonprofit organization data record."""
    id: UUID = field(default_factory=uuid4)
    ein: Optional[str] = None
    organization_name: str = ""
    dba_name: Optional[str] = None
    address: Dict = field(default_factory=dict)
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    mission_statement: Optional[str] = None
    ntee_code: Optional[str] = None
    asset_amount: Optional[float] = None
    income_amount: Optional[float] = None
    is_verified: bool = False
    data_quality_score: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "ein": self.ein,
            "organization_name": self.organization_name,
            "dba_name": self.dba_name,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "mission_statement": self.mission_statement,
            "ntee_code": self.ntee_code,
            "asset_amount": self.asset_amount,
            "income_amount": self.income_amount,
            "is_verified": self.is_verified,
            "data_quality_score": self.data_quality_score,
        }


@dataclass
class APIResponse:
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[Dict] = None
    error: Optional[str] = None
    message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "message": self.message,
            "metadata": self.metadata,
        }


@dataclass
class PaginatedResponse:
    """Paginated API response."""
    items: List[Dict] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
    has_next: bool = False
    has_prev: bool = False

    def to_dict(self) -> Dict:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }
