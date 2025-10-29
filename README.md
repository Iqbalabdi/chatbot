# Chatbot - FastAPI
---

## Components (Modules & Domains)
The source code is organized according to **Domain-Driven Design**:
```
.
├── project/
│   ├── app/
│   │   └── auth/
│   │   └── chat/
├── common/
├── env/
├── tests/
│   │   └── auth/
│   │   └── chat/
└── README.md
```
### 🧱 Domain: `auth`
Handles user authentication and identity verification.

**Modules inside `/app/auth/`:**
| Module | Description |
|--------|-------------|
| `api/` | REST API endpoints for login, token validation, etc. |
| `service/` | Business logic for authentication (token creation, validation). |

**Example endpoints:**
- `POST /auth/login` → authenticate user and issue JWT

---

### 💬 Domain: `chat`
Handles conversation processing, LLM integration, and message storage.

**Modules inside `/app/chat/`:**
| Module | Description |
|--------|-------------|
| `api/` | Chat REST + WebSocket routes for message exchange. |
| `service/` | Core chat logic — handles message flow, calls LLM, updates history. |
| `repository/` | Handles Redis operations for session history (append/get). |
| `adapters/` | Integrates with the LLM provider (Ollama, HuggingFace, etc). |
| `models/` | Pydantic data models (`ChatMessage`, `ChatSession`, etc). |

**Key flow:**
1. Client sends chat message → `api` receives request.  
2. `service` calls `adapters.llm_adapter` to get LLM-generated response.  
3. `repository` stores the session in Redis for future retrieval.  

---

### 🧰 Common Modules
Located in `/common/`, this package contains shared components used across domains.

| Module | Description |
|--------|-------------|
| `config/` | Loads environment variables and configuration (per environment). |
| `clients/` | Initializes external clients like Redis. |
| `exceptions/` | Centralized exception definitions (ChatError, RedisError, etc). |
| `rate_limiter/` | Middleware for API rate limiting. |

---

### 🧪 Common Tests
Located under `/tests/common/`.

| Domain | Purpose |
|--------|----------|
| `auth` | Verifies Auth domain for JWT service. |
| `chat` | Verifies Chat domain for integration to LLM. |

---

## ⚙️ 2. Running the Project

### 🔧 Prerequisites
- Python ≥ 3.11  
- Docker + Docker Compose  
- Redis installed (or run via Docker)

### 🐳 Run with Docker Compose
This will start both Redis and the chat service:

  ```bash
  ENVIRONMENT=stg docker-compose up --build
  ```

### 🧠 Running Locally (Without Docker)
If you have Redis running locally:
- run ollama
  ```
  ollama run gemma3:1b
  ```
- run redis
  ```
  docker run --name redis-local -p 6379:6379 redis
  ```
- run app
  ```export ENVIRONMENT=dev
  uvicorn app.chat.main:app --reload --port 9002
  ```

## 📡 3. Example API Request
- POST /auth/login

  Login to get JWT Token
  Request:
  ```
  curl -X POST http://127.0.0.1:9001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user456"}'
  ```
- POST /chat/message
  
  Send a message to the chatbot and receive a generated response.
  ```
  Request:
  curl -X POST http://127.0.0.1:9002/chat/message \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","message":"Hello, assistant!"}'
  ```
- POST /chat/message?stream=true

  Send a message to the chatbot and receive a streaming response.
  ```
  curl -X POST http://127.0.0.1:9002/chat/message?stream=true \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","message":"Hello, assistant!"}'
  ```

- Websocket /ws

  Talk to backend using websocket
  ```
  websocat ws://localhost:9002/chat/ws
  {"user_id": "user456", "message": "Hello?"}
  {"user_id": "user777", "message": "Hello via WS"}
  ```

### 🧪 4. Testing
Unit tests are written using pytest and pytest-asyncio.
Run all tests
```
pytest -q
```

### ⚙️ 5. CI/CD
CI Steps:
1. Trigger: On push or PR to main or dev
2. Run Tests: Installs deps + runs pytest
3. Upload Coverage Report: Stored in workflow artifacts
4. Build Docker Images: For both Auth & Chat services

### 7. Architecture
<img width="470" height="620" alt="image" src="https://github.com/user-attachments/assets/4922a8c3-e329-4180-9343-10ece2f5e591" />





