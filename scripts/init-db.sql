-- Initialize Lucius Database Schema
-- This script runs automatically when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Vulnerabilities table (Talon)
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cve_id VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL,
    cvss_score DECIMAL(3, 1),
    cvss_vector VARCHAR(100),
    affected_packages JSONB DEFAULT '[]',
    references JSONB DEFAULT '[]',
    published_date TIMESTAMP WITH TIME ZONE,
    modified_date TIMESTAMP WITH TIME ZONE,
    threat_score DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scan results table (Talon)
CREATE TABLE IF NOT EXISTS scan_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_name VARCHAR(255) NOT NULL,
    scan_type VARCHAR(50) NOT NULL,
    package_manager VARCHAR(50) NOT NULL,
    total_dependencies INTEGER DEFAULT 0,
    vulnerable_count INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    sbom_path VARCHAR(500),
    scan_metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Scan vulnerabilities junction table
CREATE TABLE IF NOT EXISTS scan_vulnerabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scan_results(id) ON DELETE CASCADE,
    vulnerability_id UUID REFERENCES vulnerabilities(id) ON DELETE CASCADE,
    package_name VARCHAR(255) NOT NULL,
    installed_version VARCHAR(100),
    fixed_version VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scan_id, vulnerability_id, package_name)
);

-- Notifications table (Talon)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    body TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Grants table (Operations)
CREATE TABLE IF NOT EXISTS grants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grant_name VARCHAR(500) NOT NULL,
    funder VARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'prospecting',
    priority VARCHAR(20) DEFAULT 'medium',
    submission_deadline TIMESTAMP WITH TIME ZONE,
    decision_date TIMESTAMP WITH TIME ZONE,
    project_start_date DATE,
    project_end_date DATE,
    description TEXT,
    requirements JSONB DEFAULT '{}',
    contacts JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Grant milestones table (Operations)
CREATE TABLE IF NOT EXISTS grant_milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grant_id UUID REFERENCES grants(id) ON DELETE CASCADE,
    milestone_name VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    reminder_sent BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Nonprofit data table (Operations)
CREATE TABLE IF NOT EXISTS nonprofit_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ein VARCHAR(20) UNIQUE,
    organization_name VARCHAR(500) NOT NULL,
    dba_name VARCHAR(500),
    address JSONB DEFAULT '{}',
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),
    mission_statement TEXT,
    ntee_code VARCHAR(10),
    subsection_code VARCHAR(10),
    foundation_type VARCHAR(100),
    ruling_date DATE,
    asset_amount DECIMAL(15, 2),
    income_amount DECIMAL(15, 2),
    revenue_amount DECIMAL(15, 2),
    form_990_year INTEGER,
    is_verified BOOLEAN DEFAULT FALSE,
    data_quality_score DECIMAL(5, 2),
    raw_data JSONB DEFAULT '{}',
    cleaned_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_cve ON vulnerabilities(cve_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_severity ON vulnerabilities(severity);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_cvss ON vulnerabilities(cvss_score);
CREATE INDEX IF NOT EXISTS idx_scan_results_project ON scan_results(project_name);
CREATE INDEX IF NOT EXISTS idx_scan_results_status ON scan_results(status);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_grants_status ON grants(status);
CREATE INDEX IF NOT EXISTS idx_grants_deadline ON grants(submission_deadline);
CREATE INDEX IF NOT EXISTS idx_grant_milestones_due ON grant_milestones(due_date);
CREATE INDEX IF NOT EXISTS idx_nonprofit_ein ON nonprofit_data(ein);
CREATE INDEX IF NOT EXISTS idx_nonprofit_name ON nonprofit_data USING gin(organization_name gin_trgm_ops);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
DROP TRIGGER IF EXISTS update_vulnerabilities_updated_at ON vulnerabilities;
CREATE TRIGGER update_vulnerabilities_updated_at
    BEFORE UPDATE ON vulnerabilities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_grants_updated_at ON grants;
CREATE TRIGGER update_grants_updated_at
    BEFORE UPDATE ON grants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_nonprofit_updated_at ON nonprofit_data;
CREATE TRIGGER update_nonprofit_updated_at
    BEFORE UPDATE ON nonprofit_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
