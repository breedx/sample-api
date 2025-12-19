# Senior QA Automation Assessment - Multi-Tenant API

## Overview

Design and implement comprehensive test automation for a production-like multi-tenant SaaS API with authentication, file management, and rate limiting.

**Time:** 4-6 hours
**Level:** Senior
**Skills:** Python, pytest, API testing, OAuth2/JWT, multi-tenancy, CI/CD

## The Challenge

Test a FastAPI application with:
- **JWT authentication** (OAuth2 pattern)
- **Multi-tenant architecture** with data isolation
- **File upload/download** workflows
- **Rate limiting** (10 req/min per endpoint)
- **Pagination** for large datasets
- **Role-based access control** (admin vs user)

## API Endpoints

### Authentication
```
POST /auth/register   - Register tenant + admin user
POST /auth/login      - Get JWT tokens
POST /auth/refresh    - Refresh access token
POST /auth/logout     - Invalidate token
```

### Users (Authenticated, Tenant-Scoped)
```
GET    /api/v1/users           - List users (paginated)
POST   /api/v1/users           - Create user
GET    /api/v1/users/{id}      - Get user details
PUT    /api/v1/users/{id}      - Update user
DELETE /api/v1/users/{id}      - Soft delete user
```

### Files (Authenticated, Tenant-Scoped)
```
POST   /api/v1/files/upload    - Upload file
GET    /api/v1/files/{id}      - Download file
GET    /api/v1/files           - List files (paginated)
DELETE /api/v1/files/{id}      - Delete file
```

### Admin (Admin Role Only)
```
GET /api/v1/admin/tenants - List all tenants
GET /api/v1/admin/stats   - System statistics
```

## Requirements

### Must Implement (30+ tests)

**Authentication (8+ tests)**
- Valid login flow
- Invalid credentials
- Token expiration handling
- Token refresh workflow
- Logout functionality
- Malformed/missing tokens
- Role-based access control

**Multi-Tenant Isolation (6+ tests)**
- Cross-tenant user access (should fail)
- Cross-tenant file access (should fail)
- Tenant-scoped data queries
- Admin cross-tenant access

**User Management (8+ tests)**
- Create user in tenant
- List users with pagination
- Update user details
- Soft delete user
- Duplicate username/email handling
- Invalid input validation

**File Management (6+ tests)**
- Upload various file types
- Download files
- List files with pagination
- Delete files
- File type validation
- File size limits

**Rate Limiting (2+ tests)**
- Enforce 10 req/min limit
- Verify 429 status + headers

### Advanced pytest Patterns

**Required:**
- Custom fixtures for authenticated clients per tenant
- Parametrized tests for multi-scenario coverage
- Test markers (`@pytest.mark.auth`, `@pytest.mark.tenant_isolation`, etc.)
- Proper setup/teardown for isolation
- Environment configuration support

**Bonus:**
- Async test patterns
- Test data factories (factory_boy, Faker)
- Custom pytest plugins
- Load/performance testing
- Mock external services

### Rust Integration Tests (Optional Bonus)

We also provide Rust integration tests in `rust_tests/` to demonstrate cross-language testing capability. This is **completely optional** but shows production-level polyglot engineering skills.

**Run Rust tests:**
```bash
cd rust_tests
cargo test
cargo test -- --nocapture  # Verbose output
```

**Bonus points for:**
- Completing the TODO tests in `rust_tests/tests/integration_tests.rs`
- Adding additional Rust test cases
- Demonstrating Rust/Python test coordination

**Why Rust tests?**
- Demonstrates polyglot capability (Python + Rust)
- Shows HTTP client testing from external process
- Mirrors our production stack (we use both Python and Rust)
- Tests API contracts from consumer perspective

### CI/CD Pipeline

Create `.github/workflows/tests.yml` with:
- Multi-environment test runs (dev/stage)
- Coverage reporting (minimum 80%)
- Parallel test execution
- JUnit XML output

### Documentation

Create `TESTING_STRATEGY.md` explaining:
- Your test architecture
- Fixture design decisions
- Multi-tenant isolation approach
- CI/CD strategy
- Trade-offs made

## Setup

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run API
export API_ENV=dev
export JWT_SECRET=test_secret_key
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -v --cov=app --cov-report=term-missing

# Run with markers
pytest -m auth -v
pytest -m tenant_isolation -v
pytest -m integration -v

# Parallel execution
pytest -n auto -v

# Rust tests (optional bonus)
cd rust_tests && cargo test
```

## Evaluation Criteria

**Technical (60%)**
- Authentication testing depth
- Multi-tenant isolation verification
- Advanced pytest usage (fixtures, parametrization, markers)
- CI/CD pipeline quality
- Code organization

**Architecture (25%)**
- Test design patterns
- Reusable fixtures
- Environment handling
- Scalability considerations

**Professional (15%)**
- Documentation quality
- Code readability
- Production-mindedness
- Edge case coverage

## Example Patterns

### Authenticated Client Fixture
```python
@pytest.fixture
def tenant_a_admin(client):
    """Return authenticated admin client for Tenant A"""
    # Register tenant
    register = client.post("/auth/register", json={
        "tenant_name": "tenant_a",
        "admin_email": "admin@a.com",
        "admin_username": "admin_a",
        "admin_password": "SecurePass123!"
    })

    # Login
    login = client.post("/auth/login", json={
        "username": "admin_a",
        "password": "SecurePass123!"
    })
    token = login.json()["access_token"]

    # Return client with auth header
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
```

### Tenant Isolation Test
```python
@pytest.mark.tenant_isolation
def test_cross_tenant_user_access_denied(tenant_a_admin, tenant_b_admin):
    """Tenant A cannot access Tenant B's users"""
    # Tenant B creates user
    user_b = tenant_b_admin.post("/api/v1/users", json={
        "username": "bob",
        "email": "bob@b.com",
        "full_name": "Bob User"
    })
    user_b_id = user_b.json()["id"]

    # Tenant A attempts access (should fail)
    response = tenant_a_admin.get(f"/api/v1/users/{user_b_id}")
    assert response.status_code == 404
```

### Rate Limit Test
```python
def test_rate_limit_enforcement(tenant_a_admin):
    """Verify 429 after exceeding rate limit"""
    for i in range(11):
        response = tenant_a_admin.get("/api/v1/users")
        if i < 10:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
            assert "X-RateLimit-Reset" in response.headers
```

## Submission

1. **Push code** to your fork/branch
2. **Verify tests pass**: `pytest -v --cov=app`
3. **(Optional) Run Rust tests**: `cd rust_tests && cargo test`
4. **Submit:**
   - Repository link
   - Test output (coverage report)
   - `TESTING_STRATEGY.md`
   - (Optional) Rust test results

## Questions?

- **pytest patterns?** https://docs.pytest.org/
- **FastAPI testing?** https://fastapi.tiangolo.com/tutorial/testing/
- **JWT/OAuth2?** https://jwt.io/introduction
- **Multi-tenancy?** Think AWS IAM resource scoping

---

**Good luck! Show us your senior-level testing expertise.**
