# Robinhood Ethical Testing - Quick Start Guide

## Overview

This guide provides **step-by-step examples** for ethical vulnerability testing across all 5 categories using Lucius and the provided testing scripts.

---

## Setup (Do This First)

### 1. Create Test Account
- Go to robinhood.com
- Create account using your real email (e.g., `yourname+robinhood@example.com`)
- Verify email
- Complete KYC/account setup
- Fund with small amount ($5-10 for testing)
- Document credentials securely

### 2. Get HackerOne Username
- Create/login to HackerOne account
- Note your username (visible in profile)
- This will be your `--hackerone-username` value

### 3. Activate Testing Scripts
```bash
cd /Users/chris-peterson/lucius/lucius
source .venv/bin/activate
chmod +x robinhood_testing_suite.sh
chmod +x testing_scripts.py
source robinhood_testing_suite.sh
```

### 4. Verify Setup
```bash
# Dry-run test (no actual scanning)
run_dry_run_test "example.com" "your_h1_username" "your_test@example.com"
```

---

## Phase 1: Infrastructure Assessment (2-3 hours)

### What You'll Find
- Enumerated subdomains
- Exposed internal services
- Misconfigured DNS
- Potential subdomain takeovers

### Command
```bash
# Test api.robinhood.com infrastructure
assess_infrastructure "api.robinhood.com" "your_h1_username" "your_test@example.com"

# Or with Lucius directly
python script.py api.robinhood.com \
  --hackerone-username "your_h1_username" \
  --test-account-email "your_test@example.com" \
  --output infrastructure_report.json \
  --verbose
```

### Expected Output
```json
{
  "subdomains_found": 15,
  "subdomains": [
    {"subdomain": "api.robinhood.com", "source": "google"},
    {"subdomain": "oak.robinhood.net", "source": "bing"},
    {"subdomain": "dev-api.robinhood.com", "source": "simulation"}
  ]
}
```

### Manual Verification Steps

**For each subdomain found:**

1. **Check DNS/CNAME:**
   ```bash
   nslookup subdomain.robinhood.com
   # or
   dig subdomain.robinhood.com
   ```

2. **Check HTTP response:**
   ```bash
   curl -I https://subdomain.robinhood.com
   ```

3. **Look for signs of takeover risk:**
   - If CNAME points to CloudFront/GitHub Pages/Heroku
   - If service responds with 404 or "Not Found"
   - If domain has no registrant information

### High-Value Findings

| Finding | Bounty | Report Template |
|---------|--------|-----------------|
| **Subdomain Takeover** (expired domain pointing to vulnerable service) | $3k-$10k | Document: subdomain, CNAME target, proof of access |
| **Dev/Staging Exposed** (development environment accessible publicly) | $2k-$8k | Document: subdomain, environment name, exposed data |
| **Internal Service Accessible** (internal tool accessible to internet) | $3k-$10k | Document: service name, endpoints accessed, data exposed |

### Example Finding: Exposed Dev Environment

```
TITLE: Development API Accessible Without Authentication

AFFECTED ASSET: dev-api.robinhood.com

CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
CVSS Score: 7.5 (HIGH)

STEPS TO REPRODUCE:
1. Navigate to https://dev-api.robinhood.com/api/instruments
2. No authentication required
3. Can enumerate all trading instruments with full details

IMPACT:
- Development API exposed without authentication
- Potential access to internal endpoints
- Information disclosure of API structure

HEADERS:
X-Bug-Bounty: your_h1_username
X-Test-Account-Email: your_test@example.com
```

---

## Phase 2: Dependency & CVE Assessment (2-3 hours)

### What You'll Find
- Unpatched critical CVEs
- Outdated frameworks
- Third-party component vulnerabilities

### Command
```bash
# Run CVE scan
assess_dependencies "api.robinhood.com" "your_h1_username" "your_test@example.com"

# Or with Lucius directly
python script.py api.robinhood.com \
  --enable-cve \
  --hackerone-username "your_h1_username" \
  --test-account-email "your_test@example.com" \
  --output cve_report.json \
  --verbose
```

### Expected Output
```json
{
  "cves": [
    {
      "cve_id": "CVE-2025-1234",
      "cvss_score": 9.1,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
      "severity": "CRITICAL",
      "description": "Remote Code Execution in Framework XYZ",
      "published": "2025-01-15"
    }
  ]
}
```

### Manual Verification Steps

**For each CVE found:**

1. **Extract version from headers:**
   ```bash
   curl -I https://api.robinhood.com | grep -i "server\|x-powered\|x-aspnet"
   ```

