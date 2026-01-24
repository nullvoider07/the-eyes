// crates/auth/src/lib.rs
use anyhow::Result;
use axum::{
    extract::Request,
    http::StatusCode,
    middleware::Next,
    response::Response,
};
use chrono::{DateTime, Utc};
use oauth2::{
    basic::BasicClient, AuthUrl, ClientId, ClientSecret, RedirectUrl, TokenUrl,
    AuthorizationCode, TokenResponse as OAuth2TokenResponse, CsrfToken,
};
use rand::Rng;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

// Token Authentication
#[derive(Clone)]
pub struct TokenAuth {
    token: String,
}

// Middleware for token authentication
impl TokenAuth {
    pub fn new(token: String) -> Self {
        Self { token }
    }

    // Middleware function
    pub async fn middleware(
        &self,
        req: Request,
        next: Next,
    ) -> Result<Response, StatusCode> {
        // Skip auth for health endpoint
        if req.uri().path() == "/health" {
            return Ok(next.run(req).await);
        }

        let auth_header = req
            .headers()
            .get("Authorization")
            .and_then(|v| v.to_str().ok());

        match auth_header {
            Some(header) if header.starts_with("Bearer ") => {
                let token = header.trim_start_matches("Bearer ");
                if token == self.token {
                    Ok(next.run(req).await)
                } else {
                    Err(StatusCode::UNAUTHORIZED)
                }
            }
            _ => Err(StatusCode::UNAUTHORIZED),
        }
    }
}

// Token structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Token {
    pub value: String,
    pub expires_at: DateTime<Utc>,
}

// Token generation and validation
pub fn generate_token() -> Result<String> {
    let mut rng = rand::thread_rng();
    let bytes: [u8; 32] = rng.r#gen();
    Ok(base64::encode(&bytes))
}

// Simple token validation
pub fn validate_token(token: &str) -> bool {
    !token.is_empty()
}

// OAuth Provider
#[derive(Clone)]
pub struct OAuthConfig {
    pub client_id: String,
    pub client_secret: String,
    pub redirect_url: String,
    pub auth_url: String,
    pub token_url: String,
    pub scopes: Vec<String>,
}

// OAuth Provider structure
pub struct OAuthProvider {
    client: BasicClient,
    states: Arc<RwLock<HashMap<String, DateTime<Utc>>>>,
}

// OAuth Provider implementation
impl OAuthProvider {
    pub fn new(config: OAuthConfig) -> Result<Self> {
        let client = BasicClient::new(
            ClientId::new(config.client_id),
            Some(ClientSecret::new(config.client_secret)),
            AuthUrl::new(config.auth_url)?,
            Some(TokenUrl::new(config.token_url)?),
        )
        .set_redirect_uri(RedirectUrl::new(config.redirect_url)?);

        Ok(Self {
            client,
            states: Arc::new(RwLock::new(HashMap::new())),
        })
    }

    // Generate authorization URL
    pub async fn get_auth_url(&self) -> Result<(String, String)> {
        let state = generate_state()?;
        
        // OAuth2 expects CsrfToken, not String
        let (auth_url, _csrf_token) = self.client
            .authorize_url(|| CsrfToken::new(state.clone()))
            .url();

        let mut states = self.states.write().await;
        states.insert(state.clone(), Utc::now());

        Ok((auth_url.to_string(), state))
    }

    // Exchange code for access token
    pub async fn exchange(&self, code: String, state: String) -> Result<String> {
        let mut states = self.states.write().await;
        
        if !states.contains_key(&state) {
            anyhow::bail!("Invalid state");
        }
        states.remove(&state);

        let token = self.client
            .exchange_code(AuthorizationCode::new(code))
            .request_async(oauth2::reqwest::async_http_client)
            .await?;

        Ok(token.access_token().secret().clone())
    }
}

// Generate a random state string
fn generate_state() -> Result<String> {
    let mut rng = rand::thread_rng();
    let bytes: [u8; 32] = rng.r#gen();
    Ok(base64::encode(&bytes))
}

// Base64 encoding helper
mod base64 {
    use base64::{Engine as _, engine::general_purpose};

    pub fn encode(data: &[u8]) -> String {
        general_purpose::STANDARD.encode(data)
    }
}

// Unit tests
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_generation() {
        let token = generate_token().unwrap();
        assert!(!token.is_empty());
        assert!(validate_token(&token));
    }

    #[test]
    fn test_token_auth() {
        let auth = TokenAuth::new("test-token".to_string());
        assert_eq!(auth.token, "test-token");
    }
}