# Authorization Testing Quick Reference

## Overview

The enhanced authorization testing module provides ethical verification of authorization controls without attempting to escalate privileges or access other users' data.

---

## Three Testing Methods

### 1. Data Scope Enforcement

**Goal:** Verify the system only returns YOUR data

```python
from testing_scripts import AuthorizationTester

tester = AuthorizationTester("api.robinhood.com", verbose=True)

# Test your data isolation
results = tester.test_data_scope_enforcement([
    {
        "endpoint": "/api/orders",
        "expected_user_id": "your_user_id",
        "returned_user_ids": ["your_user_id"],  # Good!
        "count": 5
    },
    {
        "endpoint": "/api/positions",
        "expected_user_id": "your_user_id",
        "returned_user_ids": ["your_user_id", "attacker_user_id"],  # BUG!
        "count": 10
    }
])
```

**Expected Output (Bug):**
```
2026-01-22 10:30:45 - root - ERROR - CRITICAL: Data scope breach on /api/positions
2026-01-22 10:30:45 - root - ERROR -   CRITICAL: Data scope enforcement failure
```

**CVSS Score:** 8.2 (High)

**Remediation:**
- Add user_id verification in query filters
- Implement row-level security policies
- Add audit logging for data access

---

### 2. Authentication Requirements

**Goal:** Verify endpoints properly enforce authentication

```python
tester = AuthorizationTester("api.robinhood.com", verbose=True)

# Test authentication enforcement
results = tester.test_endpoint_authentication_requirements([
    {
        "endpoint": "/api/orders",
        "requires_auth": True,
        "response_code": 401,  # Correct - rejected
        "authenticated": False
    },
    {
        "endpoint": "/api/public/markets",
        "requires_auth": False,
        "response_code": 200,  # Correct - allowed
        "authenticated": False
    },
    {
        "endpoint": "/api/account",
        "requires_auth": True,
        "response_code": 200,  # BUG! Should be 401
        "authenticated": False
    }
])
```

**Expected Output (Bug):**
```
2026-01-22 10:31:12 - root - ERROR - CRITICAL: Auth bypass on /api/account
2026-01-22 10:31:12 - root - ERROR -   CRITICAL: Missing authentication enforcement
```

**CVSS Score:** 9.1 (Critical)

**Remediation:**
- Add authentication middleware to endpoint
- Verify auth token in request handler
- Return 401 for missing/invalid tokens

---

### 3. Privilege Level Enforcement

**Goal:** Verify regular users cannot execute admin operations

```python
tester = AuthorizationTester("api.robinhood.com", verbose=True)

# Test privilege enforcement
results = tester.test_privilege_level_enforcement([
    {
        "operation": "view_own_orders",
        "user_privilege": "user",
        "response_code": 200,  # Correct
        "can_execute": True
    },
    {
        "operation": "delete_user",
        "user_privilege": "user",
        "response_code": 200,  # BUG! Should be 403
        "can_execute": True  # Regular user deleted account!
    },
    {
        "operation": "remove_2fa",
        "user_privilege": "user",
        "response_code": 403,  # Correct
        "can_execute": False
    },
    {
        "operation": "modify_balance",
        "user_privilege": "user",
        "response_code": 200,  # BUG!
        "can_execute": True
    }
])
```

**Expected Output (Bugs):**
```
2026-01-22 10:32:01 - root - ERROR - CRITICAL: Privilege escalation via delete_user
2026-01-22 10:32:01 - root - ERROR - CRITICAL: Privilege escalation via modify_balance
```

**CVSS Scores:**
- `delete_user`: 9.1 (Critical) - Impacts integrity & availability
- `modify_balance`: 9.1 (Critical) - Impacts integrity
- `remove_2fa`: 7.5 (High) - Impacts confidentiality

**Remediation:**
- Implement role-based access control (RBAC)
- Verify user role before admin operations
- Add privilege check middleware
- Audit log all privileged operations

---

## Integration with Main Testing Suite

### Run All Authorization Tests

```bash
python3 testing_scripts.py api.robinhood.com --authorization --verbose
```

### Run All Tests Including Authorization

```bash
python3 testing_scripts.py api.robinhood.com --all --output results.json --submission-template
```

---

## Real-World Testing Scenario

### Setup
```python
import requests
from testing_scripts import AuthorizationTester, ReportGenerator

# Initialize tester
tester = AuthorizationTester("api.robinhood.com", verbose=True)

# Your test account credentials
test_user_id = "your_user_id"
test_token = "your_auth_token"
```

### Test 1: Verify Your Data Isolation
```python
# Query your orders
response = requests.get(
    "https://api.robinhood.com/api/orders",
    headers={"Authorization": f"Bearer {test_token}"}
)

# Parse response
data = response.json()
your_orders = data.get("results", [])

# Check what user_ids are in the response
user_ids_in_response = list(set(o["user_id"] for o in your_orders))

# Run the test
results = tester.test_data_scope_enforcement([
    {
        "endpoint": "/api/orders",
        "expected_user_id": test_user_id,
        "returned_user_ids": user_ids_in_response,
        "count": len(your_orders)
    }
])

# Check results
if results:
    print(f"⚠️  CRITICAL FINDING: {results[0].description}")
else:
    print("✅ Data properly scoped")
```

