-- Migration: Advanced Scanning Features
-- Description: Add tables and columns for advanced scanning capabilities
-- Author: Lucius Security Scanner
-- Date: 2026-01-17

-- ============================================================================
-- Web Application Scan Results
-- ============================================================================

CREATE TABLE IF NOT EXISTS web_scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100),
    target_url TEXT NOT NULL,
    scan_type VARCHAR(50),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    total_requests INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    info_count INTEGER DEFAULT 0,
    security_headers JSONB,
    ssl_info JSONB,
    cookies JSONB,
    external_scripts JSONB,
    forms JSONB,
    scan_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS web_vulnerabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES web_scan_results(id) ON DELETE CASCADE,
    vuln_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    affected_url TEXT,
    evidence TEXT,
    remediation TEXT,
    cwe_id VARCHAR(20),
    owasp_category VARCHAR(100),
    cvss_score DECIMAL(3,1),
    confidence VARCHAR(20),
    references JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_web_scan_results_tenant ON web_scan_results(tenant_id);
CREATE INDEX idx_web_scan_results_target ON web_scan_results(target_url);
CREATE INDEX idx_web_vulnerabilities_scan ON web_vulnerabilities(scan_id);
CREATE INDEX idx_web_vulnerabilities_severity ON web_vulnerabilities(severity);

-- ============================================================================
-- Container Scan Results
-- ============================================================================

CREATE TABLE IF NOT EXISTS container_scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100),
    image_name TEXT NOT NULL,
    image_tag VARCHAR(100),
    image_id VARCHAR(100),
    scan_time TIMESTAMP WITH TIME ZONE NOT NULL,
    os_type VARCHAR(50),
    os_version VARCHAR(100),
    total_size BIGINT,
    security_score DECIMAL(5,2),
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    layers JSONB,
    dockerfile_issues JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS container_vulnerabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES container_scan_results(id) ON DELETE CASCADE,
    vulnerability_id VARCHAR(50),
    package_name VARCHAR(255) NOT NULL,
    installed_version VARCHAR(100),
    fixed_version VARCHAR(100),
    severity VARCHAR(20) NOT NULL,
    layer_id VARCHAR(100),
    description TEXT,
    cvss_score DECIMAL(3,1),
    references JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_container_scan_results_tenant ON container_scan_results(tenant_id);
CREATE INDEX idx_container_scan_results_image ON container_scan_results(image_name, image_tag);
CREATE INDEX idx_container_vulnerabilities_scan ON container_vulnerabilities(scan_id);
CREATE INDEX idx_container_vulnerabilities_severity ON container_vulnerabilities(severity);

-- ============================================================================
-- Secrets Scan Results
-- ============================================================================

CREATE TABLE IF NOT EXISTS secrets_scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100),
    target_path TEXT NOT NULL,
    scan_type VARCHAR(50),
    scan_time TIMESTAMP WITH TIME ZONE NOT NULL,
    files_scanned INTEGER DEFAULT 0,
    commits_scanned INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS secret_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES secrets_scan_results(id) ON DELETE CASCADE,
    secret_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    matched_string TEXT,
    pattern_name VARCHAR(255),
    entropy DECIMAL(5,2),
    commit_hash VARCHAR(100),
    commit_author VARCHAR(255),
    commit_date TIMESTAMP WITH TIME ZONE,
    remediation TEXT,
    confidence VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_secrets_scan_results_tenant ON secrets_scan_results(tenant_id);
CREATE INDEX idx_secrets_scan_results_path ON secrets_scan_results(target_path);
CREATE INDEX idx_secret_findings_scan ON secret_findings(scan_id);
CREATE INDEX idx_secret_findings_severity ON secret_findings(severity);
CREATE INDEX idx_secret_findings_type ON secret_findings(secret_type);

-- ============================================================================
-- SAST Analysis Results
-- ============================================================================

CREATE TABLE IF NOT EXISTS sast_scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100),
    target_path TEXT NOT NULL,
    scan_time TIMESTAMP WITH TIME ZONE NOT NULL,
    files_analyzed INTEGER DEFAULT 0,
    lines_analyzed INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sast_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES sast_scan_results(id) ON DELETE CASCADE,
    vulnerability_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    column_number INTEGER,
    code_snippet TEXT,
    description TEXT,
    remediation TEXT,
    cwe_id VARCHAR(20),
    owasp_category VARCHAR(100),
    confidence VARCHAR(20),
    function_name VARCHAR(255),
    variable_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sast_scan_results_tenant ON sast_scan_results(tenant_id);
CREATE INDEX idx_sast_scan_results_path ON sast_scan_results(target_path);
CREATE INDEX idx_sast_findings_scan ON sast_findings(scan_id);
CREATE INDEX idx_sast_findings_severity ON sast_findings(severity);
CREATE INDEX idx_sast_findings_cwe ON sast_findings(cwe_id);

-- ============================================================================
-- IaC Scan Results
-- ============================================================================

CREATE TABLE IF NOT EXISTS iac_scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100),
    target_path TEXT NOT NULL,
    scan_time TIMESTAMP WITH TIME ZONE NOT NULL,
    files_scanned INTEGER DEFAULT 0,
    resources_analyzed INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS iac_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES iac_scan_results(id) ON DELETE CASCADE,
    resource_type VARCHAR(100) NOT NULL,
    resource_name VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    description TEXT,
    remediation TEXT,
    cis_control VARCHAR(50),
    compliance_frameworks JSONB,
    impact TEXT,
    risk_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_iac_scan_results_tenant ON iac_scan_results(tenant_id);
