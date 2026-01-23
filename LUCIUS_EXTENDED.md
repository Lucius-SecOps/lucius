# Lucius Extended Security Reconnaissance Framework

## Overview

Lucius is now a comprehensive security reconnaissance and vulnerability assessment platform with integrated:
- **Subdomain Enumeration** (via sublist3r)
- **CVE Lookup** (via NVD API - National Vulnerability Database)
- **API Fuzzing** (payload-based vulnerability detection)
- **Authentication Testing** (default credentials, JWT validation, auth bypass)
- **CVSS Scoring** (CVSSv3.1 calculation engine)

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m py_compile script.py
```

### Dependencies
- `sublist3r>=1.0.0` — Subdomain enumeration
- `sqlmap>=1.7.0` — SQL injection testing (optional)
- `requests>=2.31.0` — HTTP client for NVD API and API fuzzing

---

## Usage

### Basic Subdomain Enumeration
```bash
python script.py robinhood.com --verbose
python script.py robinhood.com --output results.json
```

### Full Reconnaissance (CVE + Fuzz + Auth)
```bash
python script.py robinhood.com \
  --enable-cve \
  --enable-fuzz \
  --enable-auth \
  --output full_scan.json \
  --verbose
```

### With Authentication Credentials
```bash
python script.py robinhood.com \
  --enable-auth \
  --auth-user testuser \
  --auth-pass testpass \
  --verbose
```

### Dry-Run Mode (Simulation)
```bash
python script.py robinhood.com \
  --dry-run \
  --enable-cve \
  --enable-fuzz \
  --enable-auth
```

---

## Command-Line Options

| Option | Description |
|--------|-------------|
| `target` | **Required.** Target domain to scan |
| `-o, --output` | Save results to JSON file |
| `-v, --verbose` | Enable verbose/debug logging |
| `--dry-run` | Simulate without actual execution |
| `--no-subdomains` | Skip subdomain enumeration |
| `--enable-cve` | Enable CVE lookup via NVD API |
| `--enable-fuzz` | Enable API fuzzing |
| `--enable-auth` | Enable authentication testing |
| `--auth-user` | Username for auth tests |
| `--auth-pass` | Password for auth tests |

---

## Output Report

The JSON report includes:

```json
{
  "timestamp": "2026-01-22T17:40:23.977532+00:00",
  "target": "robinhood.com",
  "subdomains_found": 5,
  "vulnerabilities_found": 2,
  "subdomains": [
    {
      "domain": "robinhood.com",
      "subdomain": "api.robinhood.com",
      "source": "sublist3r",
      "timestamp": "2026-01-22T17:40:23.977532+00:00"
    }
  ],
  "cves": [
    {
      "cve_id": "CVE-2024-1234",
      "cvss_score": 9.8,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
      "description": "Critical authentication bypass in trading API",
      "published": "2024-01-15",
      "severity": "CRITICAL",
      "affected_products": []
    }
  ],
  "api_fuzz_results": [
    {
      "endpoint": "/api/users",
      "method": "GET",
      "payload": "?id=999999",
      "status_code": 200,
      "response_preview": "{...}",
      "vulnerability_type": "idor",
      "timestamp": "2026-01-22T17:40:23.977532+00:00"
    }
  ],
  "auth_test_results": [
    {
      "target": "https://robinhood.com",
      "test_name": "Default Credentials (admin:admin)",
      "passed": true,
      "details": "Credentials not found (as expected)",
      "severity": "INFO",
      "timestamp": "2026-01-22T17:40:23.977532+00:00"
    }
  ],
  "metadata": {
    "dry_run": false,
    "tools_used": ["sublist3r", "NVD API", "API Fuzzer", "Auth Tester"],
    "python_version": "3.11.0",
    "sublist3r_available": true,
    "modules_enabled": {
      "subdomain_scan": true,
      "cve_lookup": true,
      "api_fuzz": true,
      "auth_test": true
    }
  }
}
```

---

## Module Breakdown

### 1. **SubdomainScanner**
- Enumerates subdomains using sublist3r
- Supports google, bing engines (can be extended)
- Fallback to simulation if no results

```python
scanner = SubdomainScanner(logger)
results = scanner.scan("robinhood.com", dry_run=False)
```

### 2. **CVEScanner** (NVD Integration)
- Real-time access to National Vulnerability Database
- Searches by keyword (e.g., "robinhood", "fintech")
- Extracts CVSS v3.1 scores and severity ratings
- Rate-limited to respect NVD API

```python
cve_scanner = CVEScanner(logger)
cves = cve_scanner.scan(["robinhood", "trading"], dry_run=False)
```

### 3. **APIFuzzer**
- Tests API endpoints with 5 payload categories:
  - SQL Injection
  - XSS (Cross-Site Scripting)
  - Path Traversal
  - IDOR (Insecure Direct Object References)
  - Logic Bypass

```python
fuzzer = APIFuzzer(logger)
results = fuzzer.fuzz("https://api.robinhood.com", ["/users", "/admin"], dry_run=False)
```

### 4. **AuthTester**
- Tests for default credentials
- JWT token validation
- Session fixation detection
- Authentication bypass attempts

```python
auth_tester = AuthTester(logger)
results = auth_tester.test("https://robinhood.com", username="test", password="test")
```

### 5. **CVSSScorer** (CVSSv3.1 Calculator)
- Calculates CVSS scores based on vulnerability characteristics
- Supports all v3.1 metrics
- Auto-determines severity (CRITICAL, HIGH, MEDIUM, LOW, NONE)

```python
scorer = CVSSScorer(logger)
result = scorer.calculate(
    attack_vector="N",       # Network
    attack_complexity="L",   # Low
    privileges_required="N", # None
    user_interaction="N",    # None
    scope="U",               # Unchanged
    confidentiality="H",     # High
    integrity="H",           # High
    availability="H"         # High
)
# Output: {"score": 9.8, "severity": "CRITICAL", "vector": "...", "impact": ...}
```

---

## Robinhood Bug Bounty Program Integration

Lucius is optimized for Robinhood's bug bounty program scope:

### **Tier 1 Targets** (Highest Bounties $1,000–$25,000)
- `*.robinhood.com` — Web app, APIs
- `api.robinhood.com` — Central proxy
- `nummus.robinhood.com` — Crypto trading
- `*.rhapollo.net` — Internal services
- `oak.robinhood.net` — Admin tool (Major Oak)

### **High-Value Vulnerability Vectors**
1. **Authenticated Bugs** → $3,000–$10,000
2. **Business Logic** → $5,000–$25,000
3. **Sensitive Data** → $5,000–$25,000
4. **Admin Tool Access** → **HIGHEST**

### **Robinhood Submission Headers**
When reporting, include:
```bash
X-Bug-Bounty: <your-hackerone-username>
X-Test-Account-Email: <test-email>
```

---

## Example Workflow for Robinhood

```bash
# Step 1: Enumerate subdomains
python script.py robinhood.com --output subs.json --verbose

