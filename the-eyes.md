# The Eye - Vision Capture Tool

**Version:** 0.2.0  
**Last Updated:** January 2026  
**Developer:** Kartik (NullVoider)

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Capability Summary](#capability-summary)
   - [Server Capabilities](#server-capabilities)
   - [Agent Capabilities](#agent-capabilities)
   - [System Features](#system-features)
4. [Technical Specifications](#technical-specifications)
   - [System Requirements](#system-requirements)
   - [Architecture](#architecture)
   - [Performance Metrics](#performance-metrics)
5. [Installation](#installation)
   - [Windows Installation](#windows-installation)
   - [macOS and Linux Installation](#macos-and-linux-installation)
6. [Quick Start](#quick-start)
7. [Usage Modes](#usage-modes)
8. [Command Reference](#command-reference)
   - [Server Commands](#server-commands)
   - [Agent Commands](#agent-commands)
   - [Utility Commands](#utility-commands)
9. [Configuration](#configuration)
10. [Advanced Features](#advanced-features)
11. [Cloud Storage Integration](#cloud-storage-integration)
12. [API Reference](#api-reference)
13. [Python SDK](#python-sdk)
14. [Troubleshooting](#troubleshooting)
15. [About This Project](#about-this-project)

---

## Overview

**The Eye** is an AI-native vision capture tool designed for Computer Use Agent (CUA) workflows. It provides real-time screen capture capabilities with a client-server architecture, enabling remote monitoring, AI training data collection, and automated visual workflows.

The Eye consists of two main components:

- **Eye Server** (Rust): High-performance HTTP server that receives, stores, and serves captured frames
- **Eye Agent** (Python): Cross-platform screen capture client that continuously captures and uploads screenshots

### Use Cases

- **AI Training Data Collection**: Capture screen interactions for training computer use agents
- **Remote Monitoring**: Monitor remote systems in real-time
- **Automated Testing**: Record UI interactions for testing and debugging
- **Time-lapse Creation**: Generate time-lapse videos from screen captures
- **Activity Logging**: Track and analyze screen activity patterns
- **Cloud Storage**: Store captured images directly to cloud storage providers

---

## Key Features

- ✅ **Cross-Platform Support**: Windows, macOS, Linux (X11 and Wayland)
- ✅ **Multiple Image Formats**: PNG, JPEG, WebP, BMP, TIFF
- ✅ **Configurable Quality**: Adjustable compression quality (1-100)
- ✅ **Dynamic Configuration**: Real-time agent configuration updates
- ✅ **Auto-Stop Modes**: Duration-based and frame-count-based auto-stop
- ✅ **Memory-Efficient**: Circular buffer storage with configurable capacity
- ✅ **Token Authentication**: Secure server-agent communication
- ✅ **RESTful API**: Easy integration with other tools
- ✅ **Python SDK**: Programmatic access to server functionality
- ✅ **Webhook Support**: Event notifications for integrations
- ✅ **Dataset Export**: Export captures in JSON, JSONL, or CSV formats
- ✅ **Cloud Storage Ready**: Compatible with cloud storage backends

---

## Capability Summary

### Server Capabilities

The Eye Server is a lightweight, high-performance Rust application that manages frame storage and distribution.

#### Core Functions

- **Frame Reception**: Accepts uploaded frames via HTTP POST
- **In-Memory Storage**: Circular buffer storage (configurable, default 100 frames)
- **Latest Frame Serving**: Provides instant access to the most recent capture
- **Health Monitoring**: Built-in health check endpoint
- **Command & Control**: Dynamic agent configuration via response piggybacking
- **Authentication**: Bearer token authentication for secure access
- **Debug Information**: Runtime metrics and statistics

#### Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health status and metrics |
| `/upload` | POST | Upload captured frames |
| `/snapshot.png` | GET | Retrieve latest captured frame |
| `/admin/config` | POST | Update global agent configuration |
| `/debug` | GET | Server debug information |

#### Configuration Management

The server can dynamically configure all connected agents:

- **Capture Interval**: Adjust frame capture frequency (0.1s minimum)
- **Image Format**: Change output format (PNG, JPEG)
- **Quality Settings**: Modify compression quality (1-100)

### Agent Capabilities

The Eye Agent is a Python-based screen capture client with extensive platform support.

#### Platform-Specific Capture

**Linux**:
- X11 support via `mss` library
- Wayland support via `flameshot` or `gnome-screenshot`
- Automatic fallback mechanisms

**macOS**:
- Native `screencapture` tool
- Supports Retina displays

**Windows**:
- `mss` library for efficient capture
- Multi-monitor support

#### Agent Features

- **Automatic Server Discovery**: Detects server on local network
- **Health Check Waiting**: Blocks until server is ready
- **Retry Logic**: Exponential backoff on upload failures
- **Format Flexibility**: Supports PNG, JPEG, WebP, BMP, TIFF
- **Quality Control**: Configurable compression (1-100)
- **Auto-Stop Modes**:
  - Duration-based: Stop after N seconds
  - Frame-count-based: Stop after N frames
- **Desktop Notifications**: Optional notification control (Linux)
- **Remote Configuration**: Accepts config updates from server

### System Features

#### Session Management

- Create and manage multiple capture sessions
- Track session metadata (start time, frame count, status)
- Stop and resume sessions programmatically

#### Metrics Collection

- Total captures (success/failed)
- Bytes uploaded
- Success rate tracking
- Average upload rate
- Uptime monitoring

#### Dataset Export

Export captured frame metadata in multiple formats:

- **JSON**: Complete metadata export
- **JSONL**: Line-delimited JSON for streaming
- **CSV**: Tabular format for analysis

#### Webhook Integration

Send real-time notifications for:

- Frame capture events
- Session start/stop events
- Custom event triggers

#### Real-time Streaming

- WebSocket support for live frame streaming
- Low-latency frame delivery
- Multiple concurrent clients

---

## Technical Specifications

### System Requirements

#### Server

- **OS**: Linux, macOS, Windows
- **RAM**: Minimum 256 MB (512 MB recommended)
- **CPU**: Any modern processor
- **Network**: TCP port 8080 (configurable)
- **Storage**: Minimal (in-memory only by default)

#### Agent

**Minimum Requirements**:
- **OS**: Windows 10+, macOS 10.13+, Ubuntu 20.04+ (or compatible Linux)
- **Python**: 3.11 or higher
- **RAM**: 128 MB minimum
- **CPU**: 1% typical usage (10% max configurable)

**Required Python Dependencies**:
- `mss` (0.6.0+): Cross-platform screen capture
- `Pillow` (9.0.0+): Image processing
- `requests` (2.31.0+): HTTP client
- `click` (8.1.7+): CLI framework
- `pyyaml` (6.0.1+): Configuration management

**Optional Dependencies**:
- `flameshot`: Linux Wayland capture (alternative)
- `gnome-screenshot`: Linux fallback

### Architecture

```
┌─────────────────┐
│   Eye Server    │
│   (Rust Binary)   │
│                 │
│  - HTTP Server  │
│  - Memory Store │
│  - Config Mgmt  │
└────────┬────────┘
         │
         │ HTTP/REST
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Agent 1│ │Agent 2│
│(Python│ │(Python│
└───────┘ └───────┘
    │         │
    │         │
┌───▼─────────▼───┐
│  Screen Capture │
│   - mss         │
│   - screencap   │
│   - flameshot   │
└─────────────────┘
```

#### Data Flow

1. **Capture**: Agent captures screen using platform-specific method
2. **Encode**: Image encoded in configured format (PNG/JPEG/etc.)
3. **Upload**: Frame uploaded via HTTP POST to server
4. **Store**: Server stores in circular buffer (latest N frames)
5. **Config Update**: Server responds with configuration updates
6. **Apply**: Agent applies new configuration for next capture

### Performance Metrics

#### Default Configuration

- **Capture Interval**: 1.5 seconds
- **Image Format**: PNG
- **Quality**: 95/100 (for JPEG)
- **Frame Buffer**: 100 frames
- **Network Timeout**: 5 seconds

#### Typical Performance

- **Capture Time**: 10-50ms (platform dependent)
- **Upload Time**: 5-25ms (network dependent)
- **Memory Usage**: 50-150 MB (agent), 100-500 MB (server)
- **CPU Usage**: 1-5% (agent), <1% (server)
- **Bandwidth**: 0.5-2 MB/s @ 1.5s interval

#### Scalability

- **Agents per Server**: 10-50 (depends on hardware)
- **Max Frame Rate**: 0.1s interval (10 FPS)
- **Storage Modes**: Memory, Disk, Hybrid

---

## Installation

### Windows Installation

Run the following command in PowerShell (Administrator):

```powershell
irm https://raw.githubusercontent.com/nullvoider07/the-eyes/master/install/install.ps1 | iex
```

This will:
- Download the latest Windows binaries
- Install to `%LOCALAPPDATA%\Programs\Eye\bin`
- Add to system PATH
- Install Python package

### macOS and Linux Installation

Run the following command in Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/nullvoider07/the-eyes/master/install/install.sh | bash
```

This will:
- Download platform-specific binaries
- Install to `~/.local/bin`
- Install Python package and dependencies
- Update PATH in shell profile
---

## Quick Start

### 1. Start the Server

```bash
eye server start --port 8080 --token my-secret-token
```

Or use the Rust binary directly:

```bash
export EYE_PORT=8080
export EYE_AUTH_TOKEN=my-secret-token
eye-server
```

### 2. Start the Agent

```bash
eye agent start \
  --server http://localhost:8080 \
  --token my-secret-token \
  --interval 2.0 \
  --format png
```

### 3. View Latest Capture

Open in browser:
```
http://localhost:8080/snapshot.png
```

Or use curl:
```bash
curl http://localhost:8080/snapshot.png -o screenshot.png
```

---

## Usage Modes

### Continuous Capture

Capture indefinitely until manually stopped:

```bash
eye agent start --server http://localhost:8080 --token TOKEN
```

Stop with `Ctrl+C`.

### Duration-Limited Capture

Capture for a specific duration:

```bash
# Capture for 60 seconds
eye agent start \
  --server http://localhost:8080 \
  --token TOKEN \
  --duration 60
```

### Frame-Limited Capture

Capture a specific number of frames:

```bash
# Capture 100 frames
eye agent start \
  --server http://localhost:8080 \
  --token TOKEN \
  --max-frames 100
```

### High-Quality Capture

```bash
# Maximum quality JPEG
eye agent start \
  --server http://localhost:8080 \
  --token TOKEN \
  --format jpeg \
  --quality 100
```

### Fast Capture

```bash
# Capture every 0.5 seconds
eye agent start \
  --server http://localhost:8080 \
  --token TOKEN \
  --interval 0.5
```

### Silent Mode (No Notifications)

```bash
# Disable desktop notifications
eye agent start \
  --server http://localhost:8080 \
  --token TOKEN \
  --no-notify
```

---

## Command Reference

### Server Commands

#### Start Server

```bash
eye server start [OPTIONS]
```

**Options**:
- `--port <PORT>`: Server port (default: 8080)
- `--token <TOKEN>`: Authentication token (optional)

**Environment Variables**:
- `EYE_PORT`: Server port
- `EYE_AUTH_TOKEN`: Authentication token

**Example**:
```bash
eye server start --port 9000 --token supersecret
```

### Agent Commands

#### Start Agent

```bash
eye agent start [OPTIONS]
```

**Required Options**:
- `--server <URL>`: Server URL (e.g., http://localhost:8080)

**Optional Options**:
- `--token <TOKEN>`: Authentication token
- `--interval <SECONDS>`: Capture interval (default: 1.5)
- `--format <FORMAT>`: Image format: png|jpeg|webp|bmp|tiff (default: png)
- `--quality <1-100>`: Compression quality (default: 95)
- `--duration <SECONDS>`: Auto-stop after duration
- `--max-frames <N>`: Auto-stop after N frames
- `--notify/--no-notify`: Show/hide notifications (default: show)

**Examples**:

```bash
# Basic usage
eye agent start --server http://localhost:8080

# With authentication
eye agent start --server http://10.0.0.5:8080 --token my-token

# Custom format and quality
eye agent start --server http://localhost:8080 --format jpeg --quality 85

# Auto-stop after 5 minutes
eye agent start --server http://localhost:8080 --duration 300

# Capture 50 frames at high speed
eye agent start --server http://localhost:8080 --interval 0.5 --max-frames 50
```

### Utility Commands

#### Debug Information

```bash
eye debug
```

Shows server statistics and configuration.

#### Version Information

```bash
eye version
```

Displays detailed version information for all components.

#### Update Eye

```bash
# Check for updates
eye update --check-only

# Install latest version
eye update
```

#### Uninstall Eye

Remove the tool and its components from your system.

```bash
# Standard uninstall (interactive)
eye uninstall

# Force uninstall (no confirmation)
eye uninstall -y

# Complete purge (removes config files and data)
eye uninstall --purge
```

#### Health Check

```bash
curl http://localhost:8080/health
```

**Response**:
```json
{
  "status": "healthy",
  "uptime": "123.45s",
  "frame_count": 42
}
```

---

## Configuration

### Server Configuration

Set via environment variables:

```bash
export EYE_PORT=8080
export EYE_AUTH_TOKEN=your-secret-token
```

### Agent Configuration

#### Via Command Line

```bash
eye agent start \
  --server http://localhost:8080 \
  --token TOKEN \
  --interval 2.0 \
  --format jpeg \
  --quality 90
```

#### Via Config File

Create `~/.eye/config.yaml`:

```yaml
capture:
  interval: 1.5
  format: png
  quality: 100
  resolution:
    width: 1920
    height: 1080

server:
  host: 0.0.0.0
  port: 8080
  protocol: http

auth:
  enabled: true
  method: token

storage:
  mode: memory
  max_frames: 100
  retention: 1h

safety:
  rate_limit:
    max_fps: 2.0
    burst: 5
  resource_limits:
    max_cpu_percent: 10
    max_memory_mb: 512
    max_bandwidth_mbps: 10
```

### Dynamic Configuration

Update agent configuration from server:

**With Authentication**:
```bash
curl -X POST http://localhost:8080/admin/config \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interval": 2.0,
    "format": "jpeg",
    "quality": 85
  }'
```

**Without Authentication** (if server has no token set):
```bash
curl -X POST http://localhost:8080/admin/config \
  -H "Content-Type: application/json" \
  -d '{"interval": 15.0, "format": "png", "quality": 95}'
```

**Response**:
```json
{
  "message": "Configuration updated",
  "config": {
    "interval": 15.0,
    "format": "png",
    "quality": 95
  }
}
```

Agents will automatically receive and apply the new configuration on their next upload.

---

## Advanced Features

### Session Management

Create and manage capture sessions programmatically:

```python
from eye.core import SessionManager

manager = SessionManager()

# Create session
session = manager.create_session(name="demo", duration=60)

# List active sessions
active = manager.get_active_sessions()

# Stop session
manager.stop_session(session.session_id)
```

### Metrics Collection

Track capture performance:

```python
from eye.core import MetricsCollector

metrics = MetricsCollector()

# Record capture
metrics.record_capture(success=True, size_bytes=102400)

# Get statistics
stats = metrics.get_metrics()
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Upload rate: {stats['avg_upload_rate']:.2f} frames/sec")
```

### Dataset Export

Export capture metadata:

```python
from eye.integrations import DatasetExporter
from pathlib import Path

exporter = DatasetExporter()

# Add frames
exporter.add_frame(frame_data, frame_id=1, metadata={"source": "agent-1"})

# Export as JSON
exporter.export_json(Path("captures.json"))

# Export as CSV
exporter.export_csv(Path("captures.csv"))
```

### Webhook Integration

Send notifications to external services:

```python
from eye.integrations import WebhookManager

webhook = WebhookManager(
    webhook_url="https://hooks.example.com/capture",
    headers={"X-API-Key": "secret"}
)

# Send frame notification
webhook.send_frame_notification(
    frame_id=123,
    metadata={"timestamp": "2026-01-21T10:30:00Z"}
)

# Send session event
webhook.send_session_event(
    event_type="session_started",
    session_id="abc123",
    data={"name": "Demo Session"}
)
```

---

## Cloud Storage Integration

The Eye can integrate with various cloud storage providers to store captured images.

### Supported Storage Modes

- **Memory**: In-memory storage (default, 100 frames)
- **Disk**: Local disk storage
- **Hybrid**: Both memory and disk
- **Cloud**: S3-compatible storage (coming soon)

### Disk Storage

Configure disk storage in `config.yaml`:

```yaml
storage:
  mode: disk
  path: /var/eye/captures
  max_size_gb: 10
  retention_days: 7
```

Or use the Storage Manager:

```python
from eye.pkg.storage import Manager

# Create hybrid storage
storage = Manager(
    mode="hybrid",
    memory_size=100,
    disk_path="/var/eye/captures"
)

# Store frame
storage.store(frame)

# Retrieve latest
latest = storage.get_latest()
```

### Cloud Storage Integration Pattern

While direct cloud storage isn't built-in yet, you can integrate with cloud providers:

```python
import boto3
from eye.core import EyeClient

# Initialize Eye client
eye = EyeClient("http://localhost:8080", token="TOKEN")

# Initialize S3 client
s3 = boto3.client('s3')

# Fetch and upload to S3
snapshot = eye.get_snapshot()
s3.put_object(
    Bucket='my-captures',
    Key=f'captures/{datetime.now().isoformat()}.png',
    Body=snapshot
)
```

---

## API Reference

### REST API Endpoints

#### GET /health

Check server health.

**Response**:
```json
{
  "status": "healthy",
  "uptime": "3600.50s",
  "frame_count": 240
}
```

#### POST /upload

Upload a captured frame.

**Headers**:
- `Authorization: Bearer <token>` (if auth enabled)
- `Content-Type: image/png` or `multipart/form-data`
- `X-Frame-ID: <id>` (for raw upload)

**Form Data** (multipart):
- `image`: Image file
- `frame_id`: Frame identifier

**Response**:
```json
{
  "status": "ok",
  "frame_id": 123,
  "size_kb": 245.3,
  "config": {
    "interval": 1.5,
    "format": "png",
    "quality": 95
  }
}
```

#### GET /snapshot.png

Retrieve the latest captured frame.

**Headers** (response):
- `X-Frame-ID`: Frame identifier

**Response**: Binary image data

#### POST /admin/config

Update global agent configuration.

**Headers**:
- `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "interval": 2.0,
  "format": "jpeg",
  "quality": 85
}
```

**Response**:
```json
{
  "message": "Configuration updated",
  "config": {
    "interval": 2.0,
    "format": "jpeg",
    "quality": 85
  }
}
```

#### GET /debug

Get server debug information.

**Response**:
```json
{
  "uptime_sec": 3600.5,
  "total_frames": 240,
  "current_config": {
    "interval": 1.5,
    "format": "png",
    "quality": 95
  }
}
```

---

## Python SDK

### Installation

```bash
pip install eye-capture
```

### Basic Usage

```python
from eye.core import EyeClient

# Connect to server
client = EyeClient("http://localhost:8080", token="my-token")

# Check health
health = client.health_check()
print(health)

# Get latest snapshot
image_data = client.get_snapshot()
with open("screenshot.png", "wb") as f:
    f.write(image_data)

# Get metadata
metadata = client.get_snapshot_metadata()
print(f"Frame ID: {metadata['frame_id']}")

# Upload frame
with open("myframe.png", "rb") as f:
    response = client.upload_frame(f.read(), frame_id=1)
    print(response)

# Debug info
debug = client.get_debug_info()
print(debug)

# Close connection
client.close()
```

### Advanced SDK Usage

```python
from eye.core import EyeClient, SessionManager, MetricsCollector
from eye.integrations import DatasetExporter, WebhookManager

# Initialize components
client = EyeClient("http://localhost:8080", token="TOKEN")
sessions = SessionManager()
metrics = MetricsCollector()
exporter = DatasetExporter()

# Create session
session = sessions.create_session(name="Training Data", duration=300)

# Capture loop
while session.status == "active":
    # Get frame
    frame = client.get_snapshot()
    
    # Record metrics
    metrics.record_capture(success=True, size_bytes=len(frame))
    
    # Export metadata
    metadata = client.get_snapshot_metadata()
    exporter.add_frame(frame, int(metadata['frame_id']), metadata)
    
    time.sleep(1.5)

# Export dataset
exporter.export_json(Path("training_data.json"))

# Get statistics
stats = metrics.get_metrics()
print(f"Captured {stats['captures_success']} frames")
print(f"Success rate: {stats['success_rate']:.2%}")
```

---

## Troubleshooting

### Agent Issues

**Problem**: Agent can't find server

**Solution**:
```bash
# Explicitly set server URL
export MEDIATOR_URL=http://your-server:8080
eye agent start --server http://your-server:8080
```

**Problem**: Screen capture fails on Linux Wayland

**Solution**:
```bash
# Install flameshot or gnome-screenshot
sudo apt install flameshot
# OR
sudo apt install gnome-screenshot
```

**Problem**: "mss not installed" warning

**Solution**:
```bash
pip install mss pillow requests
```

### Server Issues

**Problem**: Port already in use

**Solution**:
```bash
# Use different port
eye server start --port 9000
```

**Problem**: Authentication failures

**Solution**:
```bash
# Ensure token matches on both server and agent
export EYE_AUTH_TOKEN=same-token-everywhere
```

### Performance Issues

**Problem**: High CPU usage

**Solution**:
```bash
# Increase capture interval
eye agent start --server URL --interval 3.0

# Reduce quality
eye agent start --server URL --format jpeg --quality 75
```

**Problem**: High memory usage

**Solution**:
```yaml
# Reduce frame buffer in config.yaml
storage:
  max_frames: 50
```

### Debug Mode

Enable verbose logging:

```python
from eye.utils import setup_logging

setup_logging(level="DEBUG", log_file=Path("/tmp/eye.log"))
```
---

## Support

- **Issues**: [GitHub Issues](https://github.com/nullvoider07/the-eyes/issues)
- **Documentation**: [GitHub Repository](https://github.com/nullvoider07/the-eyes)

---

**Last Updated:** January 21, 2026  
**Developer:** Kartik (NullVoider)

---

## About This Project

The Eye - Vision Capture Tool was built from scratch through iterative testing and refinement. Every command, every feature, and every line of code was crafted to solve real automation challenges for Computer Use Agents.

If you find this tool useful, encounter bugs, or have feature requests, feel free to reach out directly via [X (formerly Twitter)](https://x.com/nullvoider07).

**The Eye** - Vision capture for the AI age 👁️