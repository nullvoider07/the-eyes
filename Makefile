# Makefile for Eye Vision Capture Tool
# Builds Go binaries and Python package

.PHONY: all build clean install test deps help

# Version
VERSION := 0.1.0

# Build directories
BIN_DIR := bin
BUILD_DIR := build

# Binary names
SERVER_BIN := $(BIN_DIR)/eye-server
AGENT_BIN := $(BIN_DIR)/eye-agent

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
NC := \033[0m # No Color

all: deps build

help:
	@echo "Eye Vision Capture Tool - Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  make build         - Build all binaries (server + agent)"
	@echo "  make install       - Install Eye CLI and binaries"
	@echo "  make test          - Run all tests"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make deps          - Install dependencies"
	@echo "  make cross-compile - Build for all platforms"
	@echo "  make docker        - Build Docker images"
	@echo ""

# Install dependencies
deps:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@$(GO) mod download
	@$(PIP) install -e . --quiet
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

# Build Go binaries
build: $(SERVER_BIN) $(AGENT_BIN)
	@echo "$(GREEN)✅ Build complete$(NC)"

$(SERVER_BIN): cmd/server/main.go pkg/**/*.go
	@echo "$(GREEN)Building Eye Server...$(NC)"
	@mkdir -p $(BIN_DIR)
	@$(GO) build $(GOFLAGS) -o $(SERVER_BIN) cmd/server/main.go
	@echo "$(GREEN)✅ Server built: $(SERVER_BIN)$(NC)"

$(AGENT_BIN): cmd/agent/main.go pkg/**/*.go
	@echo "$(GREEN)Building Eye Agent...$(NC)"
	@mkdir -p $(BIN_DIR)
	@$(GO) build $(GOFLAGS) -o $(AGENT_BIN) cmd/agent/main.go
	@echo "$(GREEN)✅ Agent built: $(AGENT_BIN)$(NC)"

# Install binaries and Python package
install: build
	@echo "$(GREEN)Installing Eye...$(NC)"
	@mkdir -p /usr/local/bin
	@cp $(SERVER_BIN) /usr/local/bin/eye-server
	@cp $(AGENT_BIN) /usr/local/bin/eye-agent
	@$(PIP) install -e .
	@echo "$(GREEN)✅ Eye installed$(NC)"
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
	@$(PYTHON) -m pytest tests/ -v

# Clean build artifacts
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf $(BIN_DIR) $(BUILD_DIR)
	@rm -rf *.egg-info
	@rm -rf __pycache__ .pytest_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Clean complete$(NC)"

# Cross-compile for all platforms
cross-compile: cross-linux cross-darwin cross-windows

cross-linux:
	@echo "$(GREEN)Building for Linux (amd64)...$(NC)"
	@GOOS=linux GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/linux-amd64/eye-server cmd/server/main.go
	@GOOS=linux GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/linux-amd64/eye-agent cmd/agent/main.go
	@echo "$(GREEN)Building for Linux (arm64)...$(NC)"
	@GOOS=linux GOARCH=arm64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/linux-arm64/eye-server cmd/server/main.go
	@GOOS=linux GOARCH=arm64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/linux-arm64/eye-agent cmd/agent/main.go

cross-darwin:
	@echo "$(GREEN)Building for macOS (amd64)...$(NC)"
	@GOOS=darwin GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/darwin-amd64/eye-server cmd/server/main.go
	@GOOS=darwin GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/darwin-amd64/eye-agent cmd/agent/main.go
	@echo "$(GREEN)Building for macOS (arm64)...$(NC)"
	@GOOS=darwin GOARCH=arm64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/darwin-arm64/eye-server cmd/server/main.go
	@GOOS=darwin GOARCH=arm64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/darwin-arm64/eye-agent cmd/agent/main.go

cross-windows:
	@echo "$(GREEN)Building for Windows (amd64)...$(NC)"
	@GOOS=windows GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/windows-amd64/eye-server.exe cmd/server/main.go
	@GOOS=windows GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BUILD_DIR)/windows-amd64/eye-agent.exe cmd/agent/main.go

# Docker builds
docker: docker-server docker-agent

docker-server:
	@echo "$(GREEN)Building Eye Server Docker image...$(NC)"
	@docker build -f docker/Dockerfile.server -t eye-server:$(VERSION) .
	@docker tag eye-server:$(VERSION) eye-server:latest

docker-agent:
	@echo "$(GREEN)Building Eye Agent Docker image...$(NC)"
	@docker build -f docker/Dockerfile.agent -t eye-agent:$(VERSION) .
	@docker tag eye-agent:$(VERSION) eye-agent:latest

# Quick development testing
run-server: build
	@echo "$(GREEN)Starting Eye Server (development)...$(NC)"
	@export EYE_AUTH_TOKEN=dev-token && $(SERVER_BIN)

run-agent: build
	@echo "$(GREEN)Starting Eye Agent (development)...$(NC)"
	@export EYE_SERVER_URL=http://localhost:8080 && \
	 export EYE_AUTH_TOKEN=dev-token && \
	 $(AGENT_BIN)

# Format code
fmt:
	@echo "$(GREEN)Formatting code...$(NC)"
	@$(GO) fmt ./...
	@$(PYTHON) -m black eye/ tests/ --quiet

# Lint code
lint:
	@echo "$(GREEN)Linting code...$(NC)"
	@golangci-lint run ./...
	@$(PYTHON) -m pylint eye/

# Generate documentation
docs:
	@echo "$(GREEN)Generating documentation...$(NC)"
	@$(PYTHON) -m pdoc eye --html --output-dir docs/api

# Benchmark
bench:
	@echo "$(GREEN)Running benchmarks...$(NC)"
	@$(GO) test -bench=. -benchmem ./pkg/...

# Release build
release: clean
	@echo "$(GREEN)Building release binaries...$(NC)"
	@$(MAKE) cross-compile
	@echo "$(GREEN)Creating release archives...$(NC)"
	@cd $(BUILD_DIR) && \
		tar -czf eye-$(VERSION)-linux-amd64.tar.gz linux-amd64/ && \
		tar -czf eye-$(VERSION)-linux-arm64.tar.gz linux-arm64/ && \
		tar -czf eye-$(VERSION)-darwin-amd64.tar.gz darwin-amd64/ && \
		tar -czf eye-$(VERSION)-darwin-arm64.tar.gz darwin-arm64/ && \
		zip -r eye-$(VERSION)-windows-amd64.zip windows-amd64/
	@echo "$(GREEN)✅ Release build complete$(NC)"
	@echo "Release files in: $(BUILD_DIR)/"

# Show version
version:
	@echo "Eye Vision Capture Tool v$(VERSION)"
	@echo "Go version: $(shell $(GO) version)"
	@echo "Python version: $(shell $(PYTHON) --version)"