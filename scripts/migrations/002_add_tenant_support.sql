-- Migration: Add multi-tenant support and VulnerabilityRepository schema enhancements
-- Version: 002_add_tenant_support
-- Date: 2026-01-15
-- Description: Adds tenant_id columns, tenant table, and indexes for multi-tenant isolation

BEGIN;

-- =============================================================================
-- Create tenants table
-- =============================================================================

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tenants_tenant_id ON tenants(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenants_is_active ON tenants(is_active);

-- =============================================================================
-- Add tenant_id to scan_results
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'scan_results' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE scan_results ADD COLUMN tenant_id VARCHAR(100);
        
        -- Set default tenant for existing records
        UPDATE scan_results SET tenant_id = 'default' WHERE tenant_id IS NULL;
        
        -- Make column NOT NULL after backfill
        ALTER TABLE scan_results ALTER COLUMN tenant_id SET NOT NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_scan_results_tenant ON scan_results(tenant_id);
CREATE INDEX IF NOT EXISTS idx_scan_results_tenant_project ON scan_results(tenant_id, project_name);

-- =============================================================================
-- Add tenant_id to notifications
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notifications' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE notifications ADD COLUMN tenant_id VARCHAR(100);
        
        -- Set default tenant for existing records
        UPDATE notifications SET tenant_id = 'default' WHERE tenant_id IS NULL;
        
        -- Make column NOT NULL after backfill
        ALTER TABLE notifications ALTER COLUMN tenant_id SET NOT NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_notifications_tenant ON notifications(tenant_id);

-- =============================================================================
-- Add tenant_id to grants (Operations)
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'grants' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE grants ADD COLUMN tenant_id VARCHAR(100);
        
        -- Set default tenant for existing records
        UPDATE grants SET tenant_id = 'default' WHERE tenant_id IS NULL;
        
        -- Make column NOT NULL after backfill
        ALTER TABLE grants ALTER COLUMN tenant_id SET NOT NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_grants_tenant ON grants(tenant_id);

-- =============================================================================
-- Enhance vulnerability table indexes
-- =============================================================================

-- Index for package name searches within JSONB
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_affected_packages 
    ON vulnerabilities USING gin(affected_packages);

-- Index for recent vulnerabilities
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_published 
    ON vulnerabilities(published_date DESC NULLS LAST);

-- Index for threat scoring queue
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_unscored 
    ON vulnerabilities(published_date DESC) 
    WHERE threat_score IS NULL;

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_severity_cvss 
    ON vulnerabilities(severity, cvss_score DESC NULLS LAST);

-- =============================================================================
-- Add audit columns to tables if missing
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'scan_results' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE scan_results ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- =============================================================================
-- Create updated_at trigger for tenants
-- =============================================================================

DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Row Level Security (RLS) Policies
-- Note: These are prepared but not enabled - enable in production after testing
-- =============================================================================

-- Prepare RLS on scan_results
ALTER TABLE scan_results ENABLE ROW LEVEL SECURITY;

-- Policy for scan_results - users can only see their tenant's scans
-- DROP POLICY IF EXISTS tenant_isolation_scan_results ON scan_results;
-- CREATE POLICY tenant_isolation_scan_results ON scan_results
--     FOR ALL
--     USING (tenant_id = current_setting('app.current_tenant', true));

-- Prepare RLS on notifications
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Policy for notifications - users can only see their tenant's notifications
-- DROP POLICY IF EXISTS tenant_isolation_notifications ON notifications;
-- CREATE POLICY tenant_isolation_notifications ON notifications
--     FOR ALL
--     USING (tenant_id = current_setting('app.current_tenant', true));

-- =============================================================================
-- Insert default tenant if not exists
-- =============================================================================

INSERT INTO tenants (tenant_id, name, is_active, settings)
VALUES ('default', 'Default Tenant', TRUE, '{"tier": "free", "features": []}')
ON CONFLICT (tenant_id) DO NOTHING;

-- =============================================================================
-- Create view for vulnerability statistics
-- =============================================================================

CREATE OR REPLACE VIEW vulnerability_stats AS
SELECT 
    severity,
    COUNT(*) as count,
    AVG(cvss_score)::DECIMAL(3,1) as avg_cvss,
    MAX(cvss_score) as max_cvss,
    COUNT(*) FILTER (WHERE threat_score IS NOT NULL) as scored_count,
    COUNT(*) FILTER (WHERE published_date >= CURRENT_DATE - INTERVAL '30 days') as last_30_days,
    COUNT(*) FILTER (WHERE published_date >= CURRENT_DATE - INTERVAL '7 days') as last_7_days
FROM vulnerabilities
GROUP BY severity;

-- =============================================================================
-- Create function for bulk upsert of vulnerabilities
-- =============================================================================

CREATE OR REPLACE FUNCTION upsert_vulnerability(
    p_cve_id VARCHAR(20),
    p_description TEXT,
    p_severity VARCHAR(20),
    p_cvss_score DECIMAL(3,1),
    p_cvss_vector VARCHAR(100),
    p_affected_packages JSONB,
    p_references JSONB,
    p_published_date TIMESTAMP WITH TIME ZONE,
    p_modified_date TIMESTAMP WITH TIME ZONE
) RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO vulnerabilities (
        cve_id, description, severity, cvss_score, cvss_vector,
        affected_packages, references, published_date, modified_date
    ) VALUES (
        UPPER(TRIM(p_cve_id)), p_description, UPPER(p_severity), p_cvss_score,
        p_cvss_vector, COALESCE(p_affected_packages, '[]'::JSONB),
        COALESCE(p_references, '[]'::JSONB), p_published_date, p_modified_date
    )
    ON CONFLICT (cve_id) DO UPDATE SET
        description = EXCLUDED.description,
        severity = EXCLUDED.severity,
        cvss_score = EXCLUDED.cvss_score,
        cvss_vector = EXCLUDED.cvss_vector,
        affected_packages = EXCLUDED.affected_packages,
        references = EXCLUDED.references,
        modified_date = EXCLUDED.modified_date,
        updated_at = CURRENT_TIMESTAMP
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Grant permissions (adjust role names as needed)
-- =============================================================================

-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lucius_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lucius_app;
-- GRANT SELECT ON vulnerability_stats TO lucius_app;
-- GRANT EXECUTE ON FUNCTION upsert_vulnerability TO lucius_app;

COMMIT;

-- =============================================================================
-- Verification queries (run manually to verify migration)
-- =============================================================================

-- Check tenant_id columns exist:
-- SELECT table_name, column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE column_name = 'tenant_id' AND table_schema = 'public';

-- Check indexes created:
-- SELECT indexname, tablename FROM pg_indexes 
-- WHERE schemaname = 'public' AND indexname LIKE '%tenant%';

-- Check default tenant exists:
-- SELECT * FROM tenants WHERE tenant_id = 'default';
