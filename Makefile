# Makefile for Eye Vision Capture Tool
# Builds Go server and Python agent/CLI

.PHONY: all build clean install test deps help release release-build release-test release-publish

# Version
VERSION ?= 0.1.0

# Build directories
BIN_DIR := bin
BUILD_DIR := build
RELEASE_DIR := release

# Binary names
SERVER_BIN := $(BIN_DIR)/eye-server

# Go build flags
GO := go
GOFLAGS := -ldflags="-s -w -X main.version=$(VERSION)"
GOOS := $(shell go env GOOS)
GOARCH := $(shell go env GOARCH)

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
	@echo "Eye Vision Capture Tool - Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  make build         - Build server binary + install Python CLI"
	@echo "  make install       - Install Eye CLI and binaries system-wide"
	@echo "  make test          - Run all tests"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make deps          - Install dependencies"
	@echo "  make release       - Build and test release packages"
	@echo "  make cross-compile - Build for all platforms"
	@echo ""

# Install dependencies
deps:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@$(GO) mod download
	@$(PIP) install -e . --quiet || $(PIP) install -e .
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

# Build Go server binary
build: $(SERVER_BIN) python-cli
	@echo "$(GREEN)✅ Build complete$(NC)"

$(SERVER_BIN): cmd/server/main.go
	@echo "$(GREEN)Building Eye Server...$(NC)"
	@mkdir -p $(BIN_DIR)
	@$(GO) build $(GOFLAGS) -o $(SERVER_BIN) cmd/server/main.go
	@echo "$(GREEN)✅ Server built: $(SERVER_BIN)$(NC)"

# Install Python CLI (editable mode for development)
python-cli:
	@echo "$(GREEN)Installing Python CLI...$(NC)"
	@$(PIP) install -e . --quiet 2>/dev/null || $(PIP) install -e .
	@echo "$(GREEN)✅ Python CLI installed$(NC)"

# Install binaries and Python package system-wide
install: build
	@echo "$(GREEN)Installing Eye system-wide...$(NC)"
	@mkdir -p /usr/local/bin
	@cp $(SERVER_BIN) /usr/local/bin/eye-server
	@chmod +x /usr/local/bin/eye-server
	@$(PIP) install -e .
	@echo "$(GREEN)✅ Eye installed$(NC)"
	@echo ""
	@echo "Installed commands:"
	@echo "  - eye          (Python CLI)"
	@echo "  - eye-server   (Go server binary)"
	@echo ""
	@echo "Try: eye --help"

# Development install (editable Python package)
dev-install: build
	@echo "$(GREEN)Installing Eye (development mode)...$(NC)"
	@$(PIP) install -e .
	@echo "$(GREEN)✅ Eye installed in dev mode$(NC)"

# Run tests
test: test-go test-python

test-go:
	@echo "$(GREEN)Running Go tests...$(NC)"
	@$(GO) test -v ./pkg/... -cover

test-python:
	@echo "$(GREEN)Running Python tests...$(NC)"
	@if [ -d "tests" ]; then $(PYTHON) -m pytest tests/ -v; else echo "No tests found"; fi

# Clean build artifacts
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf $(BIN_DIR) $(BUILD_DIR) $(RELEASE_DIR)
	@rm -rf *.egg-info dist
	@rm -rf __pycache__ .pytest_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Clean complete$(NC)"

# Cross-compile for all platforms
cross-compile: cross-linux cross-darwin cross-windows
	@echo "$(GREEN)✅ Cross-compilation complete$(NC)"

cross-linux:
	@echo "$(GREEN)Building for Linux...$(NC)"
	@mkdir -p $(BUILD_DIR)/linux-amd64 $(BUILD_DIR)/linux-arm64
	@GOOS=linux GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/linux-amd64/eye-server cmd/server/main.go
	@GOOS=linux GOARCH=arm64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/linux-arm64/eye-server cmd/server/main.go

cross-darwin:
	@echo "$(GREEN)Building for macOS...$(NC)"
	@mkdir -p $(BUILD_DIR)/darwin-amd64 $(BUILD_DIR)/darwin-arm64
	@GOOS=darwin GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/darwin-amd64/eye-server cmd/server/main.go
	@GOOS=darwin GOARCH=arm64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/darwin-arm64/eye-server cmd/server/main.go

cross-windows:
	@echo "$(GREEN)Building for Windows...$(NC)"
	@mkdir -p $(BUILD_DIR)/windows-amd64
	@GOOS=windows GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/windows-amd64/eye-server.exe cmd/server/main.go

