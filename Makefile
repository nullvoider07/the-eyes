# Makefile for Eye Vision Capture Tool (Rust Edition)
# Builds Rust server and agent, keeps Python CLI

.PHONY: all build clean install test deps help release check fmt clippy bench run-server run-agent

# Version
VERSION ?= 0.1.0

# Build directories
TARGET_DIR := target
RELEASE_DIR := $(TARGET_DIR)/release
BUILD_DIR := build

# Binary names
SERVER_BIN := $(RELEASE_DIR)/eye-server
AGENT_BIN := $(RELEASE_DIR)/eye-agent

# Rust toolchain
CARGO := cargo
RUSTC := rustc

# Python
PYTHON := python3
PIP := pip3

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m

all: deps build

help:
	@echo "Eye Vision Capture Tool - Rust Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  make build         - Build Rust binaries (debug mode)"
	@echo "  make release       - Build optimized release binaries"
	@echo "  make install       - Install binaries and Python CLI system-wide"
	@echo "  make test          - Run all tests"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make deps          - Install Rust and Python dependencies"
	@echo "  make check         - Run cargo check on all crates"
	@echo "  make fmt           - Format all Rust code"
	@echo "  make clippy        - Run Clippy linter"
	@echo "  make bench         - Run benchmarks"
	@echo "  make run-server    - Build and run server (dev mode)"
	@echo "  make run-agent     - Build and run agent (dev mode)"
	@echo ""

# Install dependencies
deps:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@echo "$(BLUE)Checking Rust installation...$(NC)"
	@$(CARGO) --version || (echo "$(YELLOW)Rust not found. Install from https://rustup.rs$(NC)" && exit 1)
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	@$(PIP) install -e . --quiet 2>/dev/null || $(PIP) install -e .
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

# Build debug binaries
build:
	@echo "$(GREEN)Building Eye (debug mode)...$(NC)"
	@$(CARGO) build
	@echo "$(GREEN)✅ Build complete$(NC)"
	@echo ""
	@echo "Binaries available at:"
	@echo "  - $(TARGET_DIR)/debug/eye-server"
	@echo "  - $(TARGET_DIR)/debug/eye-agent"

# Build release binaries
release: python-cli
	@echo "$(GREEN)Building Eye (release mode)...$(NC)"
	@$(CARGO) build --release
	@echo "$(GREEN)✅ Release build complete$(NC)"
	@echo ""
	@echo "Optimized binaries available at:"
	@echo "  - $(SERVER_BIN)"
	@echo "  - $(AGENT_BIN)"

# Install Python CLI (editable mode for development)
python-cli:
	@echo "$(GREEN)Installing Python CLI...$(NC)"
	@$(PIP) install -e . --quiet 2>/dev/null || $(PIP) install -e .
	@echo "$(GREEN)✅ Python CLI installed$(NC)"

# Install binaries and Python package system-wide
install: release
	@echo "$(GREEN)Installing Eye system-wide...$(NC)"
	@mkdir -p /usr/local/bin
	@cp $(SERVER_BIN) /usr/local/bin/eye-server
	@cp $(AGENT_BIN) /usr/local/bin/eye-agent
	@chmod +x /usr/local/bin/eye-server
	@chmod +x /usr/local/bin/eye-agent
	@$(PIP) install .
	@echo "$(GREEN)✅ Eye installed$(NC)"
	@echo ""
	@echo "Installed commands:"
	@echo "  - eye          (Python CLI)"
	@echo "  - eye-server   (Rust server binary)"
	@echo "  - eye-agent    (Rust agent binary)"
	@echo ""
	@echo "Try: eye --help"

# Development install (editable Python package)
dev-install: build python-cli
	@echo "$(GREEN)Installing Eye (development mode)...$(NC)"
	@$(PIP) install -e .
	@echo "$(GREEN)✅ Eye installed in dev mode$(NC)"

# Run tests
test: test-rust test-python

test-rust:
	@echo "$(GREEN)Running Rust tests...$(NC)"
	@$(CARGO) test --workspace --all-features

test-python:
	@echo "$(GREEN)Running Python tests...$(NC)"
	@if [ -d "tests" ]; then $(PYTHON) -m pytest tests/ -v; else echo "No tests found"; fi

# Clean build artifacts
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@$(CARGO) clean
	@rm -rf $(BUILD_DIR)
	@rm -rf *.egg-info dist
	@rm -rf __pycache__ .pytest_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Clean complete$(NC)"

