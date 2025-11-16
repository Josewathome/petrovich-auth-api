
# Petrovich Search Service

## Overview

Petrovich is a web scraping service that checks user account existence on **petrovich.ru** - a Russian home improvement and construction materials retailer. The service validates whether phone numbers, emails, or usernames are registered in Petrovich's customer database.

## Core Functionality

- **Account Validation**: Checks if user accounts exist on petrovich.ru
- **Multiple Identifiers**: Supports phone numbers, email addresses, and usernames
- **Session Management**: Maintains authenticated sessions with the target website
- **Sfera Integration**: Returns standardized responses following Sfera guidelines

## Supported Search Types

| Input Type | API Type | Description | Example |
|------------|----------|-------------|----------|
| `phone` | `phone` | Russian phone numbers (7XXXXXXXXXX) | eg. 79211234567 |
| `email` | `email` | Email addresses | eg. email@email.com |
| `nick` | `login` | Usernames (mapped to "login" in API) | eg. username101 |

## Project Structure  for more informaton check the program_tree.txt

```
petrovich-search-service/
├── src/
│   ├── api/                    # FastAPI endpoints
│   │   ├── common.py          # Common controller (Validator IS integration)
│   │   └── petrovich.py       # Direct Petrovich endpoints
│   ├── application/           # Application layer (use cases)
│   │   └── services.py        # PetrovichSearchService orchestration
│   ├── core/                  # Core domain abstractions
│   │   ├── config.py          # Application settings
│   │   └── response_helper.py # Sfera response formatting
│   ├── domain/                # Domain layer (business logic)
│   │   ├── exceptions.py      # Domain-specific exceptions
│   │   ├── models.py          # Domain models (SearchType, SessionData)
│   │   └── services.py        # Domain services (adapters, parsers)
│   └── infrastructure/        # Infrastructure layer
│       ├── http_client.py     # Petrovich API HTTP client
│       ├── session_store.py   # In-memory session storage
│       └── validator_client.py # Validator IS integration
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
└── .env                       # Environment configuration
```

## Key Components

### Domain Layer
- **PayloadAdapter**: Detects and validates search types
- **SessionAdapter**: Handles session cookie management  
- **ResponseAdapter**: Parses Petrovich API responses
- **Domain Models**: SearchType, SessionData, SearchResult

### Application Layer
- **PetrovichSearchService**: Orchestrates the search workflow
- Session retry logic with configurable attempts
- Error handling and response formatting

### Infrastructure Layer
- **PetrovichHTTPClient**: HTTP communication with Petrovich API
- **ValidatorHTTPClient**: Integration with Validator IS
- **InMemorySessionStore**: Session persistence (replaces MongoDB)

### API Layer
- **Common Controller**: `/api/v1/search/validate` - Validator IS integration
- **Petrovich Service**: `/api/v1/search` - Direct searches
- Health checks and monitoring endpoints

## API Response Format

All responses follow Sfera standard:
```json
{
  "headers": {
    "sender": "petrovich",
    "status": "success|error"
  },
  "body": {
    "result": "Найден|Не найден",
    "result_code": "FOUND|NOT_FOUND", 
    "status": "success"
  },
  "extra": {
    "search_details": "additional_info"
  }
}
```

## Legacy Preservation

This service faithfully preserves the original legacy logic:
- Exact same session management flow
- Identical request/response parsing
- Same error handling strategies  
- Maintains all business rules from the original system

The refactoring focuses on architectural improvements while maintaining 100% behavioral compatibility with the legacy Petrovich scraping system.


# ⚙️ Running the Service

## Start with Uvicorn (local)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

# 🐳 Running with Docker (recommended for stability)

## Development

```bash
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up
# or detached:
docker-compose -f docker-compose.dev.yml up -d
```

## Production

```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up
# or detached:
docker-compose -f docker-compose.prod.yml up -d
```

---

# 💻 Local Installation

1. Create virtual environment
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Provide `.env` file
4. Start the server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

# 🔐 Environment Variables

Create `.env`, `.env.dev`, or `.env.prod`:

```env
VALIDATOR_URL=http://your-validator-service/api/v1
SERVICE_NAME=Avito_Search_API
MODE=dev
VERSION_NO=1.0.0
VERSION_NO_VALUE=v1
```

---

## Base Information
- **Base URL**: `http://localhost:8000` (development)
- **Content-Type**: `application/json`
- **Response Format**: Sfera-compliant format

---

## 1. Common Controller Endpoints

### 1.0  Check status
**Endpoint**: GET /health