CREATE INDEX idx_iac_scan_results_path ON iac_scan_results(target_path);
CREATE INDEX idx_iac_findings_scan ON iac_findings(scan_id);
CREATE INDEX idx_iac_findings_severity ON iac_findings(severity);
CREATE INDEX idx_iac_findings_resource ON iac_findings(resource_type);

-- ============================================================================
-- Threat Intelligence
-- ============================================================================

CREATE TABLE IF NOT EXISTS threat_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cve_id VARCHAR(20) UNIQUE NOT NULL,
    nvd_data JSONB,
    exploits JSONB,
    known_exploited BOOLEAN DEFAULT FALSE,
    exploitation_status VARCHAR(50),
    mitre_techniques JSONB,
    threat_actors JSONB,
    malware_families JSONB,
    attack_patterns JSONB,
    epss_score DECIMAL(5,4),
    kev_date_added DATE,
    shodan_results JSONB,
    github_advisories JSONB,
    references JSONB,
    enrichment_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_threat_intelligence_cve ON threat_intelligence(cve_id);
CREATE INDEX idx_threat_intelligence_known_exploited ON threat_intelligence(known_exploited);
CREATE INDEX idx_threat_intelligence_epss ON threat_intelligence(epss_score);

-- ============================================================================
-- Exploit Predictions
-- ============================================================================

CREATE TABLE IF NOT EXISTS exploit_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cve_id VARCHAR(20) NOT NULL,
    exploit_probability DECIMAL(5,4),
    weaponization_days INTEGER,
    attack_complexity VARCHAR(20),
    required_privileges VARCHAR(20),
    user_interaction VARCHAR(20),
    network_accessibility VARCHAR(20),
    risk_score DECIMAL(5,2),
    contributing_factors JSONB,
    prediction_confidence DECIMAL(5,4),
    metadata JSONB,
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_exploit_predictions_cve ON exploit_predictions(cve_id);
CREATE INDEX idx_exploit_predictions_probability ON exploit_predictions(exploit_probability);
CREATE INDEX idx_exploit_predictions_risk ON exploit_predictions(risk_score);

-- ============================================================================
-- Remediation Plans
-- ============================================================================

CREATE TABLE IF NOT EXISTS remediation_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100),
    project_name VARCHAR(255) NOT NULL,
    scan_id VARCHAR(100),
    total_actions INTEGER DEFAULT 0,
    low_risk_count INTEGER DEFAULT 0,
    medium_risk_count INTEGER DEFAULT 0,
    high_risk_count INTEGER DEFAULT 0,
    applied_count INTEGER DEFAULT 0,
    auto_apply_enabled BOOLEAN DEFAULT FALSE,
    require_tests BOOLEAN DEFAULT TRUE,
    create_pr BOOLEAN DEFAULT TRUE,
    pr_url TEXT,
    branch_name VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS remediation_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES remediation_plans(id) ON DELETE CASCADE,
    vulnerability_id VARCHAR(100),
    action_type VARCHAR(50) NOT NULL,
    description TEXT,
    risk_level VARCHAR(20),
    status VARCHAR(20),
    package_name VARCHAR(255),
    current_version VARCHAR(100),
    target_version VARCHAR(100),
    file_path TEXT,
    changes JSONB,
    validation_results JSONB,
    metadata JSONB,
    applied_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_remediation_plans_tenant ON remediation_plans(tenant_id);
CREATE INDEX idx_remediation_plans_scan ON remediation_plans(scan_id);
CREATE INDEX idx_remediation_actions_plan ON remediation_actions(plan_id);
CREATE INDEX idx_remediation_actions_status ON remediation_actions(status);

-- ============================================================================
-- Reachability Analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS reachability_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100),
    scan_id VARCHAR(100),
    package_name VARCHAR(255) NOT NULL,
    is_reachable BOOLEAN DEFAULT TRUE,
    confidence VARCHAR(20),
    call_path JSONB,
    execution_probability DECIMAL(5,4),
    impact_radius INTEGER,
    direct_usage BOOLEAN,
    transitive_depth INTEGER,
    metadata JSONB,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reachability_analysis_tenant ON reachability_analysis(tenant_id);
CREATE INDEX idx_reachability_analysis_scan ON reachability_analysis(scan_id);
CREATE INDEX idx_reachability_analysis_package ON reachability_analysis(package_name);
CREATE INDEX idx_reachability_analysis_reachable ON reachability_analysis(is_reachable);

-- ============================================================================
-- Add columns to existing vulnerabilities table
-- ============================================================================

ALTER TABLE vulnerabilities
ADD COLUMN IF NOT EXISTS exploit_prediction_id UUID REFERENCES exploit_predictions(id),
ADD COLUMN IF NOT EXISTS threat_intel_id UUID REFERENCES threat_intelligence(id),
ADD COLUMN IF NOT EXISTS reachability_id UUID REFERENCES reachability_analysis(id);

CREATE INDEX IF NOT EXISTS idx_vulnerabilities_exploit_prediction ON vulnerabilities(exploit_prediction_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_threat_intel ON vulnerabilities(threat_intel_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_reachability ON vulnerabilities(reachability_id);
