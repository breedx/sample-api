# Senior QA Automation Assessment - Multi-Tenant API

## Overview

Design and implement comprehensive test automation for a production-like multi-tenant SaaS API with authentication, file management, and rate limiting.

**Time:** 2-4 hours (tiered: 1.5-2h core, +1h extended, +1h bonus)
**Level:** Senior (with tiered evaluation)
**Skills:** Python, pytest, API testing, OAuth2/JWT, multi-tenancy

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
POST   /api/v1/users/bulk      - Create multiple users (async, uses asyncio.gather)
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

## Project Structure

```
sample-api/
├── app/                    # FastAPI application code
│   ├── main.py            # API endpoints and business logic
│   ├── auth.py            # JWT authentication, OAuth2 patterns
│   ├── config.py          # Environment configuration
│   └── __init__.py
│
├── py_tests/              # Python test suite (YOUR WORK GOES HERE)
│   ├── conftest.py        # Shared pytest fixtures
│   ├── test_health.py     # Example starter test
│   ├── test_async_example.py  # Async test patterns
│   └── (your tests here)  # Create test_auth.py, test_users.py, etc.
│
├── rust_tests/            # Rust integration tests (OPTIONAL BONUS)
│   ├── Cargo.toml         # Rust project config
│   └── tests/
│       └── integration_tests.rs  # HTTP client tests from external process
│
├── pytest.ini             # Pytest configuration (markers, coverage)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

**Where to add your tests:**
- Create test files in `py_tests/` directory (e.g., `test_auth.py`, `test_users.py`, `test_files.py`)
- Use provided fixtures from `conftest.py`
- Follow patterns in `test_async_example.py` for async operations
- See example fixture patterns below

**Rust tests (Optional):**
- Located in `rust_tests/tests/integration_tests.rs`
- Tests API from external HTTP client perspective
- Run with: `cd rust_tests && cargo test`
- Demonstrates polyglot testing capability
- **Completely optional** - focus on Python tests first

## Requirements (Tiered Approach)

### 🎯 Tier 1: Core Requirements (MUST COMPLETE)
**Target:** 10-12 tests | **Time:** 1.5-2 hours | **Evaluation:** Minimum passing score

**Authentication (4 tests)**
- Register tenant + admin user successfully
- Login with valid credentials → get JWT token
- Login with invalid credentials → 401 error
- Access protected endpoint without token → 401 error

**User Management with Auth (5 tests)**
- Create user (authenticated) → 201 success
- List users (authenticated, tenant-scoped) → returns only tenant's users
- Get user by ID (authenticated) → 200 success
- Update user (authenticated) → 200 success
- Duplicate username → 409 conflict

**Async Programming (1 test)**
- Bulk user creation using async patterns → tests `POST /api/v1/users/bulk`
- Must use `@pytest.mark.asyncio` and async/await patterns
- See `py_tests/test_async_example.py` for patterns

**Basic Tenant Isolation (2 tests)**
- Tenant A cannot access Tenant B's user → 404
- List users only shows current tenant's data

**Passing Criteria:** 10+ tests passing, 60%+ code coverage on core auth/users

---

### 🎯 Tier 2: Extended Requirements (SHOULD COMPLETE)
**Target:** +5-7 tests | **Time:** +1 hour | **Evaluation:** Strong passing score

**Additional User Tests (3 tests)**
- Delete user (soft delete) → is_active=False
- Duplicate email validation → 409 conflict
- Invalid input validation → 422 error

**File Management (3 tests)**
- Upload file successfully → 201, returns file_id
- Download file (tenant-scoped) → correct content
- Delete file (tenant-scoped) → 204 success

**Pagination (2 tests)**
- List users with pagination → multiple pages work
- Pagination metadata → has_next, total_count correct

**Strong Pass Criteria:** 15-18 tests passing, 70%+ code coverage

---

### 🎯 Tier 3: Bonus Challenges (OPTIONAL)
**Target:** +5+ tests | **Time:** +1+ hours | **Evaluation:** Exceptional/Outstanding

**Advanced Auth & Security:**
- Token refresh workflow
- Role-based access control (admin vs user)
- Invalid/expired token handling
- Cross-tenant file access prevention

**Async & Concurrency:**
- Concurrent user operations using `asyncio.gather()`
- Concurrent file uploads
- Performance testing (async vs sequential)
- Race condition handling

**Performance & Limits:**
- Rate limiting enforcement (429 responses)
- File type validation (415 unsupported media)
- File size limits (413 entity too large)

**Infrastructure & Documentation (Bonus):**
- CI/CD pipeline (GitHub Actions) working in PR
- TESTING_STRATEGY.md explaining your approach
- Test data factories for realistic data
- Rust integration tests (1-2 hours additional)

**Outstanding Criteria:** 20+ tests total, comprehensive documentation, working CI/CD

### Advanced pytest Patterns

**Required:**
- Custom fixtures for authenticated clients per tenant
- Parametrized tests for multi-scenario coverage
- Test markers (`@pytest.mark.auth`, `@pytest.mark.tenant_isolation`, etc.)
- Proper setup/teardown for isolation
- **Async test patterns** - At least one test using `@pytest.mark.asyncio`
- AsyncClient for testing bulk operations

**Bonus:**
- Test data factories (factory_boy, Faker)
- Custom pytest plugins
- Performance comparison (async vs sync operations)
- Concurrent operation testing with `asyncio.gather()`
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
- **Tier 1 (Critical):** Auth basics + User CRUD + Tenant isolation
- **Tier 2 (Important):** Files, pagination, advanced auth
- **Tier 3 (Bonus):** Rate limiting, CI/CD, advanced scenarios

**Architecture (25%)**
- Test fixture design (authenticated clients per tenant)
- Test organization and reusability
- Setup/teardown patterns
- Code clarity and maintainability

**Professional (15%)**
- Code quality (PEP 8, type hints, clear naming)
- Documentation (inline comments, TESTING_STRATEGY.md)
- Problem-solving approach (how you tackled complex scenarios)
- Time management (completed appropriate tier for time spent)

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
3. **Submit:**
   - Repository link
   - Test output showing: test count, pass rate, coverage %
   - Brief summary of what tier you completed
   - **(Tier 2+)** `TESTING_STRATEGY.md` explaining your approach
   - **(Tier 3)** Optional: Rust test results, CI/CD logs

**What We're Looking For:**
- **Minimum (Pass):** Tier 1 complete (10+ tests, 60%+ coverage, ~2 hours)
- **Target (Strong):** Tier 1 + Tier 2 (15+ tests, 70%+ coverage, ~3 hours)
- **Outstanding:** All 3 tiers (20+ tests, CI/CD, docs, ~4+ hours)

## Questions?

- **pytest patterns?** https://docs.pytest.org/
- **FastAPI testing?** https://fastapi.tiangolo.com/tutorial/testing/
- **JWT/OAuth2?** https://jwt.io/introduction
- **Multi-tenancy?** Think AWS IAM resource scoping

---

**Good luck! Show us your senior-level testing expertise.**
