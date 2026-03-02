# API Endpoints Documentation - Complete Reference

Base URL: `http://localhost:8000`

---

## Table of Contents

1. [Health & Root Endpoints](#health--root-endpoints)
2. [Authentication](#authentication-auth)
3. [Repositories](#repositories-repos)
4. [Chat](#chat-chat)

---

## Health & Root Endpoints

### GET `/`

**Purpose:** Root endpoint that returns API information

**Authentication:** Not required

**Request:**
```
GET /
```

**Headers:** None required

**Response (200 OK):**
```json
{
  "message": "Codebase RAG API",
  "docs": "/docs"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| message | string | API name/description |
| docs | string | URL to Swagger documentation |

---

### GET `/health`

**Purpose:** Health check endpoint for monitoring

**Authentication:** Not required

**Request:**
```
GET /health
```

**Headers:** None required

**Response (200 OK):**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| status | string | Current health status |
| version | string | API version |

---

## Authentication (`/auth`)

### POST `/auth/register`

**Purpose:** Register a new user account

**Authentication:** Not required

**Request:**
```
POST /auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Request Body Fields:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| name | string | Yes | User's display name | Min 1 character |
| email | string | Yes | User's email address | Must be valid email format |
| password | string | Yes | User's password | No validation (recommend min 8 chars) |

**Success Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDdmMWY3N2JjZjg2Y2Q3OTk0MzkwMTEiLCJlbWFpbCI6ImpvaG5AZXhhbXBsZS5jb20iLCJpYXQiOjE3MDU3NjgwMDAsImV4cCI6MTcwNjM3MjYwMH0.dGVzdF90b2tlbl9zaWduYXR1cmU",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00.123456"
  }
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| access_token | string | JWT token for authentication |
| token_type | string | Always "bearer" |
| user.id | string | MongoDB ObjectId as string |
| user.name | string | User's display name |
| user.email | string | User's email |
| user.created_at | string | ISO 8601 datetime |

**Error Responses:**

- **400 Bad Request** - Email already registered:
```json
{
  "detail": "Email already registered"
}
```

- **422 Unprocessable Entity** - Invalid email format:
```json
{
  "detail": [
    {
      "type": "email_parsing",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "notanemail"
    }
  ]
}
```

---

### POST `/auth/login`

**Purpose:** Authenticate user and get access token

**Authentication:** Not required

**Request:**
```
POST /auth/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Request Body Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's registered email |
| password | string | Yes | User's password |

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDdmMWY3N2JjZjg2Y2Q3OTk0MzkwMTEiLCJlbWFpbCI6ImpvaG5AZXhhbXBsZS5jb20iLCJpYXQiOjE3MDU3NjgwMDAsImV4cCI6MTcwNjM3MjYwMH0.dGVzdF90b2tlbl9zaWduYXR1cmU",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00.123456"
  }
}
```

**Error Responses:**

- **400 Bad Request** - Invalid email:
```json
{
  "detail": "Invalid email"
}
```

- **400 Bad Request** - Invalid password:
```json
{
  "detail": "Invalid password"
}
```

---

### POST `/auth/logout`

**Purpose:** Logout endpoint (token handling is client-side)

**Authentication:** Required

**Request:**
```
POST /auth/logout
Authorization: Bearer <access_token>
```

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token from login/register |

**Success Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

**Note:** This endpoint simply confirms logout. The client should delete the token from storage. JWT tokens don't need server-side invalidation.

---

## Repositories (`/repos`)

### POST `/repos/ingest`

**Purpose:** Start ingesting (cloning, parsing, embedding) a GitHub repository

**Authentication:** Required

**Request:**
```
POST /repos/ingest
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token |
| Content-Type | Yes | Must be "application/json" |

**Request Body:**
```json
{
  "repo_url": "https://github.com/facebook/react"
}
```

**Request Body Fields:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| repo_url | string | Yes | Full GitHub repository URL | Must start with "https://github.com/" |

**Success Response (201 Created):**
```json
{
  "repo_id": "507f1f77bcf86cd799439011",
  "task_id": "abc123def456ghi789",
  "status": "queued"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| repo_id | string | MongoDB ObjectId of the created repo document |
| task_id | string | Celery task ID for tracking progress |
| status | string | Initial status (always "queued") |

**Error Responses:**

- **400 Bad Request** - Invalid GitHub URL:
```json
{
  "detail": "Invalid GitHub URL"
}
```

- **400 Bad Request** - Already ingested:
```json
{
  "detail": "Repository already ingested"
}
```

- **401 Unauthorized** - Missing/invalid token:
```json
{
  "detail": "Authentication failed"
}
```

- **422 Unprocessable Entity** - Missing field:
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "repo_url"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

**Workflow After Calling This Endpoint:**

1. You receive `repo_id` and `task_id`
2. Poll `GET /repos/status/{repo_id}` every 2-3 seconds
3. Processing stages: queued → cloning → parsing → embedding → ready
4. When `status` becomes "ready" or "failed", processing is complete

---

### GET `/repos/status/{repo_id}`

**Purpose:** Check the ingestion/processing status of a repository

**Authentication:** Required

**Request:**
```
GET /repos/status/{repo_id}
Authorization: Bearer <access_token>
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| repo_id | string | Yes | The repository ID from `/repos/ingest` response |

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token |

**Success Response (200 OK):**
```json
{
  "task_id": "abc123def456ghi789",
  "celery_state": "SUCCESS",
  "repo_status": "ready",
  "file_count": 247,
  "chunk_count": 1523,
  "error": null
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| task_id | string | Celery task ID |
| celery_state | string | Celery task state: PENDING, STARTED, SUCCESS, FAILURE, RETRY |
| repo_status | string | Application status: queued, cloning, parsing, embedding, ready, failed |
| file_count | number | Number of files processed |
| chunk_count | number | Number of code chunks embedded in vector DB |
| error | string \| null | Error message if failed, null otherwise |

**repo_status Values:**
| Status | Description |
|--------|-------------|
| queued | Waiting in queue for processing |
| cloning | Currently cloning the GitHub repository |
| parsing | Parsing files and extracting code chunks |
| embedding | Creating vector embeddings for code chunks |
| ready | Successfully processed and indexed |
| failed | Processing failed (check error field) |

**Error Responses:**

- **404 Not Found** - Repository not found or doesn't belong to user:
```json
{
  "detail": "Repo not found"
}
```

- **401 Unauthorized** - Invalid token:
```json
{
  "detail": "Invalid or expired token"
}
```

---

### GET `/repos/`

**Purpose:** Get all repositories ingested by the current user

**Authentication:** Required

**Request:**
```
GET /repos/
Authorization: Bearer <access_token>
```

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token |

**Query Parameters:** None

**Success Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "user_id": "507f1f77bcf86cd799439011",
    "repo_url": "https://github.com/facebook/react",
    "repo_name": "react",
    "status": "ready",
    "file_count": 247,
    "chunk_count": 1523,
    "error": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "task_id": "abc123def456ghi789"
  },
  {
    "_id": "607f1f77bcf86cd799439022",
    "user_id": "507f1f77bcf86cd799439011",
    "repo_url": "https://github.com/vuejs/vue",
    "repo_name": "vue",
    "status": "parsing",
    "file_count": 45,
    "chunk_count": 0,
    "error": null,
    "created_at": "2024-01-16T12:00:00.123456",
    "task_id": "xyz789abc456def123"
  }
]
```

**Response Fields (Array of Objects):**
| Field | Type | Description |
|-------|------|-------------|
| _id | string | MongoDB ObjectId as string |
| user_id | string | Owner's user ID |
| repo_url | string | Full GitHub URL |
| repo_name | string | Repository name (last part of URL) |
| status | string | Current processing status |
| file_count | number | Number of files processed |
| chunk_count | number | Number of code chunks |
| error | string \| null | Error message if failed |
| created_at | string | ISO 8601 datetime |
| task_id | string | Celery task ID |

**Error Responses:**

- **401 Unauthorized** - Invalid token:
```json
{
  "detail": "Authentication failed"
}
```

---

### DELETE `/repos/{repo_id}`

**Purpose:** Delete a repository and all its associated data from the system

**Authentication:** Required

**Request:**
```
DELETE /repos/{repo_id}
Authorization: Bearer <access_token>
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| repo_id | string | Yes | The repository ID to delete |

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token |

**Success Response (200 OK):**
```json
{
  "message": "Repository deleted successfully"
}
```

**This endpoint performs:**
1. Deletes all vector embeddings from Qdrant for this repo
2. Deletes the MongoDB document

**Error Responses:**

- **404 Not Found** - Repository not found or doesn't belong to user:
```json
{
  "detail": "Repo not found"
}
```

- **401 Unauthorized** - Invalid token:
```json
{
  "detail": "Invalid or expired token"
}
```

---

## Chat (`/chat`)

### POST `/chat/query`

**Purpose:** Ask questions about a repository using AI. The system searches the embedded code chunks and uses LLM to generate an answer.

**Authentication:** Required

**Request:**
```
POST /chat/query
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer token |
| Content-Type | Yes | Must be "application/json" |

**Request Body:**
```json
{
  "question": "How does the authentication system work?",
  "repo_id": "507f1f77bcf86cd799439011",
  "chat_history": [
    {
      "role": "human",
      "content": "What is the project structure?"
    },
    {
      "role": "ai",
      "content": "This is a FastAPI project with a modular structure. It has routers for auth, repos, and chat..."
    }
  ]
}
```

**Request Body Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question | string | Yes | The question to ask about the codebase |
| repo_id | string | Yes | The repository ID to query |
| chat_history | array | No | Previous messages for context |

**Chat History Message Object:**
| Field | Type | Description |
|-------|------|-------------|
| role | string | "human" for user messages, "ai" for assistant responses |
| content | string | The message content |

**Success Response (200 OK):**
```json
{
  "answer": "The authentication system uses JWT (JSON Web Tokens) with bcrypt password hashing. Here's how it works:\n\n1. **Password Hashing**: When a user registers, the password is hashed using bcrypt with a salt. The hash is stored in MongoDB.\n\n2. **Token Generation**: On login, after verifying the password, a JWT is created with the user's ID and email as payload. The token expires in 7 days.\n\n3. **Token Verification**: Protected endpoints use the `get_current_user` dependency which:\n   - Extracts the Bearer token from Authorization header\n   - Decodes the JWT using the secret key\n   - Retrieves the user from MongoDB\n\nYou can find the implementation in `services/auth.py` and `routers/auth.py`.",
  "sources": [
    {
      "file_path": "services/auth.py",
      "chunk_index": 0,
      "score": 0.9523
    },
    {
      "file_path": "routers/auth.py",
      "chunk_index": 2,
      "score": 0.8912
    },
    {
      "file_path": "services/auth.py",
      "chunk_index": 1,
      "score": 0.8541
    }
  ]
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| answer | string | The AI-generated response (may contain markdown) |
| sources | array | Array of source code chunks used to generate the answer |

**Source Object:**
| Field | Type | Description |
|-------|------|-------------|
| file_path | string | Path to the source file in the repository |
| chunk_index | number | Index of the code chunk within that file |
| score | number | Relevance score (0.0 to 1.0, higher = more relevant) |

**How Sources Work for Frontend:**

1. Display the `answer` as the main response
2. Show `sources` as clickable citations
3. User can click a source to:
   - Copy the file path
   - Navigate to the file in a code viewer
   - See the specific code chunk

**Error Responses:**

- **404 Not Found** - Repository not found or doesn't belong to user:
```json
{
  "detail": "Repo not found"
}
```

- **401 Unauthorized** - Invalid token:
```json
{
  "detail": "Invalid or expired token"
}
```

- **422 Unprocessable Entity** - Missing required fields:
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "question"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

## Authentication Flow for Frontend

### Step 1: Register User
```javascript
const register = async (name, email, password) => {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data.user;
  }
  throw new Error(data.detail);
};
```

### Step 2: Login User
```javascript
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data.user;
  }
  throw new Error(data.detail);
};
```

### Step 3: Make Authenticated Requests
```javascript
const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (response.status === 401) {
    // Token expired or invalid - redirect to login
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  
  return response;
};
```

### Step 4: Ingest Repository (with polling)
```javascript
const ingestRepo = async (repoUrl) => {
  // Start ingestion
  const response = await fetchWithAuth('http://localhost:8000/repos/ingest', {
    method: 'POST',
    body: JSON.stringify({ repo_url: repoUrl })
  });
  const { repo_id, task_id, status } = await response.json();
  
  // Poll for status
  const checkStatus = async () => {
    const statusRes = await fetchWithAuth(`http://localhost:8000/repos/status/${repo_id}`);
    const statusData = await statusRes.json();
    
    if (statusData.repo_status === 'ready') {
      return statusData;
    } else if (statusData.repo_status === 'failed') {
      throw new Error(statusData.error || 'Processing failed');
    } else {
      // Continue polling
      setTimeout(checkStatus, 2000);
    }
  };
  
  return checkStatus();
};
```

### Step 5: Ask Chat Question
```javascript
const askQuestion = async (question, repoId, chatHistory = []) => {
  const response = await fetchWithAuth('http://localhost:8000/chat/query', {
    method: 'POST',
    body: JSON.stringify({
      question,
      repo_id: repoId,
      chat_history: chatHistory
    })
  });
  return await response.json();
};
```

---

## Common Error Responses

All authenticated endpoints may return:

| Status Code | Meaning | Response |
|-------------|---------|----------|
| 401 | Invalid/missing token | `{ "detail": "Invalid or expired token" }` |
| 401 | Token user not found | `{ "detail": "User not found" }` |
| 403 | Forbidden | `{ "detail": "Not authorized" }` |
| 404 | Resource not found | `{ "detail": "Not found" }` |
| 500 | Server error | `{ "detail": "Internal server error" }` |

---

## Data Types Reference

### User Object
```typescript
interface User {
  id: string;           // MongoDB ObjectId as string
  name: string;        // User's display name
  email: string;       // User's email address
  created_at: string;  // ISO 8601 datetime
}
```

### Repository Object
```typescript
interface Repository {
  _id: string;           // MongoDB ObjectId
  user_id: string;      // Owner's user ID
  repo_url: string;     // GitHub URL
  repo_name: string;    // Repository name
  status: RepositoryStatus;
  file_count: number;   // Files processed
  chunk_count: number;  // Vector chunks created
  error: string | null; // Error message if failed
  created_at: string;   // ISO 8601 datetime
  task_id: string;      // Celery task ID
}

type RepositoryStatus = 
  | "queued" 
  | "cloning" 
  | "parsing" 
  | "embedding" 
  | "ready" 
  | "failed";
```

### Chat Message
```typescript
interface ChatMessage {
  role: "human" | "ai";
  content: string;
}
```

### Chat Response
```typescript
interface ChatResponse {
  answer: string;
  sources: Source[];
}

interface Source {
  file_path: string;
  chunk_index: number;
  score: number;
}
```
