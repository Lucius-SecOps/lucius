# Lucius Operations Platform

A microservices architecture for vulnerability management, threat intelligence, and nonprofit grant operations.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Lucius Operations Platform                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │  Sentinel   │───▶│    Talon    │◀───│      Operations         │ │
│  │  (Scanner)  │    │   (API)     │    │   (Grant Management)    │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│        │                  │                       │                 │
│        ▼                  ▼                       ▼                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │  NVD API    │    │ PostgreSQL  │    │   Nonprofit Data        │ │
│  │             │    │   Redis     │    │   Grant Pipeline        │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Services

### Sentinel - Vulnerability Scanner
- Scans dependency manifests (package-lock.json, requirements.txt, composer.lock)
- Queries NVD API for vulnerability data
- Generates SBOM in CycloneDX and SPDX formats
- Reports findings to Talon for aggregation

### Talon - Threat Intelligence Hub
- REST API for vulnerability management
- ML-based threat scoring
- Multi-channel notifications (Email, SMS, Slack)
- Background task processing with Celery

### Operations - Grant Management
- Grant pipeline tracking
- Deadline monitoring with SMS alerts
- Nonprofit data cleaning and enrichment
- Milestone management

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

## 🛠️ Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/lucius.git
cd lucius
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start with Docker Compose

```bash
docker compose up -d
```

### 3. Initialize Database

```bash
docker compose exec postgres psql -U lucius -d lucius -f /docker-entrypoint-initdb.d/init.sql
```

### 4. Access Services

- **Talon API**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

## 🔧 Development Setup

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows
```

### Install Dependencies

```bash
pip install -e ".[dev]"
# Or install individual services:
pip install -r sentinel/requirements.txt
pip install -r talon/requirements.txt
pip install -r operations/requirements.txt
```

### Run Tests

```bash
pytest tests/ -v --cov
```

### Run Linting

```bash
ruff check .
black --check .
mypy sentinel talon operations shared
```

## 📁 Project Structure

```
lucius/
├── sentinel/                 # Vulnerability Scanner
│   ├── cli.py               # Command-line interface
│   ├── scanner.py           # Core scanning logic
│   ├── parsers.py           # Dependency file parsers
│   ├── nvd_client.py        # NVD API integration
│   ├── sbom.py              # SBOM generation
│   └── talon_client.py      # Talon API client
│
├── talon/                    # Threat Intelligence API
│   ├── app.py               # Flask application factory
│   ├── celery_app.py        # Celery configuration
│   ├── models.py            # SQLAlchemy models
│   ├── api/                 # REST API endpoints
│   │   ├── scans.py
│   │   ├── vulnerabilities.py
│   │   └── notifications.py
│   ├── services/            # Business logic
│   │   ├── scan_service.py
│   │   ├── notification_service.py
│   │   └── threat_scoring.py
│   └── tasks/               # Celery background tasks
│
├── operations/               # Grant Management
│   ├── cli.py               # Command-line interface
│   ├── models.py            # Database models
│   └── services/
│       ├── grant_service.py
│       ├── deadline_monitor.py
│       └── data_cleaner.py
│
├── shared/                   # Shared utilities
│   ├── logging.py           # Structured logging
│   └── types.py             # Common type definitions
│
├── tests/                    # Test suite
├── scripts/                  # Utility scripts
│   └── init-db.sql          # Database initialization
│
├── .github/workflows/        # CI/CD pipelines
├── docker-compose.yml        # Container orchestration
└── pyproject.toml           # Project configuration
```

## 🔐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `NVD_API_KEY` | NVD API key for vulnerability data | Required |
| `SECRET_KEY` | Flask secret key | Required |
| `TWILIO_ACCOUNT_SID` | Twilio account for SMS | Optional |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | Optional |
| `SMTP_HOST` | Email server host | Optional |

## 🔄 Design Patterns

- **Repository Pattern**: Data access abstraction in services
- **Service Layer**: Business logic encapsulation
- **Factory Pattern**: Parser selection based on file type
- **Strategy Pattern**: Notification channel dispatching
- **Observer Pattern**: Event-driven notifications

## 📊 API Endpoints

### Talon API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scans` | Submit scan results |
| `GET` | `/api/scans/{id}` | Get scan details |
| `GET` | `/api/vulnerabilities` | List vulnerabilities |
| `POST` | `/api/notifications` | Send notification |
| `GET` | `/health` | Health check |

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov --cov-report=html

# Run specific service tests
pytest tests/sentinel/ -v
pytest tests/talon/ -v
pytest tests/operations/ -v
```

## 📦 Docker Images

Build images:
```bash
docker build -f sentinel/Dockerfile -t lucius/sentinel .
docker build -f talon/Dockerfile -t lucius/talon .
docker build -f operations/Dockerfile -t lucius/operations .
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