# Quick development testing
run-server: build
	@echo "$(GREEN)Starting Eye Server (development)...$(NC)"
	@export EYE_AUTH_TOKEN=dev-token && $(SERVER_BIN)

run-agent: build
	@echo "$(GREEN)Starting Eye Agent (development)...$(NC)"
	@echo "$(BLUE)Note: Using Python agent$(NC)"
	@export EYE_SERVER_URL=http://localhost:8080 && \
	 export EYE_AUTH_TOKEN=dev-token && \
	 $(PYTHON) -c "from eye.agent import Agent; Agent('http://localhost:8080', 'dev-token').run()"

# Format code
fmt:
	@echo "$(GREEN)Formatting code...$(NC)"
	@$(GO) fmt ./...
	@$(PYTHON) -m black eye/ tests/ --quiet 2>/dev/null || echo "black not installed (optional)"

# Lint code
lint:
	@echo "$(GREEN)Linting code...$(NC)"
	@which golangci-lint >/dev/null && golangci-lint run ./... || echo "golangci-lint not installed (optional)"
	@$(PYTHON) -m pylint eye/ 2>/dev/null || echo "pylint not installed (optional)"

# Benchmark
bench:
	@echo "$(GREEN)Running benchmarks...$(NC)"
	@$(GO) test -bench=. -benchmem ./pkg/...

# ----------------------------------------------------------------------------
# Release Management
# ----------------------------------------------------------------------------

release-build:
	@echo "$(GREEN)Building release v$(VERSION)...$(NC)"
	@if [ ! -f scripts/build_release.sh ]; then \
		echo "$(YELLOW)Warning: scripts/build_release.sh not found$(NC)"; \
		echo "$(YELLOW)Using basic cross-compile instead$(NC)"; \
		$(MAKE) cross-compile; \
	else \
		chmod +x scripts/build_release.sh; \
		VERSION=$(VERSION) ./scripts/build_release.sh $(VERSION); \
	fi

release-test:
	@echo "$(GREEN)Testing release packages...$(NC)"
	@if [ -d $(RELEASE_DIR) ] && [ -f $(RELEASE_DIR)/SHA256SUMS ]; then \
		cd $(RELEASE_DIR) && sha256sum -c SHA256SUMS; \
	else \
		echo "$(YELLOW)No release packages found to test$(NC)"; \
	fi

release-publish:
	@echo "$(GREEN)Publishing release v$(VERSION)...$(NC)"
	@if [ ! -f scripts/publish_release.sh ]; then \
		echo "$(YELLOW)Error: scripts/publish_release.sh not found$(NC)"; \
		echo "Create this file to enable publishing"; \
		exit 1; \
	else \
		chmod +x scripts/publish_release.sh; \
		./scripts/publish_release.sh $(VERSION); \
	fi

# Main release target (Build + Test)
release: release-build release-test
	@echo ""
	@echo "$(GREEN)✅ Release $(VERSION) built and tested$(NC)"
	@echo ""
	@echo "Release artifacts:"
	@ls -lh $(RELEASE_DIR)/ 2>/dev/null || ls -lh $(BUILD_DIR)/
	@echo ""
	@echo "To publish, run:"
	@echo "  $(BLUE)make release-publish VERSION=$(VERSION)$(NC)"

# Show version and build info
version:
	@echo "$(GREEN)Eye Vision Capture Tool v$(VERSION)$(NC)"
	@echo "Go version: $(shell $(GO) version)"
	@echo "Python version: $(shell $(PYTHON) --version)"
	@echo "OS/Arch: $(GOOS)/$(GOARCH)"

# Quick health check
check:
	@echo "$(GREEN)System Check$(NC)"
	@echo "  Go:     $(shell which go && echo ✅ || echo ❌)"
	@echo "  Python: $(shell which python3 && echo ✅ || echo ❌)"
	@echo "  pip3:   $(shell which pip3 && echo ✅ || echo ❌)"
	@echo ""
	@echo "Python packages:"
	@$(PYTHON) -c "import mss; print('  mss:     ✅')" 2>/dev/null || echo "  mss:     ❌"
	@$(PYTHON) -c "import PIL; print('  pillow:  ✅')" 2>/dev/null || echo "  pillow:  ❌"
	@$(PYTHON) -c "import requests; print('  requests: ✅')" 2>/dev/null || echo "  requests: ❌"
	@$(PYTHON) -c "import click; print('  click:   ✅')" 2>/dev/null || echo "  click:   ❌"