# Lucius Extended Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    LUCIUS FRAMEWORK v2.0                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Reconnaissance  │  │    Fuzzing       │                 │
│  │     Engine       │  │     Engine       │                 │
│  ├──────────────────┤  ├──────────────────┤                 │
│  │                  │  │                  │                 │
│  │ • SubdomainScan  │  │ • SQL Injection  │                 │
│  │ • CVE Lookup     │  │ • XSS            │                 │
│  │ • Auth Testing   │  │ • Path Traversal │                 │
│  │                  │  │ • IDOR           │                 │
│  │                  │  │ • Logic Bypass   │                 │
│  └──────────────────┘  └──────────────────┘                 │
│         │                       │                            │
│         └───────────┬───────────┘                            │
│                     │                                        │
│         ┌───────────▼───────────┐                            │
│         │  ReconOrchestrator    │                            │
│         │  (Coordinator)        │                            │
│         └───────────┬───────────┘                            │
│                     │                                        │
│         ┌───────────▼───────────┐                            │
│         │   CVSS Scorer         │                            │
│         │   Report Generator    │                            │
│         └───────────┬───────────┘                            │
│                     │                                        │
│         ┌───────────▼───────────┐                            │
│         │   JSON Report         │                            │
│         │   Console Summary     │                            │
│         └───────────────────────┘                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘

         External APIs / Services
         ────────────────────────
         • sublist3r (Subdomain enum)
         • NVD API (CVE lookup)
         • HTTP clients (API fuzzing)
```

---

## Data Flow

```
INPUT
  └─ Target Domain
     └─ Config (flags, creds)

PROCESSING
  ├─ SubdomainScanner.scan()
  │  └─ sublist3r | Simulation
  │
  ├─ CVEScanner.scan()
  │  └─ NVD API Queries
  │
  ├─ APIFuzzer.fuzz()
  │  └─ Payload Injection
  │
  ├─ AuthTester.test()
  │  └─ Credential/Token Tests
  │
  └─ CVSSScorer.calculate()
     └─ Severity Classification

OUTPUT
  ├─ ReconReport (aggregated)
  ├─ JSON file (results.json)
  └─ Console summary
```

---

## Class Hierarchy

```python
# Core Framework Classes

class SubdomainResult:
    """Single subdomain discovery result"""
    domain: str
    subdomain: str
    source: str        # "sublist3r" or "simulated"
    timestamp: str


class CVEResult:
    """Single CVE from NVD"""
    cve_id: str
    cvss_score: float
    cvss_vector: str
    severity: str      # CRITICAL, HIGH, MEDIUM, LOW


class APIFuzzResult:
    """Single fuzzing finding"""
    endpoint: str
    vulnerability_type: str  # sql_injection, xss, etc.
    payload: str
    status_code: int


class AuthTestResult:
    """Single authentication test outcome"""
    test_name: str
    passed: bool
    severity: str
    details: str


class ReconReport:
    """Aggregated findings report"""
    target: str
    subdomains: List[SubdomainResult]
    cves: List[CVEResult]
    api_fuzz_results: List[APIFuzzResult]
    auth_test_results: List[AuthTestResult]
    metadata: Dict
    
    def save_json(filepath: str) -> None
    def print_summary() -> None


# Scanning Engines

class SubdomainScanner:
    """Enumerate subdomains using sublist3r or simulation"""
    
    def scan(domain: str, dry_run: bool) -> List[SubdomainResult]
    def _simulate_scan(domain: str) -> List[SubdomainResult]


class CVEScanner:
    """Query NVD API for CVE information"""
    
    def scan(keywords: List[str], dry_run: bool) -> List[CVEResult]
    def _simulate_cve_scan(keywords: List[str]) -> List[CVEResult]


class APIFuzzer:
    """Fuzz API endpoints with payloads"""
    
    def fuzz(base_url: str, endpoints: List[str]) -> List[APIFuzzResult]
    def _simulate_fuzz(base_url: str, endpoints: List[str]) -> List[APIFuzzResult]


class AuthTester:
    """Test authentication/authorization mechanisms"""
    
    def test(base_url: str, username: str, password: str) -> List[AuthTestResult]
    def _test_default_credentials(base_url: str) -> None
    def _test_jwt_validation(base_url: str) -> None
    def _test_session_fixation(base_url: str) -> None
    def _test_auth_bypass(base_url: str) -> None


class CVSSScorer:
    """Calculate CVSSv3.1 scores"""
    
    def calculate(
        attack_vector: str,
        attack_complexity: str,
        privileges_required: str,
        user_interaction: str,
        scope: str,
        confidentiality: str,
        integrity: str,
        availability: str
    ) -> Dict[str, Any]


# Orchestrator & Config

class ReconConfig:
    """Configuration for all scanning operations"""
    target: str
    enable_subdomain_scan: bool
    enable_cve_lookup: bool
    enable_api_fuzz: bool
    enable_auth_test: bool
    auth_username: Optional[str]
    auth_password: Optional[str]
    # ... other settings


class ReconOrchestrator:
    """Coordinates all scanning engines"""
    
    def __init__(config: ReconConfig) -> None
    def validate_target() -> bool
    def run() -> bool
        # Orchestrates: subdomains → CVEs → API fuzz → auth tests
        # Aggregates into ReconReport