2. **Check if version matches CVE:**
   - CVE says: vulnerable in 1.2.0-1.2.5
   - Headers show: Server: MyApp/1.2.3
   - Result: VULNERABLE ✓

3. **Research CVE details:**
   - Visit https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXX
   - Check if public exploit exists
   - Verify remote exploitability

4. **Test (carefully!):**
   - Try proof-of-concept on non-production endpoint ONLY
   - Document response
   - Report immediately

### High-Value Findings

| Finding | Bounty | Requirement |
|---------|--------|------------|
| **Critical CVE (CVSS 9+) with RCE** | $5k-$25k | Verify version, confirm exploitability, DON'T exploit production |
| **High CVE (CVSS 7-8.9)** | $3k-$10k | Verify version, confirm impact |
| **Known Vulnerability in Component** | $2k-$8k | Document version and CVE |

### Example Finding: Unpatched Framework

```
TITLE: Remote Code Execution via Unpatched Framework

AFFECTED ASSET: api.robinhood.com

CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H
CVSS Score: 9.1 (CRITICAL)

VULNERABILITY DETAILS:
- CVE-2025-1234 affects framework XYZ versions 1.2.0-1.2.5
- Robinhood is running version 1.2.3 (confirmed via Server header)
- Public exploit available on GitHub
- Vulnerability allows unauthenticated RCE

PROOF:
Server header: Server: Express/1.2.3
CVE Match: ✓ (CVE-2025-1234)

STEPS TO REPRODUCE:
1. curl -I https://api.robinhood.com (shows Express/1.2.3)
2. Visit https://nvd.nist.gov/vuln/detail/CVE-2025-1234
3. Confirm vulnerability in 1.2.3

IMPACT:
- Remote code execution possible
- Full system compromise risk
- Urgent patching required

HEADERS:
X-Bug-Bounty: your_h1_username
X-Test-Account-Email: your_test@example.com
```

---

## Phase 3: Input Validation & Fuzzing (6-8 hours)

### What You'll Find
- SQL Injection vulnerabilities
- XSS in authenticated contexts
- IDOR (Insecure Direct Object Reference)
- Path Traversal
- Logic bypasses

### Command
```bash
# Run fuzzing with authentication
assess_input_validation "api.robinhood.com" \
  "your_h1_username" \
  "your_test@example.com" \
  "your_test_username" \
  "your_test_password"

# Or with Lucius directly
python script.py api.robinhood.com \
  --enable-fuzz \
  --auth-user "your_test_username" \
  --auth-pass "your_test_password" \
  --hackerone-username "your_h1_username" \
  --test-account-email "your_test@example.com" \
  --output fuzzing_report.json \
  --verbose
```

### IDOR Testing Workflow (Most Common High-Value Finding)

**Step 1: Identify user/resource ID parameters**
```bash
# Using curl to test /api/orders endpoint
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.robinhood.com/api/orders?account_id=12345" | jq .

# Response shows: your orders
```

**Step 2: Test with different ID**
```bash
# Try incrementing account_id
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.robinhood.com/api/orders?account_id=12346" | jq .

# VULNERABILITY: If you get another user's orders, STOP HERE and report
```

**Step 3: Document and Report**
- STOP testing immediately
- Document the request and response
- Take one screenshot
- Report to HackerOne

### Example Finding: IDOR Vulnerability

```
TITLE: IDOR Allows Access to Other Users' Orders

AFFECTED ASSET: https://api.robinhood.com/api/orders

CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N
CVSS Score: 6.5 (MEDIUM-HIGH)

VULNERABILITY DETAILS:
Account ID is not validated server-side. By incrementing account_id
parameter, any authenticated user can access orders of any other user.

REPRODUCTION STEPS:
1. Login to test account (test@example.com)
2. GET https://api.robinhood.com/api/orders?account_id=YOUR_ID
3. Response: Your orders (expected)
4. GET https://api.robinhood.com/api/orders?account_id=OTHER_USER_ID
5. Response: Other user's orders (UNEXPECTED - VULNERABLE)

PROOF OF CONCEPT:
Request:
  GET /api/orders?account_id=999 HTTP/1.1
  Host: api.robinhood.com
  Authorization: Bearer <YOUR_TOKEN>

Response:
  200 OK
  {
    "orders": [
      {
        "id": "order_999_1",
        "user_id": 999,
        "symbol": "AAPL",
        "quantity": 100,
        "price": 150.00
      }
    ]
  }

IMPACT:
- Any authenticated user can enumerate all user orders
- Sensitive trading information exposed
- Can correlate orders to identify users
- Information can be used for market manipulation

REMEDIATION:
- Server-side verify account_id belongs to authenticated user
- Implement proper authorization checks
- Return 403 Forbidden for unauthorized access

HEADERS:
X-Bug-Bounty: your_h1_username
X-Test-Account-Email: your_test@example.com
```