**Response**:
```json
{
  "status": "healthy",
  "service": "petrovich_auth_api",
  "version": "v1.0.0"
}

```

### 1.1 Validate and Search
**Endpoint**: `POST /api/v1/search/validate`

**Description**: Validates input queries using Validator IS and searches across all available services. Returns unified Sfera-compliant responses.

**Request**:
```http
POST /api/v1/validate
Content-Type: application/json
```

**Request Body**:
```json
{
  "query": [
    "email@example.com",
    "79211234567",
    "username123"
  ]
}
```

**Response**:
```json
[
  {
    "headers": {
      "sender": "petrovich",
      "status": "success",
      "processed_at": "2024-01-01T12:00:00Z"
    },
    "body": {
      "result": "Найден",
      "result_code": "FOUND",
      "status": "success"
    },
    "extra": {
      "raw_data": {
        "state": {"code": 200, "title": "Запрос успешно выполнен"},
        "data": {"isUsed": true, "type": "email"}
      },
      "search_type": "email",
      "searched_value": "email@example.com",
      "session_retries": 0,
      "validator_used": true
    }
  },
  {
    "headers": {
      "sender": "petrovich",
      "status": "success",
      "processed_at": "2024-01-01T12:00:01Z"
    },
    "body": {
      "result": "Не найден",
      "result_code": "NOT_FOUND",
      "status": "success"
    },
    "extra": {
      "raw_data": {
        "state": {"code": 200, "title": "Запрос успешно выполнен"},
        "data": {"isUsed": false, "type": "phone"}
      },
      "search_type": "phone",
      "searched_value": "79211234567",
      "session_retries": 0,
      "validator_used": true
    }
  },
  {
    "headers": {
      "sender": "petrovich",
      "status": "error",
      "processed_at": "2024-01-01T12:00:02Z"
    },
    "body": {
      "error": "No valid search type found in payload",
      "error_code": "INVALID_DATA",
      "status": "error"
    },
    "extra": {
      "original_query": "username123",
      "validator_failed": false,
      "fallback_used": false,
      "exception_type": "InvalidDataError"
    }
  }
]
```

**Error Responses**:
```json
{
  "headers": {
    "sender": "petrovich",
    "status": "error",
    "processed_at": "2024-01-01T12:00:00Z"
  },
  "body": {
    "error": "Validation service unavailable",
    "error_code": "VALIDATOR_UNAVAILABLE",
    "status": "error",
    "fallback_used": true
  },
  "extra": {
    "details": {
      "original_queries": ["email@example.com", "79211234567"]
    },
    "original_error": "Failed to connect to Validator IS after 3 attempts",
    "exception_type": "ServiceUnavailableError"
  }
}
```

---

### 1.2 Batch Search
**Endpoint**: `POST /api/v1/batch-search`

**Description**: Direct batch search with pre-validated payloads. Bypasses Validator IS for direct service invocation.

**Request**:
```http
POST /api/v1/batch-search
Content-Type: application/json
```

**Request Body**:
```json
{
  "data": [
    {
      "phone": "79211234567"
    },
    {
      "email": "email@example.com"
    },
    {
      "nick": "username123"
    }
  ]
}
```

**Response**:
```json
[
  {
    "headers": {
      "sender": "petrovich",
      "status": "success"
    },
    "body": {
      "result": "Найден",
      "result_code": "FOUND",
      "status": "success"
    },
    "extra": {
      "payload": {"phone": "79211234567"},
      "search_attempted": true,
      "search_retries": 0
    }
  },
  {
    "headers": {
      "sender": "petrovich",
      "status": "success"
    },
    "body": {
      "result": "Не найден",
      "result_code": "NOT_FOUND",
      "status": "success"
    },
    "extra": {
      "payload": {"email": "email@example.com"},
      "search_attempted": true,
      "search_retries": 1
    }
  }
]
```

---

### 1.3 Validator Health Check
**Endpoint**: `GET /api/v1/validator-health`

**Description**: Checks connectivity and health status of the Validator IS integration.

**Request**:
```http
GET /api/v1/validator-health
```

