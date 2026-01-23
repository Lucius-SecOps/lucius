# Lucius for Robinhood Bug Bounty - Official Protocol Guide

## Overview
This guide explains how to use Lucius in compliance with Robinhood's official bug bounty program on HackerOne.

---

## Program Requirements

### Key Rules (NON-NEGOTIABLE)
1. **Test ownership**: Only test against accounts YOU own
2. **Submission headers required**: All requests must include:
   - `X-Bug-Bounty: <HackerOne-Username>`
   - `X-Test-Account-Email: <Your-Test-Account-Email>`
3. **$1,000 USD limit**: Cap testing on unbounded loss vulnerabilities at $1k USD before filing report
4. **No transactions with other accounts**
5. **Report immediately if you discover sensitive data** (SSN, credentials, etc.)
6. **Gold Standard Safe Harbor** applies—you have legal protection for authorized testing

### In-Scope Targets (Tier 1 - Highest Value)
- `*.robinhood.com` — Main web assets, APIs
- `api.robinhood.com` — AWS ALB proxying services
- `*.rhapollo.net` — Internal services
- `*.rhinternal.net` — Internal services
- `*.robinhood.net` — Internal services (oak.robinhood.net = administrative tooling)
- `nummus.robinhood.com` — Cryptocurrency trading
- iOS/Android apps

---

## Using Lucius with HackerOne Requirements

### Installation & Setup
```bash
cd /Users/chris-peterson/lucius/lucius
source .venv/bin/activate
python script.py --help
```

### Basic Usage (Minimum Compliance)
```bash
# Set your HackerOne username and test account email
HACKERONE_USER="your_hackerone_username"
TEST_EMAIL="your_test_account@example.com"

# Run reconnaissance with Robinhood headers
python script.py robinhood.com \
  --hackerone-username "$HACKERONE_USER" \
  --test-account-email "$TEST_EMAIL" \
  --verbose
```

### Full Example with All Modules
```bash
python script.py robinhood.com \
  --hackerone-username "your_username" \
  --test-account-email "test@example.com" \
  --enable-cve \
  --enable-fuzz \
  --enable-auth \
  --auth-user "your_test_username" \
  --auth-pass "your_test_password" \
  --output results.json \
  --verbose
```

### Dry-Run Testing (Before Production)
```bash
# Test configuration without actual scanning
python script.py robinhood.com \
  --hackerone-username "your_username" \
  --test-account-email "test@example.com" \
  --dry-run \
  --enable-cve \
  --enable-fuzz \
  --enable-auth \
  --verbose
```

---

## Command-Line Options

### Required for HackerOne Submission
```
--hackerone-username USERNAME
    Your HackerOne username (appears in X-Bug-Bounty header)
    
--test-account-email EMAIL
    Email of test account used (appears in X-Test-Account-Email header)
    MUST match Robinhood account email you tested with
```

### Reconnaissance Modules
```
--enable-cve
    Enable CVE lookup via NVD API
    Searches for vulnerabilities related to target keywords
    
--enable-fuzz
    Enable API fuzzing (5 payload categories)
    - SQL injection, XSS, path traversal, IDOR, logic bypass
    
--enable-auth
    Enable authentication testing
    Tests: default credentials, JWT validation, session fixation, auth bypass
    
--auth-user USERNAME
    Username for authentication testing (used with --enable-auth)
    
--auth-pass PASSWORD
    Password for authentication testing (used with --enable-auth)
```

### Configuration & Output
```
--dry-run
    Simulate execution without actual scanning
    Useful for testing configuration before live testing
    
--output FILE
    Save JSON report to file (recommended for HackerOne submission)
    
--verbose
    Enable detailed logging
    
--no-subdomains
    Skip subdomain enumeration
```

---

## Example Workflows

### 1. Subdomain Enumeration Only
```bash
python script.py api.robinhood.com \
  --hackerone-username "your_user" \
  --test-account-email "test@robinhood.com" \
  --output subdomains.json \
  --verbose
```

**Output**: List of discovered subdomains, which can indicate:
- Staging/development environments
- Internal service endpoints
- Misconfigured DNS records

**High-Value Findings**:
- Subdomains pointing to wrong infrastructure
- Subdomain takeover opportunities
- Forgotten dev/test environments

---

### 2. Vulnerability & CVE Lookup
```bash
python script.py robinhood.com \
  --hackerone-username "your_user" \
  --test-account-email "test@robinhood.com" \
  --enable-cve \
  --output cve_report.json \
  --verbose
```

**Output**: CVEs affecting Robinhood or fintech platforms, including:
- CVSS scores
- Severity levels
- Published dates

**High-Value Findings**:
- Known vulnerabilities in dependencies they use
- Recent CVEs in framework versions
- Unpatched security issues in third-party integrations

---

### 3. API Fuzzing (Authenticated Testing)
```bash
python script.py api.robinhood.com \
  --hackerone-username "your_user" \
  --test-account-email "test@robinhood.com" \
  --enable-fuzz \
  --auth-user "your_test_user" \
  --auth-pass "your_test_password" \
  --output fuzz_results.json \
  --verbose
```

**Output**: API responses to fuzzing payloads:
- SQL injection probes
- XSS payload responses
- Path traversal attempts
- IDOR (Insecure Direct Object Reference) tests
- Business logic bypass sequences

**High-Value Findings**:
- API validation bypasses
- Input filtering weaknesses
- Response header leakage
- Error messages revealing internal structure

---

### 4. Full Reconnaissance (All Modules)
```bash
python script.py robinhood.com \
  --hackerone-username "your_user" \
  --test-account-email "test@robinhood.com" \
  --enable-cve \
  --enable-fuzz \
  --enable-auth \
  --auth-user "your_test_user" \
  --auth-pass "your_test_password" \
  --output full_recon.json \
  --verbose
```

