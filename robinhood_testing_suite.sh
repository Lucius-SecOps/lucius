#!/bin/bash

################################################################################
# ETHICAL ROBINHOOD VULNERABILITY TESTING SUITE
# Lucius Integration Scripts
# 
# This script suite provides safe, ethical testing workflows for Robinhood
# bug bounty assessment. All testing is confined to YOUR OWN test accounts.
#
# Usage: source robinhood_testing_suite.sh
################################################################################

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"
PYTHON_BIN="$VENV_PATH/bin/python"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Results directory
RESULTS_DIR="$SCRIPT_DIR/assessments"
mkdir -p "$RESULTS_DIR"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# ============================================================================
# 1. INFRASTRUCTURE ASSESSMENT SCRIPTS
# ============================================================================

assess_infrastructure() {
    local target="$1"
    local h1_user="$2"
    local test_email="$3"
    
    log_header "PHASE 1: INFRASTRUCTURE ASSESSMENT"
    log_info "Target: $target"
    log_info "Test Account: $test_email"
    
    local report_file="$RESULTS_DIR/phase1_infrastructure_${TIMESTAMP}.json"
    
    log_info "Running subdomain enumeration..."
    $PYTHON_BIN "$SCRIPT_DIR/script.py" "$target" \
        --hackerone-username "$h1_user" \
        --test-account-email "$test_email" \
        --output "$report_file" \
        --verbose
    
    log_success "Infrastructure assessment complete"
    echo "Report: $report_file"
    
    # Parse results and check for anomalies
    check_infrastructure_anomalies "$report_file"
}

check_infrastructure_anomalies() {
    local report_file="$1"
    
    log_info "Analyzing infrastructure findings..."
    
    if [ ! -f "$report_file" ]; then
        log_error "Report file not found"
        return 1
    fi
    
    # Extract subdomains
    $PYTHON_BIN << 'EOF' "$report_file"
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

print("\n=== DISCOVERED SUBDOMAINS ===")
for subdomain in data.get('subdomains', []):
    print(f"  - {subdomain['subdomain']} (source: {subdomain['source']})")

print(f"\nTotal subdomains found: {len(data.get('subdomains', []))}")
EOF

    log_warning "Review subdomains for unexpected or development environments"
}

# ============================================================================
# 2. DEPENDENCY & CVE ASSESSMENT SCRIPTS
# ============================================================================

assess_dependencies() {
    local target="$1"
    local h1_user="$2"
    local test_email="$3"
    
    log_header "PHASE 2: DEPENDENCY & CVE ASSESSMENT"
    log_info "Target: $target"
    
    local report_file="$RESULTS_DIR/phase2_dependencies_${TIMESTAMP}.json"
    
    log_info "Running CVE lookup..."
    $PYTHON_BIN "$SCRIPT_DIR/script.py" "$target" \
        --hackerone-username "$h1_user" \
        --test-account-email "$test_email" \
        --enable-cve \
        --output "$report_file" \
        --verbose
    
    log_success "CVE assessment complete"
    echo "Report: $report_file"
    
    # Analyze CVE findings
    analyze_cves "$report_file"
}

analyze_cves() {
    local report_file="$1"
    
    log_info "Analyzing CVE findings..."
    
    $PYTHON_BIN << 'EOF' "$report_file"
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

print("\n=== CVE FINDINGS ===")
cves = data.get('cves', [])

if not cves:
    print("  No CVEs found")
    sys.exit(0)

# Sort by CVSS score
cves_sorted = sorted(cves, key=lambda x: x.get('cvss_score', 0), reverse=True)

for cve in cves_sorted:
    score = cve.get('cvss_score', 'N/A')
    severity = cve.get('severity', 'UNKNOWN')
    cve_id = cve.get('cve_id', 'UNKNOWN')
    
    print(f"\n  {cve_id} - CVSS {score} ({severity})")
    print(f"    Published: {cve.get('published', 'Unknown')}")
    print(f"    Vector: {cve.get('cvss_vector', 'N/A')}")
    print(f"    Description: {cve.get('description', 'N/A')[:100]}...")

print(f"\n\nTotal CVEs found: {len(cves)}")
print("⚠ Review each CVE for exploitability in target environment")
EOF

    log_warning "Verify CVE applicability before reporting"
}