### Test 2: Verify Authentication Enforcement
```python
# Attempt to access endpoint WITHOUT authentication
response = requests.get(
    "https://api.robinhood.com/api/account"
    # No Authorization header!
)

# Run the test
results = tester.test_endpoint_authentication_requirements([
    {
        "endpoint": "/api/account",
        "requires_auth": True,
        "response_code": response.status_code,
        "authenticated": False
    }
])

# Check results
if results:
    print(f"⚠️  CRITICAL FINDING: {results[0].description}")
else:
    print("✅ Authentication properly enforced")
```

### Test 3: Verify Admin Operations Are Blocked
```python
# Attempt to delete another user (STOP IMMEDIATELY IF SUCCESSFUL)
response = requests.delete(
    "https://api.robinhood.com/api/admin/users/other_user_id",
    headers={"Authorization": f"Bearer {test_token}"}
)

# Run the test
results = tester.test_privilege_level_enforcement([
    {
        "operation": "delete_user",
        "user_privilege": "user",
        "response_code": response.status_code,
        "can_execute": response.status_code == 200
    }
])

# Check results
if results:
    print(f"⚠️  CRITICAL FINDING: {results[0].description}")
    print("STOP TESTING - Do not attempt further admin operations")
else:
    print("✅ Privilege levels properly enforced")
```

---

## Expected CVSS Scores

### Data Scope Enforcement Failure
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
Score: 8.2 (High)
Impact: Confidentiality breach - access to other users' data
```

### Authentication Enforcement Failure
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
Score: 9.1 (Critical)
Impact: All impacts - unauthenticated access to all functions
```

### Privilege Escalation
```
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H
Score: 9.1 (Critical)
Impact: Regular user executing admin operations
```

---

## CLI Usage Examples

### Test Individual Endpoints
```bash
python3 testing_scripts.py api.robinhood.com \
  --authorization \
  --verbose
```

### Generate Full Report with Templates
```bash
python3 testing_scripts.py api.robinhood.com \
  --authorization \
  --output auth_report.json \
  --submission-template
```

### Test Everything
```bash
python3 testing_scripts.py api.robinhood.com \
  --all \
  --output complete_report.json \
  --submission-template \
  --verbose
```

---

## Output Format

### JSON Report Structure
```json
{
  "metadata": {
    "timestamp": "2026-01-22T10:35:00Z",
    "target": "api.robinhood.com",
    "compliance": {
      "headers_required": ["X-Bug-Bounty", "X-Test-Account-Email"]
    }
  },
  "summary": {
    "vulnerabilities_found": 3,
    "suspicious_findings": 0
  },
  "vulnerabilities": [
    {
      "category": "authorization",
      "test_name": "data_scope_enforcement_failure",
      "status": "vulnerable",
      "severity": "critical",
      "description": "Endpoint returns data from other users: /api/positions",
      "cvss_score": 8.2,
      "timestamp": "2026-01-22T10:35:00Z"
    }
  ]
}
```

---

## Key Points

### ✅ What This Tests
- Data isolation between users
- Authentication requirement enforcement
- Privilege level boundaries
- Authorization control effectiveness

### ❌ What This Does NOT Do
- Access other users' accounts
- Escalate privileges beyond identification
- Execute admin operations
- Modify data or system state
- Perform DOS attacks

### 🎯 Ethical Boundaries
- Only test YOUR OWN test account
- Verify security WITHOUT exploitation
- Document findings WITHOUT executing them
- Report responsibly to HackerOne

---

## Submission Template for Authorization Findings

```markdown
## Title
[CRITICAL] Authorization: {Vulnerability Type}

## Category
Authorization / Access Control

## Severity
Critical / High

## Description
Regular users can access admin functionalities without proper privilege checks.

## Reproduction Steps
1. Create test Robinhood account
2. Authenticate with test credentials
3. Include X-Bug-Bounty and X-Test-Account-Email headers
4. Attempt restricted operation: {operation}
5. Observe response code: {response_code}

## Expected Behavior
- Regular users should receive 403 Forbidden
- Admin operations should require elevated privileges
- Privilege level should be verified server-side

## Actual Behavior
- Regular users receive 200 OK
- Admin operation succeeds despite insufficient privileges
- No privilege verification on server

## Impact
Privilege escalation allows regular users to:
- Modify account balances
- Delete user accounts
- Disable security features
- Access admin panels

## CVSS v3.1 Vector
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H
Score: 9.1 (Critical)

## Remediation
1. Implement role-based access control
2. Verify privilege level before admin operations
3. Add privilege check middleware
4. Audit log all privileged actions
5. Implement least-privilege principle
```

---

## Next Steps

1. **Run the Tests**
   ```bash
   python3 testing_scripts.py api.robinhood.com --authorization --verbose
   ```

2. **Review Findings**
   - Check JSON report
   - Verify CVSS scores
   - Document evidence

3. **Generate Submission Template**
   ```bash
   python3 testing_scripts.py api.robinhood.com \
     --authorization \
     --submission-template
   ```

4. **Submit to HackerOne**
   - Include X-Bug-Bounty header
   - Include X-Test-Account-Email header
   - Provide exact reproduction steps
   - Include CVSS vector string

---

## Support

- **Framework:** testing_scripts.py
- **Documentation:** ETHICAL_TESTING_ENHANCEMENTS.md
- **Protocol:** ROBINHOOD_PROTOCOL.md
- **Quickstart:** TESTING_QUICKSTART.md

For questions or issues with authorization testing, refer to the main documentation files.
