# OpenAPI & REST API Specification

Base URL: `http://localhost:8000/api`  
Interactive Swagger UI: `http://localhost:8000/docs`  
ReDoc Documentation: `http://localhost:8000/redoc`

---

## 1. Authentication Endpoints

### `POST /api/auth/register`
Create a new user account.
- **Request Body**:
  ```json
  {
    "email": "analyst@company.com",
    "password": "SecurePassword123",
    "full_name": "Jordan Lee",
    "role": "analyst"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "analyst@company.com",
      "full_name": "Jordan Lee",
      "role": "analyst",
      "is_active": true,
      "created_at": "2026-09-02T10:00:00Z"
    }
  }
  ```

### `POST /api/auth/login`
Authenticate with email and password.
- **Request Body**:
  ```json
  {
    "email": "analyst@company.com",
    "password": "SecurePassword123"
  }
  ```

### `POST /api/auth/refresh`
Rotate access token using refresh token.

### `GET /api/auth/me`
Retrieve authenticated user profile. Requires `Authorization: Bearer <token>`.

---

## 2. Schema Management Endpoints

### `GET /api/schemas`
List all accessible schemas (system default + user custom).

### `GET /api/schemas/{id}`
Get full metadata and DDL for schema by ID.

### `POST /api/schemas/upload`
Upload custom database schema via DDL statements.
- **Request Body**:
  ```json
  {
    "name": "Logistics & Fleet DB",
    "description": "Trucks, drivers, and delivery routes",
    "dialect": "postgres",
    "ddl_content": "CREATE TABLE trucks (truck_id INT PRIMARY KEY, model VARCHAR(50));"
  }
  ```

### `GET /api/schemas/{id}/preview?table_name={table}&limit=10`
Preview live sample records from any table.

---

## 3. Query & Inference Endpoints

### `POST /api/queries/generate`
Translate natural language prompt to SQL query.
- **Request Body**:
  ```json
  {
    "schema_id": 1,
    "prompt": "Show top 5 customers by total order amount"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "query_id": 42,
    "natural_language_query": "Show top 5 customers by total order amount",
    "generated_sql": "SELECT c.customer_id, c.first_name, c.last_name, SUM(o.total_amount) AS total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.first_name, c.last_name ORDER BY total_spent DESC LIMIT 5;",
    "confidence_score": 0.98,
    "explanation": "This query retrieves and analyzes records across customers and orders.",
    "is_cached": false,
    "inference_time_ms": 14.2,
    "suggested_charts": ["bar", "pie"]
  }
  ```

### `POST /api/queries/execute`
Execute validated read-only SQL query against target database.
- **Request Body**:
  ```json
  {
    "schema_id": 1,
    "sql_query": "SELECT country, COUNT(customer_id) AS total_customers FROM customers GROUP BY country;",
    "query_id": 42
  }
  ```

### `POST /api/queries/validate`
AST safety and SQL injection firewall inspection.

### `POST /api/queries/explain`
Deconstruct SQL query into step-by-step plain English explanations.

### `GET /api/queries/history`
Fetch query history logs with latency and status.

### `POST /api/queries/save`
Bookmark a natural language / SQL query with custom tags.

---

## 4. Results & Export Endpoints

### `GET /api/results/{id}`
Retrieve stored dataset for query execution.

### `POST /api/results/{id}/export`
Export query results to file format (`csv`, `xlsx`, `json`).
- **Request Body**:
  ```json
  {
    "format": "csv",
    "filename": "top_customers_report"
  }
  ```

---

## 5. Admin & Observability Endpoints

### `GET /api/admin/users`
List all users and permissions (Admin role required).

### `GET /api/admin/analytics`
System query volume, latency metrics, and top queried tables.

### `GET /api/admin/models`
Active ML model metadata, architecture details, and latency benchmarks.

### `GET /api/admin/audit-logs`
Security audit trail tracking user actions and IP addresses.