# ============================================================================
# 3. INPUT VALIDATION & FUZZING SCRIPTS
# ============================================================================

assess_input_validation() {
    local target="$1"
    local h1_user="$2"
    local test_email="$3"
    local test_user="$4"
    local test_pass="$5"
    
    log_header "PHASE 3: INPUT VALIDATION & FUZZING"
    log_info "Target: $target"
    log_info "Test Account: $test_email"
    
    local report_file="$RESULTS_DIR/phase3_fuzzing_${TIMESTAMP}.json"
    
    log_info "Running API fuzzing tests..."
    $PYTHON_BIN "$SCRIPT_DIR/script.py" "$target" \
        --hackerone-username "$h1_user" \
        --test-account-email "$test_email" \
        --enable-fuzz \
        --auth-user "$test_user" \
        --auth-pass "$test_pass" \
        --output "$report_file" \
        --verbose
    
    log_success "Fuzzing assessment complete"
    echo "Report: $report_file"
    
    # Analyze fuzzing results
    analyze_fuzzing_results "$report_file"
}

analyze_fuzzing_results() {
    local report_file="$1"
    
    log_info "Analyzing fuzzing results..."
    
    $PYTHON_BIN << 'EOF' "$report_file"
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

print("\n=== API FUZZING RESULTS ===")
fuzz_results = data.get('api_fuzz_results', [])

if not fuzz_results:
    print("  No fuzzing results found")
    sys.exit(0)

# Categorize by response code
by_code = {}
for result in fuzz_results:
    code = result.get('response_code', 'Unknown')
    if code not in by_code:
        by_code[code] = []
    by_code[code].append(result)

for code in sorted(by_code.keys()):
    results = by_code[code]
    print(f"\n  Response Code {code}: {len(results)} results")
    
    # Show unexpected responses (4xx, 5xx errors might indicate vulnerability)
    if code >= 400:
        for result in results[:3]:  # Show first 3
            endpoint = result.get('endpoint', 'Unknown')
            payload_type = result.get('payload_type', 'Unknown')
            print(f"    - {endpoint} ({payload_type})")

print(f"\nTotal fuzzing attempts: {len(fuzz_results)}")
print("⚠ Review 5xx errors and unusual responses for vulnerabilities")
EOF

    log_warning "Check for error messages revealing system information"
}

# ============================================================================
# 4. AUTHENTICATION & AUTHORIZATION SCRIPTS
# ============================================================================

assess_authentication() {
    local target="$1"
    local h1_user="$2"
    local test_email="$3"
    local test_user="$4"
    local test_pass="$5"
    
    log_header "PHASE 4: AUTHENTICATION & AUTHORIZATION"
    log_info "Target: $target"
    log_info "Test Account: $test_email"
    
    local report_file="$RESULTS_DIR/phase4_authentication_${TIMESTAMP}.json"
    
    log_info "Running authentication tests..."
    $PYTHON_BIN "$SCRIPT_DIR/script.py" "$target" \
        --hackerone-username "$h1_user" \
        --test-account-email "$test_email" \
        --enable-auth \
        --auth-user "$test_user" \
        --auth-pass "$test_pass" \
        --output "$report_file" \
        --verbose
    
    log_success "Authentication assessment complete"
    echo "Report: $report_file"
    
    # Analyze auth results
    analyze_auth_results "$report_file"
}