```

---

## Payload Categories

### SQL Injection
```
' OR '1'='1
'; DROP TABLE users; --
1 UNION SELECT NULL,NULL,NULL --
```

### XSS (Cross-Site Scripting)
```
<script>alert('XSS')</script>
javascript:alert('XSS')
"><svg/onload=alert(1)>
```

### Path Traversal
```
../../../etc/passwd
....//....//....//etc/passwd
%2e%2e%2f%2e%2e%2fetc%2fpasswd
```

### IDOR (Insecure Direct Object References)
```
?id=999999
?user_id=1
?account_id=admin
```

### Logic Bypass
```
?admin=true
&role=administrator
?authorized=1
```

---

## CVSS v3.1 Metrics

### Attack Vector (AV)
- N = Network (0.85)
- A = Adjacent (0.62)
- L = Local (0.55)
- P = Physical (0.2)

### Attack Complexity (AC)
- L = Low (0.77)
- H = High (0.44)

### Privileges Required (PR)
- N = None (0.85)
- L = Low (0.62 / 0.68 if scope changed)
- H = High (0.27 / 0.50 if scope changed)

### User Interaction (UI)
- N = None (0.85)
- R = Required (0.62)

### Scope (S)
- U = Unchanged (1.0x multiplier)
- C = Changed (1.08x multiplier)

### Impact Metrics (C, I, A)
- H = High (0.56)
- L = Low (0.22)
- N = None (0.0)

### Severity Mapping
- 9.0–10.0: CRITICAL
- 7.0–8.9: HIGH
- 4.0–6.9: MEDIUM
- 0.1–3.9: LOW
- 0.0: NONE

---

## NVD API Integration

### Endpoint
```
https://services.nvd.nist.gov/rest/json/cves/2.0
```

### Parameters
```json
{
  "keywordSearch": "robinhood",
  "resultsPerPage": 20
}
```

### Response Schema
```json
{
  "vulnerabilities": [
    {
      "cve": {
        "id": "CVE-2024-XXXX",
        "descriptions": [
          {
            "value": "Description..."
          }
        ],
        "published": "2024-01-15",
        "metrics": {
          "cvssMetricV31": [
            {
              "cvssData": {
                "baseScore": 9.8,
                "vectorString": "CVSS:3.1/AV:N/...",
                "baseSeverity": "CRITICAL"
              }
            }
          ]
        }
      }
    }
  ]
}
```

---

## CLI Argument Parser

```python
parser.add_argument("target", help="Target domain")
parser.add_argument("-o, --output", help="Output JSON file")
parser.add_argument("-v, --verbose", help="Debug logging")
parser.add_argument("--dry-run", help="Simulation mode")
parser.add_argument("--no-subdomains", help="Skip subdomain scan")

# Advanced Flags
parser.add_argument("--enable-cve", help="CVE lookup")
parser.add_argument("--enable-fuzz", help="API fuzzing")
parser.add_argument("--enable-auth", help="Auth testing")
parser.add_argument("--auth-user", help="Test username")
parser.add_argument("--auth-pass", help="Test password")
```

---

## File Structure

```
lucius/
├── script.py                      [1068 lines] Main framework
├── requirements.txt               Dependencies
├── QUICK_REFERENCE.md             [This quick guide]
├── LUCIUS_EXTENDED.md             [Full documentation]
├── IMPLEMENTATION_SUMMARY.md       [Technical details]
├── robinhood_quickstart.py         [Interactive guide]
└── check_syntax.py                [Validation helper]
```

---

## Dependencies

```
sublist3r>=1.0.0                  # Subdomain enumeration
sqlmap>=1.7.0                     # SQL injection testing
requests>=2.31.0                  # HTTP client (NVD, API fuzzing)
```

### Python Version
- **Minimum**: 3.8
- **Tested**: 3.11
- **Features**: Type hints, dataclasses, async support

---

## Integration Points

### External APIs
- **NVD**: CVE lookup (rate-limited)
- **sublist3r**: Subdomain enumeration (multiple search engines)

### Internal Modules
- **logging**: Structured logging with levels
- **json**: Report serialization
- **dataclasses**: Type-safe data models
- **requests**: HTTP requests
- **argparse**: CLI argument parsing

---

## Performance Metrics

| Operation | Timeout | Throughput |
|-----------|---------|-----------|
| Subdomain Scan | 30s | 5–100 subdomains |
| CVE Lookup | 30s | 1 keyword/second |
| API Fuzzing | 10s per endpoint | ~50 payloads |
| Auth Testing | 10s per test | 4+ tests |
| Report Generation | <1s | Instant |

---

## Error Handling

All modules implement graceful fallbacks:
- **SubdomainScanner**: Falls back to simulation
- **CVEScanner**: Skips on API failure
- **APIFuzzer**: Continues on request errors
- **AuthTester**: Reports test skip if unreachable
- **Orchestrator**: Returns partial results on failure

---

## Security Considerations

✓ **Implemented**
- Rate limiting (NVD API)
- Request timeouts
- Error message filtering (no credential exposure)
- Graceful degradation
- Fallback simulation mode

⚠️ **User Responsibility**
- Test only authorized targets
- Use test accounts for auth testing
- Avoid sensitive data capture
- Review payloads before fuzzing
- Follow program rules (Robinhood)

---

## Future Enhancement Roadmap

- [ ] Shodan integration for asset discovery
- [ ] GraphQL introspection
- [ ] JWT algorithm downgrade tests
- [ ] Mobile app analysis
- [ ] Webhook payload interception
- [ ] ML-based anomaly detection
- [ ] Concurrent scanning (thread pool)
- [ ] Proxy support for internal networks
- [ ] Custom payload templates
- [ ] Elasticsearch result storage

---

**Lucius Extended** — Ethical Security Reconnaissance Framework v2.0