---

## Phase 4: Authentication & Authorization (4-5 hours)

### What You'll Find
- Authentication bypass
- Privilege escalation
- Session management flaws
- JWT vulnerabilities
- Default credentials

### Command
```bash
# Run authentication tests
assess_authentication "api.robinhood.com" \
  "your_h1_username" \
  "your_test@example.com" \
  "your_test_username" \
  "your_test_password"

# Or with Lucius directly
python script.py api.robinhood.com \
  --enable-auth \
  --auth-user "your_test_username" \
  --auth-pass "your_test_password" \
  --hackerone-username "your_h1_username" \
  --test-account-email "your_test@example.com" \
  --output auth_report.json \
  --verbose
```

### JWT Token Testing (If Used)

**Step 1: Capture JWT token**
```bash
# After login, capture Authorization header
curl -s -H "Authorization: Bearer eyJhbGc..." \
  "https://api.robinhood.com/api/user" | jq .
```

**Step 2: Decode token (jwt.io)**
```
Header: {
  "alg": "HS256",
  "typ": "JWT"
}

Payload: {
  "sub": "user_12345",
  "iat": 1642770000,
  "exp": 1642856400,
  "aud": "robinhood-api"
}

Signature: [HMAC-SHA256]
```

**Step 3: Check for vulnerabilities**
```bash
# Try with "alg": "none"
# Try with modified claims
# Try after expiration
# Check signature validation
```

### Authorization Testing

**Step 1: Try accessing admin endpoints**
```bash
# Try oak.robinhood.net (internal admin tool)
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "https://oak.robinhood.net/api/admin/users" | jq .

# If you get 200 (not 403/401), that's a CRITICAL finding - STOP and report
```

**Step 2: Check permission enforcement**
```bash
# Try accessing other user's settings
curl -s -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.robinhood.com/api/user/12346/settings" | jq .

# If successful, it's privilege escalation - report immediately
```

### Example Finding: Privilege Escalation

```
TITLE: Privilege Escalation Allows Regular User to Access Admin Endpoints

AFFECTED ASSET: https://oak.robinhood.net/api/admin/

CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H
CVSS Score: 9.1 (CRITICAL)

VULNERABILITY DETAILS:
Authorization checks are not properly enforced on administrative endpoints.
A regular user with valid authentication can access administrative
functions intended for support staff only.

REPRODUCTION STEPS:
1. Create regular test account (test@robinhood.com)
2. Login and capture JWT token
3. GET https://oak.robinhood.net/api/admin/users
   Authorization: Bearer <YOUR_TOKEN>
4. Response: 200 OK with list of all users (VULNERABLE)

Expected: 403 Forbidden (permission denied)
Actual: 200 OK (admin access granted)

PROOF OF CONCEPT:
Request:
  GET /api/admin/users HTTP/1.1
  Host: oak.robinhood.net
  Authorization: Bearer eyJhbGc...

Response:
  200 OK
  {
    "users": [
      {"id": 1, "email": "user1@example.com", ...},
      {"id": 2, "email": "user2@example.com", ...},
      ...
    ]
  }

IMPACT:
- Complete administrative access from regular account
- Can modify other users' accounts
- Can freeze/unfreeze accounts
- Can access sensitive customer information
- Massive security breach

REMEDIATION:
- Verify user role before granting admin access
- Implement proper RBAC (Role-Based Access Control)
- Log all admin access attempts
- Require additional authentication for admin functions

HEADERS:
X-Bug-Bounty: your_h1_username
X-Test-Account-Email: your_test@example.com
```

---

## Phase 5: Business Logic Testing (4-6 hours)

### What You'll Find
- Sequence bypass
- Race conditions
- Logic flaws in workflows
- State machine inconsistencies

### Manual Testing (No Script)

```bash
# Use testing_scripts.py for guidance
python3 testing_scripts.py api.robinhood.com --business-logic
```

### Example 1: Insufficient Funds Check Bypass

**Objective:** Test if you can place order larger than account balance

