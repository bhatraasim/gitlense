# GitLense API - Complete Endpoint Documentation

## Base URL
`http://localhost:8000` (development)

## Authentication
Most endpoints require Bearer token authentication:
```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints (`/auth`)

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "name": "string",
  "email": "string (valid email)",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string (JWT token)",
  "token_type": "bearer",
  "user": {
    "id": "string (MongoDB ObjectId)",
    "name": "string",
    "email": "string",
    "created_at": "string (ISO datetime)"
  }
}
```

**Error Responses:**
- `400`: Email already registered

---

### POST /auth/login
Login with existing credentials.

**Request Body:**
```json
{
  "name": "string (not used, but required by schema)",
  "email": "string (valid email)",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string (JWT token)",
  "token_type": "bearer",
  "user": {
    "id": "string (MongoDB ObjectId)",
    "name": "string",
    "email": "string",
    "created_at": "string (ISO datetime)"
  }
}
```

**Error Responses:**
- `400`: Invalid email or Invalid password

---

### POST /auth/logout
Logout current user (client-side token deletion).

**Authentication:** Required

**Request Body:** None

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## Repository Endpoints (`/repos`)

### POST /repos/ingest
Ingest a GitHub repository for RAG processing.

**Authentication:** Required

**Request Body:**
```json
{
  "repo_url": "string (must start with https://github.com/)"
}
```

**Response (200):**
```json
{
  "repo_id": "string (MongoDB ObjectId)",
  "task_id": "string (Celery task ID)",
  "status": "queued"
}
```

**Error Responses:**
- `400`: Invalid GitHub URL
- `400`: Repository already ingested

---

### GET /repos/status/{repo_id}
Get the processing status of an ingested repository.

**Authentication:** Required

**Path Parameters:**
- `repo_id`: string (MongoDB ObjectId)

**Response (200):**
```json
{
  "task_id": "string (Celery task ID)",
  "celery_state": "string (PENDING|STARTED|SUCCESS|FAILURE|RETRY)",
  "repo_status": "string (queued|cloning|parsing|embedding|ready|failed)",
  "file_count": "number",
  "chunk_count": "number",
  "error": "string|null (error message if failed)"
}
```

**Error Responses:**
- `404`: Repo not found

---

### GET /repos/
Get all repositories for the current user.

**Authentication:** Required

**Response (200):**
```json
[
  {
    "_id": "string (MongoDB ObjectId)",
    "user_id": "string",
    "repo_url": "string",
    "repo_name": "string",
    "status": "string (queued|cloning|parsing|embedding|ready|failed)",
    "file_count": "number",
    "chunk_count": "number",
    "error": "string|null",
    "created_at": "string (ISO datetime)",
    "task_id": "string (Celery task ID)"
  }
]
```

**Notes:**
- Returns up to 100 repositories
- Empty array if no repositories found

---

### DELETE /repos/{repo_id}
Delete a repository and all its associated data.

**Authentication:** Required

**Path Parameters:**
- `repo_id`: string (MongoDB ObjectId)

**Response (200):**
```json
{
  "message": "Repository deleted successfully"
}
```

**Error Responses:**
- `404`: Repo not found

**Side Effects:**
- Deletes vectors from Qdrant
- Deletes repository document from MongoDB

---

## Chat Endpoints (`/chat`)

### POST /chat/query
Query a repository using RAG (Retrieval-Augmented Generation).

**Authentication:** Required

**Request Body:**
```json
{
  "question": "string (user's question)",
  "repo_id": "string (MongoDB ObjectId)",
  "chat_history": [
    {
      "role": "string (human|ai)",
      "content": "string (message content)"
    }
  ]
}
```

**Notes:**
- `chat_history` is optional (defaults to empty array)
- Chat history maintains conversation context

**Response (200):**
```json
{
  "answer": "string (AI-generated response)",
  "sources": [
    {
      "file_path": "string",
      "content": "string (relevant code snippet)",
      "score": "number (relevance score)"
    }
  ]
}
```

**Error Responses:**
- `404`: Repo not found (or doesn't belong to user)

---

## Data Models

### User
```typescript
{
  id: string;              // MongoDB ObjectId
  name: string;
  email: string;           // Valid email format
  created_at: string;      // ISO datetime
}
```

### Repository
```typescript
{
  _id: string;             // MongoDB ObjectId
  user_id: string;         // Owner's user ID
  repo_url: string;        // GitHub URL
  repo_name: string;       // Repository name
  status: "queued" | "cloning" | "parsing" | "embedding" | "ready" | "failed";
  file_count: number;      // Number of files processed
  chunk_count: number;     // Number of text chunks created
  error: string | null;    // Error message if failed
  created_at: string;      // ISO datetime
  task_id: string;         // Celery task ID
}
```

### ChatMessage
```typescript
{
  role: "human" | "ai";
  content: string;
}
```

---

## Error Response Format

All error responses follow this structure:

```json
{
  "detail": "string (error message)"
}
```

Common HTTP status codes:
- `400`: Bad Request (validation error, duplicate data)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

---

## Authentication Flow

1. **Register**: `POST /auth/register` → Get access token
2. **Login**: `POST /auth/login` → Get access token
3. **Use Token**: Include in `Authorization: Bearer <token>` header
4. **Logout**: `POST /auth/logout` → Delete token client-side

---

## Repository Ingestion Flow

1. **Ingest**: `POST /repos/ingest` → Get repo_id and task_id
2. **Poll Status**: `GET /repos/status/{repo_id}` → Check processing status
3. **Wait**: Status progresses: queued → cloning → parsing → embedding → ready
4. **Query**: `POST /chat/query` → Ask questions about the repository

---

## Notes for Frontend Development

- All datetime fields are in ISO 8601 format
- MongoDB ObjectIds are 24-character hex strings
- JWT tokens expire based on server configuration
- Repository processing is asynchronous (use polling for status updates)
- Chat history is maintained client-side and sent with each query
- All authenticated endpoints return 401 if token is invalid/expired
