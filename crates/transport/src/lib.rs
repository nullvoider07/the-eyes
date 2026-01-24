// crates/transport/src/lib.rs
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use reqwest::{Client as HttpClient, multipart};
use serde::{Deserialize, Serialize};
use std::time::Duration;

// Data structures for transport communication
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FrameMetadata {
    pub frame_id: i64,
    pub timestamp: DateTime<Utc>,
    pub size_bytes: i64,
    pub format: String,
}

// Request and Response structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UploadRequest {
    pub metadata: FrameMetadata,
    pub data: Vec<u8>,
}

// Response structure for upload acknowledgment
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UploadResponse {
    pub success: bool,
    pub message: String,
    pub frame_id: i64,
}

// Configuration structure for the agent
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentConfig {
    pub interval: f64,
    pub format: String,
    pub quality: i32,
}

// Client for communicating with the server
pub struct Client {
    server_url: String,
    token: String,
    client: HttpClient,
}

// Implementation of Client
impl Client {
    pub fn new(server_url: String, token: String) -> Self {
        let client = HttpClient::builder()
            .timeout(Duration::from_secs(5))
            .build()
            .expect("Failed to build HTTP client");

        Self {
            server_url,
            token,
            client,
        }
    }

    // Upload a frame to the server
    pub async fn upload_frame(&self, frame_id: i64, data: Vec<u8>) -> Result<serde_json::Value> {
        let url = format!("{}/upload", self.server_url);

        let form = multipart::Form::new()
            .part("image", multipart::Part::bytes(data).file_name("frame.png"))
            .text("frame_id", frame_id.to_string());

        let mut request = self.client
            .post(&url)
            .multipart(form);

        // Only add auth header if token is not empty
        if !self.token.is_empty() {
            request = request.header("Authorization", format!("Bearer {}", self.token));
        }

        let response = request
            .send()
            .await
            .context("Failed to send upload request")?;

        if !response.status().is_success() {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            anyhow::bail!("Upload failed: {} - {}", status, body);
        }

        let json = response.json::<serde_json::Value>()
            .await
            .context("Failed to parse response")?;

        Ok(json)
    }

    // Health check to verify server availability
    pub async fn health_check(&self) -> Result<()> {
        let url = format!("{}/health", self.server_url);

        let response = self.client
            .get(&url)
            .send()
            .await
            .context("Failed to send health check request")?;

        if !response.status().is_success() {
            anyhow::bail!("Unhealthy: {}", response.status());
        }

        Ok(())
    }
}

pub struct WebSocketServer {
}

impl WebSocketServer {
    pub fn new() -> Self {
        Self {}
    }

    pub async fn broadcast(&self, _data: Vec<u8>) -> Result<()> {
        Ok(())
    }
}

impl Default for WebSocketServer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_creation() {
        let client = Client::new(
            "http://localhost:8080".to_string(),
            "test-token".to_string(),
        );
        assert!(!client.server_url.is_empty());
    }
}