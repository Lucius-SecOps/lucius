# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-01-15

### Added

#### Multi-Tenant Support
- Added `tenant_id` column to `scan_results`, `notifications`, and `grants` tables
- Created `tenants` table for tenant management
- Implemented row-level security (RLS) policies (prepared, not enabled)
- Added composite indexes for tenant-scoped queries

#### Repository Pattern Implementation
- **VulnerabilityRepository**: Complete CRUD operations for vulnerability records
  - `find_by_cve_id()`: Lookup by CVE identifier with normalization
  - `find_by_severity()`: Filter by severity level (CRITICAL, HIGH, MEDIUM, LOW)
  - `find_by_min_cvss()`: Filter by minimum CVSS score
  - `find_by_package()`: Search vulnerabilities affecting specific packages
  - `find_recent()`: Get vulnerabilities published within N days
  - `find_modified_since()`: Incremental sync support
  - `search()`: Full-text search with multiple filters
  - `upsert()`: Idempotent create/update by CVE ID
  - `bulk_upsert()`: Batch operations for bulk imports
  - `get_statistics()`: Aggregate statistics and counts
  - `update_threat_score()`: Update ML-based threat scores

- **ScanRepository**: Complete CRUD operations for scan results
  - `find_by_project()`: Get scans for a specific project
  - `find_by_status()`: Filter by scan status
  - `find_recent()`: Get recent scans within time window
  - `find_with_critical_vulns()`: Find scans with critical vulnerabilities
  - `update_status()`: Manage scan lifecycle
  - `add_vulnerability_to_scan()`: Associate vulnerabilities with scans
  - `get_vulnerability_details_for_scan()`: Get detailed vuln info
  - `get_project_statistics()`: Per-project aggregations
  - `cleanup_old_scans()`: Automated scan retention management

- **BaseRepository**: Abstract base class with common functionality
  - Tenant isolation via `_apply_tenant_filter()`
  - Audit logging for all operations
  - Pagination with safety limits
  - Transaction management helpers

#### Pydantic Validation Schemas
- `VulnerabilityCreate`: Input validation for new vulnerabilities
- `VulnerabilityUpdate`: Partial update validation
- `VulnerabilityResponse`: API response serialization
- `VulnerabilitySearchQuery`: Search parameter validation
- `ScanResultCreate`: Scan submission validation
- `ScanResultResponse`: Scan response serialization
- `SeverityLevel` and `ScanStatus` enums
- `APIResponse`, `ErrorResponse`, `PaginatedResponse` schemas

#### GitHub Actions Workflows
- **security.yml**: Comprehensive security scanning
  - Dependency vulnerability scanning (pip-audit, Safety)
  - Static code analysis (Bandit, Semgrep)
  - Secrets detection (Gitleaks, TruffleHog)
  - Container image scanning (Trivy)
  - Sentinel self-scan for SBOM generation
  
- **license-guard.yml**: License compliance verification
  - Apache-2.0 license file validation
  - Dependency license compatibility checking
  - Source file license header verification

#### Database Enhancements
- Migration script `002_add_tenant_support.sql`
- `upsert_vulnerability()` PostgreSQL function for efficient bulk imports
- `vulnerability_stats` view for dashboard queries
- Optimized indexes for common query patterns

### Changed
- Updated `ScanResult` model with `tenant_id` field
- Updated `Notification` model with `tenant_id` field
- Enhanced `.env.example` with new configuration options
- Updated README.md with repository pattern documentation

### Security
- Input validation via Pydantic schemas prevents injection attacks
- Parameterized queries throughout repository layer
- Tenant isolation prevents cross-tenant data access
- Audit logging for compliance and forensics

### Documentation
- Added multi-tenancy usage examples
- Added repository pattern code samples
- Updated project structure diagram
- Added environment variable documentation

## [1.0.0] - 2025-12-01

### Added
- Initial release of Lucius Operations Platform
- Sentinel vulnerability scanner with NVD integration
- Talon threat intelligence API
- Operations grant management module
- Docker Compose deployment configuration
- CI/CD pipelines for testing and deployment