analyze_auth_results() {
    local report_file="$1"
    
    log_info "Analyzing authentication results..."
    
    $PYTHON_BIN << 'EOF' "$report_file"
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

print("\n=== AUTHENTICATION TEST RESULTS ===")
auth_results = data.get('auth_test_results', [])

if not auth_results:
    print("  No auth test results found")
    sys.exit(0)

passed = sum(1 for r in auth_results if r.get('passed', False))
failed = sum(1 for r in auth_results if not r.get('passed', False))

print(f"\n  Passed: {passed}")
print(f"  Failed: {failed}")

print("\n  Failed tests (potential vulnerabilities):")
for result in auth_results:
    if not result.get('passed', False):
        test_name = result.get('test_name', 'Unknown')
        severity = result.get('severity', 'Unknown')
        details = result.get('details', 'No details')
        print(f"\n    - {test_name} ({severity})")
        print(f"      {details}")

print(f"\n\nTotal tests: {len(auth_results)}")
EOF

    log_warning "Failed auth tests indicate potential vulnerabilities"
}

# ============================================================================
# 5. BUSINESS LOGIC TESTING SCRIPTS
# ============================================================================

assess_business_logic() {
    local target="$1"
    local h1_user="$2"
    local test_email="$3"
    local test_user="$4"
    local test_pass="$5"
    
    log_header "PHASE 5: BUSINESS LOGIC ASSESSMENT"
    log_info "Target: $target"
    log_info "Test Account: $test_email"
    log_warning "This phase requires manual testing. Automated checks below are suggestions only."
    
    cat << 'EOF'

=== BUSINESS LOGIC TESTING CHECKLIST ===

1. ORDER FLOW TESTING
   - [ ] Test creating order with insufficient funds (should be rejected)
   - [ ] Verify funds are reserved before execution
   - [ ] Test modifying order in-flight
   - [ ] Test canceling partially-filled order
   - [ ] Verify no duplicate fills

2. SEQUENCE VALIDATION
   - [ ] Test calling endpoints out of order
   - [ ] Verify authorization is checked BEFORE action
   - [ ] Test if state machine can be bypassed
   - [ ] Verify operations complete atomically

3. EDGE CASES
   - [ ] Test with minimum/maximum values
   - [ ] Test boundary conditions (exactly at limit)
   - [ ] Test concurrent operations
   - [ ] Test rapid-fire requests

4. AUTHORIZATION EDGE CASES
   - [ ] Test accessing admin endpoints as regular user
   - [ ] Try accessing oak.robinhood.net
   - [ ] Test accessing other users' data/settings
   - [ ] Verify role-based access control

⚠ IMPORTANT:
  - Stay under $1,000 USD in test losses
  - Stop immediately if you gain unauthorized access
  - Report findings without further exploration
  - Document exact API calls and responses

For detailed manual testing procedures, review ETHICAL_TESTING_CHECKLIST.md
EOF
}

# ============================================================================
# 6. FULL ASSESSMENT WORKFLOW
# ============================================================================

run_full_assessment() {
    local target="$1"
    local h1_user="$2"
    local test_email="$3"
    local test_user="$4"
    local test_pass="$5"
    
    log_header "ROBINHOOD FULL VULNERABILITY ASSESSMENT"
    log_info "Target: $target"
    log_info "Test Account: $test_email"
    log_info "Results: $RESULTS_DIR"
    
    # Phase 1: Infrastructure
    assess_infrastructure "$target" "$h1_user" "$test_email"
    echo ""
    
    # Phase 2: Dependencies
    assess_dependencies "$target" "$h1_user" "$test_email"
    echo ""
    
    # Phase 3: Input Validation
    assess_input_validation "$target" "$h1_user" "$test_email" "$test_user" "$test_pass"
    echo ""
    
    # Phase 4: Authentication
    assess_authentication "$target" "$h1_user" "$test_email" "$test_user" "$test_pass"
    echo ""
    
    # Phase 5: Business Logic
    assess_business_logic "$target" "$h1_user" "$test_email" "$test_user" "$test_pass"
    echo ""
    
    # Summary
    generate_assessment_summary "$target"
}