```bash
# Setup
1. Test account has $100
2. Try to buy 1000 shares of $1 stock (requires $1000)

# What should happen
- Order should be rejected
- Error message: "Insufficient buying power"

# What to test
- Try via API directly (bypass UI validation)
- Try with margin (if disabled, should still fail)
- Try concurrent requests (race condition)

# If vulnerable:
curl -X POST https://api.robinhood.com/api/orders \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "instrument": "AAPL",
    "quantity": 1000,
    "price": 150
  }'

# VULNERABLE if response is:
200 OK
{
  "order_id": "order_123",
  "status": "confirmed"
}

# SECURE if response is:
400 Bad Request
{
  "error": "Insufficient buying power"
}
```

### Example 2: Race Condition in Order Processing

**Objective:** Test if concurrent orders can bypass sequential processing

```bash
# Send two orders simultaneously
bash -c '
curl -X POST https://api.robinhood.com/api/orders \
  -H "Authorization: Bearer TOKEN" \
  -d "{\"instrument\":\"AAPL\",\"quantity\":100}" &

curl -X POST https://api.robinhood.com/api/orders \
  -H "Authorization: Bearer TOKEN" \
  -d "{\"instrument\":\"AAPL\",\"quantity\":100}" &

wait
'

# VULNERABILITY if:
- Both orders filled even if total exceeds buying power
- Double-fill on same position
- Stock balance becomes negative

# SECURE if:
- Only one order fills
- Second order is queued/rejected
- Balance stays consistent
```

### Example Finding: Sequence Bypass

```
TITLE: Order Execution Bypasses Funds Validation

AFFECTED ASSET: https://api.robinhood.com/api/orders

CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H
CVSS Score: 9.8 (CRITICAL)

VULNERABILITY DETAILS:
API does not validate buying power server-side before confirming orders.
By calling POST /api/orders directly, attacker can execute trades without
sufficient funds. The system credits the trade optimistically before
validating available margin.

REPRODUCTION STEPS:
1. Create test account with $100 buying power
2. Attempt to buy 1000 shares of $1 stock via API:
   POST /api/orders
   {"instrument": "AAPL", "quantity": 1000, "price": 150}
3. Order is confirmed despite insufficient funds
4. Verify account shows negative balance

PROOF:
Account balance: $100
Attempted purchase: 1000 * $150 = $150,000
Result: Order filled (VULNERABLE)

Expected: Order rejected with 400 Bad Request
Actual: Order accepted with 200 OK

IMPACT:
- Trading beyond available funds (infinite leverage)
- Massive financial risk
- Regulatory violation
- Account fraud

HEADERS:
X-Bug-Bounty: your_h1_username
X-Test-Account-Email: your_test@example.com

⚠ IMPORTANT: Stop testing immediately after confirming vulnerability.
Do NOT attempt to complete trade or realize financial loss.
```

---

## Full Assessment in One Session

### Quick Command (All Phases)
```bash
export H1_USER="your_h1_username"
export TEST_EMAIL="your_test@example.com"
export TEST_USER="your_test_username"
export TEST_PASS="your_test_password"

run_full_assessment "api.robinhood.com" "$H1_USER" "$TEST_EMAIL" "$TEST_USER" "$TEST_PASS"
```

### Expected Timeline
- **Phase 1 (Infrastructure):** 2-3 hours
- **Phase 2 (Dependencies):** 2-3 hours
- **Phase 3 (Fuzzing):** 6-8 hours
- **Phase 4 (Authentication):** 4-5 hours
- **Phase 5 (Business Logic):** 4-6 hours
- **Analysis & Reporting:** 3-4 hours

**Total: 21-29 hours of thorough testing**

---

## Reporting Checklist

Before submitting each finding:

- [ ] Tested with YOUR account only
- [ ] Documented exact reproduction steps
- [ ] Calculated CVSS v3.1 score (use https://www.first.org/cvss/calculator/3.1)
- [ ] Included CVSS vector string
- [ ] Took screenshot/captured proof
- [ ] Verified finding is still reproducible
- [ ] Prepared JSON output from Lucius
- [ ] Written clear impact statement
- [ ] Included required headers (X-Bug-Bounty, X-Test-Account-Email)
- [ ] Reviewed for sensitive data
- [ ] Ready to submit to HackerOne

---

## Good Luck!

You now have:
✓ Complete testing checklist  
✓ Automated testing scripts  
✓ Step-by-step examples  
✓ Finding templates  
✓ CVSS calculator  
✓ Reporting guides  

Follow the protocol, document thoroughly, and test ethically. Happy hunting!