# Check code (fast compile check without building)
check:
	@echo "$(GREEN)Checking Rust code...$(NC)"
	@$(CARGO) check --workspace --all-features

# Format code
fmt:
	@echo "$(GREEN)Formatting Rust code...$(NC)"
	@$(CARGO) fmt --all
	@echo "$(BLUE)Formatting Python code...$(NC)"
	@$(PYTHON) -m black eye/ tests/ --quiet 2>/dev/null || echo "black not installed (optional)"
	@echo "$(GREEN)✅ Formatting complete$(NC)"

# Lint code with Clippy
clippy:
	@echo "$(GREEN)Running Clippy linter...$(NC)"
	@$(CARGO) clippy --workspace --all-features -- -D warnings

# Run benchmarks
bench:
	@echo "$(GREEN)Running benchmarks...$(NC)"
	@$(CARGO) bench --workspace

# Quick development testing
run-server: build
	@echo "$(GREEN)Starting Eye Server (development)...$(NC)"
	@export EYE_PORT=8080 && \
	 export EYE_AUTH_TOKEN=dev-token && \
	 $(CARGO) run -p eye-server

run-agent: build
	@echo "$(GREEN)Starting Eye Agent (development)...$(NC)"
	@export EYE_SERVER_URL=http://localhost:8080 && \
	 export EYE_AUTH_TOKEN=dev-token && \
	 $(CARGO) run -p eye-agent

# Show version and build info
version:
	@echo "$(GREEN)Eye Vision Capture Tool v$(VERSION) (Rust Edition)$(NC)"
	@echo "Rust version: $(shell $(RUSTC) --version)"
	@echo "Python version: $(shell $(PYTHON) --version)"
	@echo "Cargo version: $(shell $(CARGO) --version)"

# Quick health check
check-env:
	@echo "$(GREEN)System Check$(NC)"
	@echo "  Rust:   $(shell which rustc && echo ✅ || echo ❌)"
	@echo "  Cargo:  $(shell which cargo && echo ✅ || echo ❌)"
	@echo "  Python: $(shell which python3 && echo ✅ || echo ❌)"
	@echo "  pip3:   $(shell which pip3 && echo ✅ || echo ❌)"
	@echo ""
	@echo "Python packages:"
	@$(PYTHON) -c "import mss; print('  mss:     ✅')" 2>/dev/null || echo "  mss:     ❌"
	@$(PYTHON) -c "import PIL; print('  pillow:  ✅')" 2>/dev/null || echo "  pillow:  ❌"
	@$(PYTHON) -c "import requests; print('  requests: ✅')" 2>/dev/null || echo "  requests: ❌"
	@$(PYTHON) -c "import click; print('  click:   ✅')" 2>/dev/null || echo "  click:   ✅"

# Documentation
doc:
	@echo "$(GREEN)Building documentation...$(NC)"
	@$(CARGO) doc --workspace --no-deps --open

# Watch and rebuild on changes (requires cargo-watch)
watch:
	@echo "$(GREEN)Watching for changes...$(NC)"
	@$(CARGO) watch -x 'build --workspace'

# Update dependencies
update:
	@echo "$(GREEN)Updating dependencies...$(NC)"
	@$(CARGO) update
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

# Audit dependencies for security issues
audit:
	@echo "$(GREEN)Auditing dependencies...$(NC)"
	@$(CARGO) audit || (echo "$(YELLOW)Install cargo-audit: cargo install cargo-audit$(NC)" && exit 1)

# Build for multiple platforms (requires cross)
cross-compile:
	@echo "$(GREEN)Cross-compiling for multiple platforms...$(NC)"
	@echo "$(YELLOW)Note: Requires 'cross' tool: cargo install cross$(NC)"
	@cross build --release --target x86_64-unknown-linux-gnu
	@cross build --release --target aarch64-unknown-linux-gnu
	@cross build --release --target x86_64-apple-darwin
	@cross build --release --target aarch64-apple-darwin
	@cross build --release --target x86_64-pc-windows-gnu

# Create distributable packages
dist: release
	@echo "$(GREEN)Creating distribution packages...$(NC)"
	@mkdir -p dist
	@tar -czf dist/eye-$(VERSION)-linux-x64.tar.gz -C $(RELEASE_DIR) eye-server eye-agent
	@echo "$(GREEN)✅ Distribution package created: dist/eye-$(VERSION)-linux-x64.tar.gz$(NC)"

# Quick fix for common issues
fix:
	@echo "$(GREEN)Running cargo fix...$(NC)"
	@$(CARGO) fix --workspace --allow-dirty --allow-staged