**Response**:
```json
{
  "headers": {
    "sender": "petrovich",
    "status": "success"
  },
  "body": {
    "validator_status": "healthy",
    "test_query_processed": true,
    "results_count": 1,
    "status": "success"
  },
  "extra": {
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**Error Response**:
```json
{
  "headers": {
    "sender": "petrovich",
    "status": "error"
  },
  "body": {
    "error": "Failed to connect to Validator IS after 3 attempts",
    "error_code": "SERVICE_UNAVAILABLE",
    "status": "error"
  },
  "extra": {
    "details": {
      "error": "Cannot connect to host validator-service:80 ssl:False [Name or service not known]",
      "max_retries": 3
    },
    "exception_type": "ServiceUnavailableError"
  }
}
```

---

## 2. Petrovich Service Endpoints

### 2.1 Direct Petrovich Search
**Endpoint**: `POST /api/v1/search`

**Description**: Direct search against Petrovich.ru service with explicit payload types.

**Request**:
```http
POST /api/v1/search
Content-Type: application/json
```

**Request Body**:
```json
{
  "phone": "79211234567",
  "email": "email@example.com", 
  "nick": "username123"
}
```

**Note**: Only one field should be provided per request. If multiple fields are provided, they are processed in priority order: phone → email → nick.

**Response**:
```json
{
  "headers": {
    "sender": "petrovich",
    "status": "success"
  },
  "body": {
    "result": "Найден",
    "result_code": "FOUND",
    "status": "success"
  },
  "extra": {
    "raw_data": {
      "state": {"code": 200, "title": "Запрос успешно выполнен"},
      "data": {"isUsed": true, "type": "phone"}
    },
    "search_type": "phone",
    "searched_value": "79211234567",
    "session_retries": 0,
    "session_recreated": false
  }
}
```

**Error Response**:
```json
{
  "headers": {
    "sender": "petrovich",
    "status": "error"
  },
  "body": {
    "error": "Session blocked and max retries exceeded",
    "error_code": "SESSION_BLOCKED",
    "status": "error"
  },
  "extra": {
    "payload": {"phone": "79211234567"},
    "search_attempted": true,
    "search_retries": 3,
    "exception_type": "SessionBlockedError"
  }
}
```

---

### 2.2 Petrovich Health Check
**Endpoint**: `GET /api/v1/health`

**Description**: Health check for the Petrovich service including session management.

**Request**:
```http
GET /api/v1/health
```

**Response**:
```json
{
  "headers": {
    "sender": "petrovich",
    "status": "success"
  },
  "body": {
    "service": "petrovich",
    "status": "healthy",
    "session_count": 1,
    "status": "success"
  },
  "extra": {
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

## 3. Root Endpoints

### 3.1 API Root
**Endpoint**: `GET /`

**Description**: Basic API information and welcome message.

**Request**:
```http
GET /
```

**Response**:
```json
{
  "message": "Petrovich Search Service API",
  "version": "1.0.0",
  "endpoints": {
    
  }
}
```

---

### 3.2 Global Health Check
**Endpoint**: `GET /health`

**Description**: Overall service health status.

**Request**:
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "petrovich-search-service",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Error Response Standard Format

All error responses follow this format:

```json
{
  "headers": {
    "sender": "petrovich",
    "status": "error"
  },
  "body": {
    "error": "Human readable error message",
    "error_code": "ERROR_CODE_IN_UPPERCASE",
    "status": "error"
  },
  "extra": {
    "details": {
      "additional_info": "contextual data"
    },
    "exception_type": "ExceptionClassName",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Common Error Codes:
- `VALIDATOR_UNAVAILABLE` - Validator IS service unavailable
- `SESSION_BLOCKED` - Session blocked by target service
- `SESSION_CREATION_FAILED` - Failed to create new session
- `INVALID_DATA` - Invalid input data format
- `SEARCH_FAILED` - Search operation failed
- `SOURCE_PARSE_ERROR` - Failed to parse source response
- `SERVICE_UNAVAILABLE` - External service unavailable
- `INTERNAL_ERROR` - Internal server error

---

## Success Response Standard Format

All success responses follow this format:

```json
{
  "headers": {
    "sender": "petrovich",
    "status": "success"
  },
  "body": {
    "result": "Найден|Не найден",
    "result_code": "FOUND|NOT_FOUND",
    "status": "success"
  },
  "extra": {
    "service_specific_data": "additional information",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

## Usage Examples

### Example 1: Single Phone Search
```bash
curl -X POST "http://localhost:8000/api/v1/validate" \
  -H "Content-Type: application/json" \
  -d '{"query": ["79211234567"]}'
```

### Example 2: Mixed Data Types
```bash
curl -X POST "http://localhost:8000/api/v1/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": [
      "email@example.com",
      "79211234567", 
      "testuser",
      "invalid@data"
    ]
  }'
```

### Example 3: Direct Petrovich Search
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"phone": "79211234567"}'
```

### Example 4: Health Check
```bash
curl "http://localhost:8000/health"
```