# Step 2: Lookup related CVEs
python script.py robinhood.com --enable-cve --output cves.json

# Step 3: Fuzz APIs
python script.py api.robinhood.com --enable-fuzz --output fuzz.json

# Step 4: Test auth with your test account
python script.py robinhood.com \
  --enable-auth \
  --auth-user your-test-account \
  --auth-pass your-password \
  --output auth_results.json

# Step 5: Full reconnaissance
python script.py oak.robinhood.net \
  --enable-cve --enable-fuzz --enable-auth \
  --output final_report.json \
  --verbose
```

---

## Dry-Run for Testing

Test the framework without hitting live services:
```bash
python script.py robinhood.com --dry-run --enable-cve --enable-fuzz --enable-auth --verbose
```

This will simulate all modules and display expected output format.

---

## Performance & Rate Limiting

- **NVD API**: 1-second delay between requests (respects rate limits)
- **API Fuzzing**: 10-second timeout per request
- **Sublist3r**: 30-second timeout, 40 threads
- **Auth Tests**: Sequential execution to avoid lockouts

---

## Responsible Disclosure

⚠️ **IMPORTANT**: 
- Only test domains/APIs you own or have explicit permission to test
- Stop immediately if you discover sensitive data (SSN, credentials)
- Do not cause harm or disruption to services
- Follow Robinhood's program rules: https://hackerone.com/robinhood

---

## Security Notes

- Credentials passed via `--auth-user` / `--auth-pass` are used only for testing
- Reports are saved locally as JSON; do not commit to version control
- Always use `--dry-run` first to validate payloads
- NVD API calls are logged; review for compliance with local regulations

---

## Future Enhancements

- [ ] Shodan/Censys integration for asset discovery
- [ ] GraphQL introspection fuzzing
- [ ] JWT cracking/algorithm downgrade tests
- [ ] Database fingerprinting (MySQL, PostgreSQL, Oracle)
- [ ] Mobile app APK analysis
- [ ] Webhook payload interception
- [ ] ML-based anomaly detection in responses

---

## Support & Debugging

Enable verbose logging for troubleshooting:
```bash
python script.py robinhood.com --enable-cve --verbose 2>&1 | tee debug.log
```

Review `debug.log` for:
- Sublist3r engine failures
- NVD API connectivity issues
- API response parsing errors
- Auth test failures

---

**Lucius** — Your ethical security cheat code.
