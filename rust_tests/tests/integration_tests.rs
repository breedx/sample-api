//! Rust Integration Tests for Multi-Tenant API
//!
//! BONUS CHALLENGE (Optional):
//! These tests demonstrate cross-language testing capability.
//! Implement comprehensive Rust tests that verify the Python API.
//!
//! Run with: cargo test
//! Run verbose: cargo test -- --nocapture

use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

const API_BASE: &str = "http://localhost:8000";

// ============================================================================
// Models (matching Python API)
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
struct HealthResponse {
    status: String,
    timestamp: String,
    environment: String,
    version: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct RegisterRequest {
    tenant_name: String,
    admin_email: String,
    admin_username: String,
    admin_password: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct RegisterResponse {
    message: String,
    tenant_id: String,
    admin_user_id: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct TokenResponse {
    access_token: String,
    refresh_token: String,
    token_type: String,
    expires_in: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct User {
    id: String,
    tenant_id: String,
    username: String,
    email: String,
    full_name: String,
    role: String,
    is_active: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct CreateUserRequest {
    username: String,
    email: String,
    full_name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    role: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ErrorResponse {
    detail: String,
}

// ============================================================================
// Test Utilities
// ============================================================================

struct TestClient {
    client: Client,
    base_url: String,
}

impl TestClient {
    fn new() -> Self {
        Self {
            client: Client::new(),
            base_url: API_BASE.to_string(),
        }
    }

    fn with_auth(token: &str) -> Self {
        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert(
            reqwest::header::AUTHORIZATION,
            format!("Bearer {}", token).parse().unwrap(),
        );

        Self {
            client: Client::builder()
                .default_headers(headers)
                .build()
                .unwrap(),
            base_url: API_BASE.to_string(),
        }
    }
}

/// Helper to register a tenant and return admin token
fn setup_tenant(tenant_name: &str) -> Result<TokenResponse, Box<dyn std::error::Error>> {
    let client = TestClient::new();

    // Register tenant
    let register = RegisterRequest {
        tenant_name: tenant_name.to_string(),
        admin_email: format!("admin@{}.com", tenant_name),
        admin_username: format!("admin_{}", tenant_name),
        admin_password: "SecurePass123!".to_string(),
    };

    let _: RegisterResponse = client
        .client
        .post(format!("{}/auth/register", client.base_url))
        .json(&register)
        .send()?
        .json()?;

    // Login
    let login = LoginRequest {
        username: format!("admin_{}", tenant_name),
        password: "SecurePass123!".to_string(),
    };

    let tokens: TokenResponse = client
        .client
        .post(format!("{}/auth/login", client.base_url))
        .json(&login)
        .send()?
        .json()?;

    Ok(tokens)
}

// ============================================================================
// Tests
// ============================================================================

#[test]
fn test_health_check() {
    let client = TestClient::new();

    let response = client
        .client
        .get(format!("{}/health", client.base_url))
        .send()
        .expect("Failed to send request");

    assert_eq!(response.status(), 200);

    let health: HealthResponse = response.json().expect("Failed to parse JSON");

    assert_eq!(health.status, "healthy");
    assert_eq!(health.version, "2.0.0");
}

#[test]
fn test_register_tenant_success() {
    let client = TestClient::new();

    let register = RegisterRequest {
        tenant_name: "test_tenant_rust".to_string(),
        admin_email: "admin@rust.com".to_string(),
        admin_username: "admin_rust".to_string(),
        admin_password: "SecurePass123!".to_string(),
    };

    let response = client
        .client
        .post(format!("{}/auth/register", client.base_url))
        .json(&register)
        .send()
        .expect("Failed to register tenant");

    assert_eq!(response.status(), 201);

    let result: RegisterResponse = response.json().expect("Failed to parse response");

    assert_eq!(result.message, "Tenant registered successfully");
    assert!(!result.tenant_id.is_empty());
    assert!(!result.admin_user_id.is_empty());
}

#[test]
fn test_login_success() {
    // Setup tenant first
    let tokens = setup_tenant("login_test").expect("Failed to setup tenant");

    assert_eq!(tokens.token_type, "bearer");
    assert!(!tokens.access_token.is_empty());
    assert!(!tokens.refresh_token.is_empty());
    assert!(tokens.expires_in > 0);
}

#[test]
fn test_login_invalid_credentials() {
    let client = TestClient::new();

    let login = LoginRequest {
        username: "nonexistent_user".to_string(),
        password: "WrongPassword".to_string(),
    };

    let response = client
        .client
        .post(format!("{}/auth/login", client.base_url))
        .json(&login)
        .send()
        .expect("Failed to send login request");

    assert_eq!(response.status(), 401);

    let error: ErrorResponse = response.json().expect("Failed to parse error");
    assert_eq!(error.detail, "Invalid username or password");
}

#[test]
fn test_create_user_authenticated() {
    // Setup tenant and get token
    let tokens = setup_tenant("user_test").expect("Failed to setup tenant");
    let client = TestClient::with_auth(&tokens.access_token);

    // Create user
    let new_user = CreateUserRequest {
        username: "test_user".to_string(),
        email: "testuser@example.com".to_string(),
        full_name: "Test User".to_string(),
        role: Some("user".to_string()),
    };

    let response = client
        .client
        .post(format!("{}/api/v1/users", client.base_url))
        .json(&new_user)
        .send()
        .expect("Failed to create user");

    assert_eq!(response.status(), 201);

    let user: User = response.json().expect("Failed to parse user");

    assert_eq!(user.username, "test_user");
    assert_eq!(user.email, "testuser@example.com");
    assert_eq!(user.role, "user");
    assert!(user.is_active);
}

#[test]
fn test_create_user_without_auth_fails() {
    let client = TestClient::new();

    let new_user = CreateUserRequest {
        username: "test_user".to_string(),
        email: "testuser@example.com".to_string(),
        full_name: "Test User".to_string(),
        role: None,
    };

    let response = client
        .client
        .post(format!("{}/api/v1/users", client.base_url))
        .json(&new_user)
        .send()
        .expect("Failed to send request");

    assert_eq!(response.status(), 401);
}

#[test]
fn test_tenant_isolation() {
    // Setup two tenants
    let tokens_a = setup_tenant("tenant_a_rust").expect("Failed to setup tenant A");
    let tokens_b = setup_tenant("tenant_b_rust").expect("Failed to setup tenant B");

    // Tenant B creates a user
    let client_b = TestClient::with_auth(&tokens_b.access_token);
    let new_user = CreateUserRequest {
        username: "user_b".to_string(),
        email: "userb@example.com".to_string(),
        full_name: "User B".to_string(),
        role: Some("user".to_string()),
    };

    let user_b_response = client_b
        .client
        .post(format!("{}/api/v1/users", client_b.base_url))
        .json(&new_user)
        .send()
        .expect("Failed to create user in tenant B");

    assert_eq!(user_b_response.status(), 201);

    let user_b: User = user_b_response.json().expect("Failed to parse user");
    let user_b_id = user_b.id;

    // Tenant A tries to access Tenant B's user (should fail)
    let client_a = TestClient::with_auth(&tokens_a.access_token);
    let response = client_a
        .client
        .get(format!("{}/api/v1/users/{}", client_a.base_url, user_b_id))
        .send()
        .expect("Failed to send request");

    // Should return 404 (not found) for security - don't leak tenant existence
    assert_eq!(response.status(), 404);
}

// TODO: Implement more tests
// - List users with pagination
// - Update user
// - Delete user
// - File upload/download
// - Rate limiting
// - Token refresh
// - Admin endpoints
// - Concurrent operations

#[test]
#[ignore] // TODO: Implement
fn test_rate_limiting() {
    // TODO: Make 11 requests and verify 11th returns 429
    todo!("Implement rate limiting test");
}

#[test]
#[ignore] // TODO: Implement
fn test_file_upload() {
    // TODO: Test file upload with multipart form
    todo!("Implement file upload test");
}

#[test]
#[ignore] // TODO: Implement
fn test_pagination() {
    // TODO: Create many users and test pagination
    todo!("Implement pagination test");
}
