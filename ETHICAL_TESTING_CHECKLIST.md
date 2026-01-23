# Ethical Vulnerability Testing Checklist for Robinhood

## Complete Checklist & Testing Guidelines

---

## 1. INFRASTRUCTURE ASSESSMENT

### Pre-Testing
- [ ] Create test account on Robinhood (use your real email)
- [ ] Document your test account email
- [ ] Set HackerOne username in environment
- [ ] Review Robinhood's in-scope targets (Tier 1)
- [ ] Have HackerOne submission ready (don't submit yet)

### Subdomain Enumeration
- [ ] Run subdomain scan on primary domain
- [ ] Run subdomain scan on all subdomains
- [ ] Document all discovered subdomains
- [ ] Check response times (slow responses = potential takeover)
- [ ] Verify DNS records for each subdomain
- [ ] Identify expected vs. unexpected subdomains

**Target Domains:**
```
robinhood.com
api.robinhood.com
nummus.robinhood.com
rhapollo.net
rhinternal.net
robinhood.net
```

### Subdomain Validation
- [ ] Test each subdomain with curl/wget
- [ ] Document HTTP status codes
- [ ] Check for timeout/connection refused (potential orphaned domain)
- [ ] Note any redirect chains
- [ ] Capture response headers
- [ ] Check for certificate information (HTTPS)

### Takeover Detection
- [ ] Look for CNAME records pointing to third-party services
- [ ] Check if third-party service is still active
- [ ] Verify domain registration status
- [ ] Note any "404 Not Found" from CDN/service providers
- [ ] Check for DNS cache issues
- [ ] Document evidence of orphaned DNS

### High-Value Findings (Subdomain)
| Finding | Risk | Bounty | Action |
|---------|------|--------|--------|
| Expired subdomain takeover | Critical | $3k-$10k | Verify ownership, report with proof |
| Dev/staging environment exposed | High | $2k-$8k | Document access, report immediately |
| Internal service accessible | High | $3k-$10k | Test authorization, report |
| Misconfigured DNS | Medium | $1k-$3k | Document configuration, report |
| CloudFront/CDN misconfiguration | High | $2k-$8k | Test access, report |

---

## 2. DEPENDENCY & CVE ASSESSMENT

### Pre-Testing
- [ ] Access NVD database setup
- [ ] Understand CVSS v3.1 scoring
- [ ] Have CVE lookup tools ready
- [ ] Document any found versions

### Version Discovery
- [ ] Check HTTP response headers
  - [ ] `Server` header (reveals framework)
  - [ ] `X-AspNet-Version` (ASP.NET)
  - [ ] `X-Framework` (custom headers)
  - [ ] `X-Powered-By`
  - [ ] `X-Generator`
- [ ] Check error page footers
- [ ] Look for robots.txt comments
- [ ] Check sitemap.xml headers
- [ ] Review JavaScript files for version strings
- [ ] Check META tags in HTML
- [ ] Inspect API response headers

### CVE Lookup
- [ ] Search NVD for framework + version
- [ ] Check for CVSS score > 7.0
- [ ] Verify public exploit exists
- [ ] Check if vulnerability is exploitable remotely
- [ ] Confirm it affects exposed version
- [ ] Document CVE ID and date published

### High-Value Findings (Dependencies)
| Finding | Risk | Bounty | Action |
|---------|------|--------|--------|
| Critical CVE (CVSS 9+) in exposed service | Critical | $3k-$10k | Verify version, document exploitation path, report |
| High CVE (CVSS 7-8.9) in framework | High | $2k-$8k | Verify exploitability, report with proof |
| Multiple outdated dependencies | Medium | $1k-$3k | List all, report with versions |
| Public RCE in framework | Critical | $5k-$25k | Verify and report (carefully!) |

### Exploitation Verification (Ethical)
- [ ] Confirm version matches CVE requirement
- [ ] Check if vulnerability is patched in deployed version
- [ ] Verify exploit is public knowledge
- [ ] Test on non-production endpoint ONLY
- [ ] Stop at proof-of-concept (don't explore further)
- [ ] Document exact payload and response
- [ ] Report immediately

---

## 3. INPUT VALIDATION & FUZZING

### Pre-Testing
- [ ] Create test account
- [ ] Login and capture authenticated cookies/tokens
- [ ] Document all API endpoints you plan to test
- [ ] Note request/response patterns
- [ ] Verify you're testing YOUR data only

### API Endpoint Mapping
- [ ] List all discovered API endpoints
- [ ] Categorize by HTTP method (GET, POST, PUT, DELETE)
- [ ] Identify user ID parameters
- [ ] Identify resource ID parameters
- [ ] Document expected input formats
- [ ] Note authentication requirements

**Common Robinhood API Endpoints:**
```
/api/orders
/api/positions
/api/accounts
/api/portfolio
/api/watchlist
/api/instruments
/api/quotes
/api/news
/api/settings
/api/users
/api/notifications
```

### Input Validation Testing
- [ ] Test SQL injection on all string parameters
- [ ] Test XSS on all text fields
- [ ] Test path traversal on file/path parameters
- [ ] Test type confusion (int vs string)
- [ ] Test boundary conditions (very large/small numbers)
- [ ] Test special characters
- [ ] Test Unicode/encoding bypasses
- [ ] Test null/empty values

### IDOR Testing (Critical)
- [ ] Identify user ID in request (e.g., user_id=123)
- [ ] Test with your own ID (baseline)
- [ ] Increment ID by 1 and test (user_id=124)
- [ ] Try ID from different user (if known)
- [ ] Try sequential enumeration (user_id=1, 2, 3...)
- [ ] Try random high numbers (user_id=999999)
- [ ] Test with negative IDs (user_id=-1)
- [ ] Test with zero (user_id=0)

**⚠️ IMPORTANT:** If you get another user's data, STOP immediately. Log the request/response and report without further exploration.

### High-Value Findings (Input Validation)
| Finding | Risk | Bounty | Action |
|---------|------|--------|--------|
| SQL Injection with data access | Critical | $5k-$25k | Verify, report with payload and response |
| IDOR accessing user data | High | $3k-$10k | Report with 1-2 examples maximum |
| XSS in authenticated context | Medium | $2k-$8k | Report with payload and proof |
| Path Traversal | High | $3k-$10k | Report with file accessed |
| Command Injection | Critical | $5k-$25k | Report carefully (no data exfil) |

### Fuzzing Parameters to Test
```
user_id, account_id, portfolio_id
instrument_id, order_id, position_id
ticker, symbol, isin
quantity, price, amount
start_date, end_date, timestamp
email, username, account_number
ssn, phone, address
api_key, token, session_id
```

---

## 4. AUTHENTICATION & AUTHORIZATION

### Pre-Testing
- [ ] Have test account credentials ready
- [ ] Create second test account if possible (for comparison)
- [ ] Capture authentication tokens/cookies
- [ ] Document session management flow
- [ ] Review OAuth/API key authentication

### Authentication Mechanism Testing
- [ ] Test default credentials on test endpoints
- [ ] Verify password requirements
- [ ] Test weak password acceptance
- [ ] Check if passwords are validated against common lists
- [ ] Test account lockout after failed attempts
- [ ] Verify lockout resets properly
- [ ] Test password reset flow
- [ ] Verify reset tokens are single-use
- [ ] Check if reset tokens are time-bound

### JWT Token Testing (If Used)
- [ ] Decode JWT token (jwt.io, but verify offline)
- [ ] Check token claims (exp, iat, sub, aud)
- [ ] Test if token is valid after expiration
- [ ] Test if signature can be modified
- [ ] Try removing signature
- [ ] Try changing algorithm (HS256 to none)
- [ ] Test key confusion attacks
- [ ] Check if token refresh is secure

### Session Management Testing
- [ ] Capture session cookie
- [ ] Check cookie flags (Secure, HttpOnly, SameSite)
- [ ] Test if session ID is random/unpredictable
- [ ] Test if old sessions are invalidated
- [ ] Test concurrent session handling
- [ ] Verify logout clears session
- [ ] Test if session persists across login/logout
- [ ] Check session timeout behavior

### Authorization Testing
- [ ] Test accessing admin endpoints as regular user
- [ ] Test accessing support tools as regular user
- [ ] Test accessing oak.robinhood.net endpoints
- [ ] Try escalating to higher privilege level
- [ ] Test accessing other users' settings
- [ ] Verify role-based access control
- [ ] Test if permissions are enforced server-side
- [ ] Check for horizontal privilege escalation

**⚠️ CRITICAL:** If you gain admin/support access, STOP immediately. Log the request and report without exploring.

### High-Value Findings (Authentication)
| Finding | Risk | Bounty | Action |
|---------|------|--------|--------|
| Authentication bypass (no credentials needed) | Critical | $5k-$25k | Report with reproduction steps |
| Privilege escalation to admin | Critical | $5k-$25k | Report immediately without exploring |
| JWT signature not verified | High | $3k-$10k | Report with modified token |
| Session fixation | High | $2k-$8k | Report with proof |
| Predictable session IDs | High | $3k-$10k | Report with pattern |
| Account takeover via auth flaw | Critical | $10k-$25k | Report with caution |

---

## 5. BUSINESS LOGIC TESTING

### Pre-Testing
- [ ] Understand normal trade execution flow
- [ ] Document order states (pending, confirmed, filled, rejected)
- [ ] Map API call sequence for trades
- [ ] Note authorization checks at each step
- [ ] Have test account with small balance ($5-10)

### Order Flow Testing
- [ ] Test creating order with insufficient funds
  - [ ] Expected: Rejected
  - [ ] Actual: ?
- [ ] Test creating order after account locked
  - [ ] Expected: Rejected
  - [ ] Actual: ?
- [ ] Test modifying order in flight
  - [ ] Expected: Partial fill or cancel
  - [ ] Actual: ?
- [ ] Test canceling filled order
  - [ ] Expected: Cannot cancel
  - [ ] Actual: ?
- [ ] Test concurrent order placement
  - [ ] Expected: Sequential processing
  - [ ] Actual: ?

### Sequence Bypass Testing
- [ ] Test calling endpoints out of order
- [ ] Test skipping validation steps
- [ ] Test replaying requests
- [ ] Test modifying request between API calls
- [ ] Test parallelizing normally-sequential operations
- [ ] Document any state inconsistencies

### Business Logic Flaws to Look For
- [ ] Bypassing UI restrictions via API
- [ ] Performing operations in wrong order
- [ ] Accessing disabled features
- [ ] Circumventing rate limits
- [ ] Double-spending resources
- [ ] State machine bypass
- [ ] Race condition exploitation
- [ ] Authorization check timing gaps

**⚠️ CRITICAL:** Stay under $1,000 USD in test losses. If approaching limit, STOP and report.

### High-Value Findings (Business Logic)
| Finding | Risk | Bounty | Action |
|---------|------|--------|--------|
| Authorization bypass in trade execution | Critical | $5k-$25k | Report without executing trades |
| Trading without sufficient funds | High | $3k-$10k | Report with proof |
| Rate limit bypass | Medium | $1k-$3k | Report with evidence |
| Sequence bypass in critical flow | High | $3k-$10k | Report with steps |
| State machine inconsistency | High | $2k-$8k | Report with timing |

---

## Post-Testing Checklist

### Before Submitting
- [ ] Review all findings
- [ ] Verify no unauthorized data accessed
- [ ] Calculate CVSS scores (use CVSS calculator)
- [ ] Document exact reproduction steps
- [ ] Take screenshots/video if applicable
- [ ] Prepare JSON report from Lucius
- [ ] Create HackerOne submission template
- [ ] Double-check no sensitive data in report
- [ ] Verify test account email matches HackerOne profile

### Submission Checklist
- [ ] Title is clear and descriptive
- [ ] Summary explains the vulnerability
- [ ] CVSS v3.1 vector string included
- [ ] Affected asset (domain/endpoint) specified
- [ ] Exact reproduction steps provided
- [ ] Proof-of-concept demonstrates impact
- [ ] Impact statement explains damage
- [ ] X-Bug-Bounty header documented
- [ ] X-Test-Account-Email header documented
- [ ] Include Lucius JSON output as supporting evidence

### After Submission
- [ ] Monitor HackerOne dashboard
- [ ] Respond to triage questions
- [ ] Provide additional proof if requested
- [ ] Don't disclose publicly
- [ ] Don't test after submission (unless asked)
- [ ] Track bounty timeline

---

## Critical Rules (Do Not Violate)

❌ **Never:**
- Test accounts you don't own
- Access other users' data beyond proof-of-concept
- Exfiltrate large datasets
- Execute financial transactions (beyond $1k testing)
- Use exploits for personal gain
- Perform DOS attacks
- Share findings publicly
- Social engineer employees
- Disclose before Robinhood patches

✅ **Always:**
- Test your accounts only
- Include required headers
- Stop at vulnerability identification
- Report immediately when found
- Document everything
- Be respectful of systems
- Follow responsible disclosure
- Stay under $1k USD testing limit

---

## Finding Documentation Template

For each vulnerability found, document:

```
VULNERABILITY SUMMARY
- Title: [Clear, descriptive title]
- Type: [IDOR, SQLi, Auth Bypass, etc.]
- Severity: [Critical/High/Medium]
- CVSS Score: [X.X]
- CVSS Vector: [CVSS:3.1/...]

AFFECTED ASSET
- Domain/Endpoint: [api.robinhood.com/orders]
- HTTP Method: [GET/POST/PUT/DELETE]
- Parameters: [user_id, account_id, etc.]

REPRODUCTION STEPS
1. [Step 1]
2. [Step 2]
3. [Step 3]

PROOF OF CONCEPT
- Request: [Exact HTTP request]
- Response: [Actual response showing vulnerability]
- Evidence: [Screenshot/log]

IMPACT
- What can attacker do?
- How many users affected?
- What data is exposed?
- How valuable is the exploit?

REMEDIATION
- What should be fixed?
- How to verify fix?
```

---

## Testing Schedule Recommendation

### Day 1: Infrastructure (4-6 hours)
- Subdomain enumeration
- DNS analysis
- Takeover detection
- Document findings

### Day 2: Dependencies (3-4 hours)
- Version discovery
- CVE lookup
- Exploitation research
- Verify exposure

### Day 3: Input Validation (6-8 hours)
- API endpoint mapping
- Fuzzing payloads
- IDOR testing
- Data validation

### Day 4: Authentication (4-5 hours)
- Token analysis
- Session testing
- Authorization checks
- Privilege escalation

### Day 5: Business Logic (4-6 hours)
- Workflow testing
- Sequence validation
- State machine analysis
- Edge case testing

### Day 6: Analysis & Reporting (3-4 hours)
- Review all findings
- Calculate CVSS scores
- Prepare submissions
- Verify evidence

---

## Success Indicators

You've done good work if:
- ✓ Found at least one valid vulnerability
- ✓ Documented exact reproduction steps
- ✓ Calculated accurate CVSS scores
- ✓ Demonstrated actual impact
- ✓ Never accessed unauthorized data
- ✓ Stayed within $1k testing limit
- ✓ Followed all program rules
- ✓ Prepared professional submissions

---

## Resources

- **Robinhood Program**: https://hackerone.com/robinhood
- **CVSS Calculator**: https://www.first.org/cvss/calculator/3.1
- **NVD Database**: https://nvd.nist.gov/
- **OWASP Testing Guide**: https://owasp.org/www-project-web-security-testing-guide/
- **HackerOne Docs**: https://docs.hackerone.com/

---

Good luck with your ethical security testing!
