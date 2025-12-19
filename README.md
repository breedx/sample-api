# Senior QA Automation Assessment - Multi-Tenant API

## Overview

Design and implement comprehensive test automation for a production-like multi-tenant SaaS API with authentication, file management, and rate limiting.

**Time:** 4-6 hours (tiered: 3-4 hours core, +2 hours extended/bonus)
**Level:** Senior (with tiered evaluation)
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

## Requirements (Tiered Approach)

### 🎯 Tier 1: Core Requirements (MUST COMPLETE)
**Target:** 15-18 tests | **Time:** 3-4 hours | **Evaluation:** Minimum passing score

**Authentication Basics (5 tests)**
- Register tenant + admin user
- Login with valid credentials
- Login with invalid credentials
- Access endpoint without token (should return 401)
- Access endpoint with invalid token (should return 401)

**User Management with Auth (8 tests)**
- Create user (authenticated, tenant-scoped)
- List users (authenticated, returns only tenant's users)
- Get user by ID (authenticated, tenant-scoped)
- Update user (authenticated, tenant-scoped)
- Delete user (authenticated, tenant-scoped)
- Duplicate username validation (409 conflict)
- Duplicate email validation (409 conflict)
- Invalid input validation (422 error)

**Basic Tenant Isolation (3 tests)**
- Tenant A cannot access Tenant B's users (404)
- List users only shows current tenant's data
- User operations are scoped to authenticated tenant

**Passing Criteria:** 15+ tests passing, 70%+ code coverage on auth/users modules

---

### 🎯 Tier 2: Extended Requirements (SHOULD COMPLETE)
**Target:** +6-8 tests | **Time:** +1.5-2 hours | **Evaluation:** Strong passing score

**File Management (4 tests)**
- Upload file successfully
- Download file (authenticated, tenant-scoped)
- List files (authenticated, returns only tenant's files)
- Delete file (authenticated, tenant-scoped)

**Pagination (2 tests)**
- List users with pagination (test multiple pages)
- Pagination metadata correct (has_next, total_count, etc.)

**Advanced Auth (2 tests)**
- Token refresh workflow
- Role-based access control (admin vs user)

**Strong Pass Criteria:** 20-25 tests passing, 80%+ code coverage

---

### 🎯 Tier 3: Bonus Challenges (OPTIONAL)
**Target:** +5-10 tests | **Time:** +1-2 hours | **Evaluation:** Exceptional/Outstanding

**Advanced Scenarios:**
- Rate limiting enforcement (429 responses)
- Cross-tenant file access prevention
- Token expiration handling
- File type/size validation
- Concurrent operations testing

**Infrastructure & Documentation:**
- CI/CD pipeline (GitHub Actions)
- TESTING_STRATEGY.md documentation
- Test data factories (factory_boy, Faker)
- Rust integration tests (cross-language)

**Outstanding Criteria:** All 3 tiers completed (25-30+ tests), comprehensive documentation

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
- **Minimum (Pass):** Tier 1 complete (15+ tests, 70%+ coverage)
- **Target (Strong):** Tier 1 + Tier 2 (20+ tests, 80%+ coverage)
- **Outstanding:** All 3 tiers (25+ tests, comprehensive documentation)

## Questions?

- **pytest patterns?** https://docs.pytest.org/
- **FastAPI testing?** https://fastapi.tiangolo.com/tutorial/testing/
- **JWT/OAuth2?** https://jwt.io/introduction
- **Multi-tenancy?** Think AWS IAM resource scoping

---

**Good luck! Show us your senior-level testing expertise.**
