
---

# Petrovich Search Service

**High-performance backend service for account verification on petrovich.ru.**
Designed to validate user existence by phone or email while maintaining full session integrity and enterprise-grade reliability. Fully Sfera-compliant and backward-compatible with legacy workflows.

---

## Why This Exists

Petrovich is a Russian home improvement retailer. This service exists to programmatically verify whether user accounts exist without relying on client-side automation or scraping fragile HTML. It’s production-ready, fault-tolerant, and designed for integration with larger SaaS workflows.

---

## Core Capabilities

* Account validation for **phone numbers** and **emails**
* Robust session management and automatic session recovery
* Full Sfera-compliant JSON responses
* High reliability: retries, error classification, and graceful degradation
* Backward-compatible with legacy logic while improving maintainability

---

## Architecture Overview

```
src/
├── api/             # FastAPI endpoints
├── application/     # Orchestrates use cases and workflow logic
├── core/            # Configuration, helpers, and standards
├── domain/          # Business logic, adapters, models
└── infrastructure/  # HTTP clients, session storage, Validator IS integration
main.py              # Service entrypoint
```

**Key Patterns**:

* **Domain-Driven Design**: clear separation between domain logic, application orchestration, and infrastructure concerns
* **Adapters**: PayloadAdapter, SessionAdapter, ResponseAdapter
* **Resiliency**: retry logic, session recreation, and fallback paths
* **Observability**: structured logs, health checks, and error classification

---

## API Endpoints

### `/api/v1/search/validate` – Unified Validator IS Search

* Accepts emails and phone numbers
* Returns Sfera-compliant responses
* Automatic session handling and retries
* Validated payloads only

### `/api/v1/batch-search` – Direct Petrovich Search

* Bypasses Validator IS
* Optimized for bulk requests
* Supports priority processing: phone → email

### `/api/v1/validator-health` & `/api/v1/health`

* Operational monitoring endpoints
* Tracks session count, retries, and validator availability

---

## Response Format

**Success**:

```json
{
  "headers": {"sender":"petrovich","status":"success"},
  "body": {"result":"Найден","result_code":"FOUND","status":"success"},
  "extra": {"service_specific_data":"metadata","timestamp":"2024-01-01T12:00:00Z"}
}
```

**Error**:

```json
{
  "headers": {"sender":"petrovich","status":"error"},
  "body": {"error":"Human-readable message","error_code":"SESSION_BLOCKED","status":"error"},
  "extra": {"exception_type":"SessionBlockedError","timestamp":"2024-01-01T12:00:00Z"}
}
```

Errors are classified and retried according to type (SESSION_BLOCKED, VALIDATOR_UNAVAILABLE, SERVICE_UNAVAILABLE, INVALID_DATA).

---

## Operational Notes

* **Sessions**: In-memory store with configurable retry logic; automatically recreated if blocked
* **Legacy Preservation**: Maintains exact legacy request/response behavior
* **Scalability**: Asynchronous workflows, reusable HTTP clients, modular adapters

---

## Deployment

### Local

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Environment Variables

```env
VALIDATOR_URL=http://your-validator-service/api/v1
SERVICE_NAME=Petrovich_Search_Service
MODE=dev
VERSION_NO=1.0.0
VERSION_NO_VALUE=v1
```

---

## Usage Examples

**Single phone check**:

```bash
curl -X POST "http://localhost:8000/api/v1/validate" \
  -H "Content-Type: application/json" \
  -d '{"query":["79211234567"]}'
```

**Mixed phone & email**:

```bash
curl -X POST "http://localhost:8000/api/v1/validate" \
  -H "Content-Type: application/json" \
  -d '{"query":["email@example.com","79211234567"]}'
```

**Direct Petrovich search**:

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"phone":"79211234567"}'
```

---