**Output**: Comprehensive JSON report with:
- Enumerated subdomains
- CVE findings with CVSS scores
- API fuzzing results (payloads + responses)
- Authentication test results
- Aggregated metadata

---

## Output Format & CVSS Scoring

### JSON Report Structure
```json
{
  "timestamp": "2026-01-22T14:30:00+00:00",
  "target": "robinhood.com",
  "subdomains_found": 15,
  "vulnerabilities_found": 3,
  "subdomains": [
    {
      "subdomain": "api.robinhood.com",
      "source": "google"
    }
  ],
  "cves": [
    {
      "cve_id": "CVE-2025-1234",
      "cvss_score": 7.5,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
      "severity": "HIGH",
      "description": "...",
      "published": "2025-01-15"
    }
  ],
  "api_fuzz_results": [
    {
      "endpoint": "/api/users",
      "payload_type": "sql_injection",
      "payload": "' OR '1'='1",
      "response_code": 400,
      "response_preview": "..."
    }
  ],
  "auth_test_results": [
    {
      "test_name": "default_credentials",
      "passed": false,
      "details": "Default credentials not accepted"
    }
  ],
  "metadata": {
    "modules_enabled": {
      "subdomain_scan": true,
      "cve_lookup": true,
      "api_fuzz": true,
      "auth_test": true
    }
  }
}
```

### CVSS v3.1 Calculation
Lucius automatically calculates CVSS scores when CVEs are found. Include this breakdown in your HackerOne submission:

**Example**:
```
Vulnerability: SQL Injection in /api/orders endpoint
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H
CVSS Score: 9.1 (CRITICAL)

Breakdown:
- AV (Attack Vector): Network (N)
- AC (Attack Complexity): Low (L)
- PR (Privileges Required): Low (L)
- UI (User Interaction): None (N)
- S (Scope): Changed (C)
- C (Confidentiality): High (H)
- I (Integrity): High (H)
- A (Availability): High (H)

Impact:
- High confidentiality impact: Database/user records accessible
- High integrity impact: Orders can be modified
- High availability impact: Service disruption possible
```

---

## Key Findings to Target (High-Value Opportunities)

### $5,000 - $25,000 (Critical/Business Logic)
- **State machine bypass**: Orders processed out of sequence (account takeover)
- **Infinite leverage**: Margin calculation bypasses
- **Race conditions**: Double-spend vulnerabilities in trade execution
- **Authentication bypass**: Gaining access without valid credentials
- **Privilege escalation**: Customer accessing admin/support endpoints

### $3,000 - $10,000 (High/Authenticated)
- **Unauthorized actions**: Transactions possible without permission
- **Sensitive data disclosure**: PII/account numbers leakage
- **Account manipulation**: Changing profile/settings for other users
- **API logic flaws**: Orders executed when they should be rejected

### $1,000 - $3,000 (Medium)
- **Information disclosure**: System version/path leakage
- **IDOR vulnerabilities**: Direct ID manipulation
- **Session management flaws**: Token/cookie issues
- **Input validation**: Weak parameter checking

---

## Submission Checklist

Before submitting to HackerOne:

- [ ] Tested against account YOU own
- [ ] Verified X-Bug-Bounty header: `your_hackerone_username`
- [ ] Verified X-Test-Account-Email: `your_test_account@example.com`
- [ ] Included CVSS v3.1 score and vector string
- [ ] **Demonstrable impact**: Show actual data accessed, not theoretical
- [ ] Documented exact reproduction steps
- [ ] Included affected endpoint/domain (e.g., `api.robinhood.com/orders`)
- [ ] Screenshots/logs of vulnerability proof
- [ ] Test account email matches HackerOne profile
- [ ] For unbounded loss: Did NOT exceed $1,000 USD before reporting
- [ ] Read and agreed to program rules (no other account testing, no DOS, etc.)

### Submission Template
```
**Summary**:
[One-line description of vulnerability]

**Affected Asset**:
[Domain/endpoint affected, e.g., api.robinhood.com/api/orders]

**Vulnerability Type**:
[CVSS Category, e.g., Improper Input Validation, Authentication Bypass]

**CVSS Score & Vector**:
Score: X.X (SEVERITY)
Vector: CVSS:3.1/[full vector string]

**Steps to Reproduce**:
1. Login to test account: your_test_email@example.com
2. [Detailed steps]
3. [Observe vulnerable behavior]

**Proof of Concept**:
[Code/payload/screenshots showing impact]

**Impact**:
[What attacker can do, with actual data accessed if applicable]

**Testing Methodology**:
Tested with Lucius Security Reconnaissance Framework v1.0
Headers: X-Bug-Bounty: your_username, X-Test-Account-Email: your_test_email@example.com
```

---

## Important Reminders

1. **Only test YOUR accounts**: Robinhood explicitly prohibits testing other user accounts
2. **$1,000 USD limit**: For unbounded loss vulns, stop at $1k and file report
3. **Stop on sensitive data**: If you discover SSN, credentials, etc., report immediately
4. **No financial transactions**: Don't execute real trades with other accounts
5. **No DOS**: Don't resource-exhaust or crash services
6. **Safe harbor applies**: You have legal protection under HackerOne's Gold Standard Safe Harbor
7. **Confidentiality**: Never share reports publicly or on social media

---

## Questions?

- **Robinhood program**: https://hackerone.com/robinhood
- **HackerOne docs**: https://docs.hackerone.com/
- **This framework**: See ARCHITECTURE.md and IMPLEMENTATION_SUMMARY.md for technical details

Good luck with your testing! Follow the protocol, document thoroughly, and report responsibly.