generate_assessment_summary() {
    local target="$1"
    
    log_header "ASSESSMENT SUMMARY"
    
    local total_reports=$(find "$RESULTS_DIR" -name "phase*_${TIMESTAMP}.json" | wc -l)
    
    echo -e "\n${GREEN}Assessment Complete!${NC}"
    echo "Target: $target"
    echo "Reports Generated: $total_reports"
    echo "Location: $RESULTS_DIR"
    
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo "1. Review each phase report in detail"
    echo "2. Cross-reference findings in ETHICAL_TESTING_CHECKLIST.md"
    echo "3. Calculate CVSS scores for each vulnerability"
    echo "4. Prepare HackerOne submissions"
    echo "5. Submit findings with required headers"
    
    echo -e "\n${YELLOW}Important Reminders:${NC}"
    echo "- Only test accounts YOU own"
    echo "- Stay under \$1,000 USD testing limit"
    echo "- Report immediately if sensitive data accessed"
    echo "- Include X-Bug-Bounty and X-Test-Account-Email headers"
    echo "- Document all findings carefully"
}

# ============================================================================
# 7. DRY-RUN TEST MODE
# ============================================================================

run_dry_run_test() {
    local target="${1:-example.com}"
    local h1_user="${2:-test_user}"
    local test_email="${3:-test@example.com}"
    
    log_header "DRY-RUN TEST MODE"
    log_info "Testing configuration without actual scanning"
    log_info "Target: $target"
    
    $PYTHON_BIN "$SCRIPT_DIR/script.py" "$target" \
        --hackerone-username "$h1_user" \
        --test-account-email "$test_email" \
        --dry-run \
        --enable-cve \
        --enable-fuzz \
        --enable-auth \
        --verbose
    
    log_success "Dry-run test complete. Configuration validated."
    echo ""
    echo "Ready to perform actual assessment. Use run_full_assessment() with real credentials."
}

# ============================================================================
# 8. INTERACTIVE CLI
# ============================================================================

show_menu() {
    cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║     ROBINHOOD ETHICAL VULNERABILITY TESTING SUITE              ║
║                    Powered by Lucius                           ║
╚════════════════════════════════════════════════════════════════╝

AVAILABLE COMMANDS:

  1. dry_run_test                  - Test configuration (no scanning)
  2. assess_infrastructure         - Phase 1: Subdomains & infrastructure
  3. assess_dependencies           - Phase 2: CVE & dependency scanning
  4. assess_input_validation       - Phase 3: API fuzzing & validation
  5. assess_authentication         - Phase 4: Auth & authorization
  6. assess_business_logic         - Phase 5: Business logic (manual)
  7. run_full_assessment           - Run all phases (1-5)

USAGE EXAMPLES:

  # Test configuration first
  $ run_dry_run_test "robinhood.com" "your_h1_username" "test@example.com"

  # Run specific phase
  $ assess_infrastructure "robinhood.com" "your_h1_username" "test@example.com"

  # Run full assessment (all phases)
  $ run_full_assessment "api.robinhood.com" "your_h1_username" \
      "test@example.com" "test_user" "test_password"

IMPORTANT:
  - Replace placeholders with your real credentials
  - Only test accounts YOU own
  - Review ETHICAL_TESTING_CHECKLIST.md for detailed guidelines
  - Stay under $1,000 USD in test losses
  - Report findings responsibly

EOF
}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

# Export functions for use in shell session
export -f log_header log_success log_warning log_error log_info
export -f assess_infrastructure assess_dependencies assess_input_validation
export -f assess_authentication assess_business_logic run_full_assessment
export -f run_dry_run_test show_menu

# Show menu on first source
if [ "${1:-}" != "no-menu" ]; then
    show_menu
fi
