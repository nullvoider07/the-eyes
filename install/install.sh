#!/bin/bash
# Eye Vision Capture Tool - Installation Script

set -e

# ============================================================================
# Configuration
# ============================================================================
REPO="nullvoider07/the-eyes"
INSTALL_DIR="$HOME/.local/bin"
SERVER_BINARY="eye-server"
CLI_BINARY="eye"

# ============================================================================
# Detect OS
# ============================================================================
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_TYPE="linux";;
    Darwin*)    OS_TYPE="osx";;     # CHANGED: 'darwin' -> 'osx' to match your release asset
    *)          echo "❌ Unsupported OS: ${OS}"; exit 1;;
esac

# ============================================================================
# Detect Architecture
# ============================================================================
ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64)    ARCH_TYPE="x64";;    # CHANGED: 'amd64' -> 'x64' to match your release asset
    arm64)     ARCH_TYPE="arm64";;
    aarch64)   ARCH_TYPE="arm64";;
    *)         echo "❌ Unsupported Architecture: ${ARCH}"; exit 1;;
esac

echo "Detected: ${OS_TYPE} (${ARCH_TYPE})"

# ============================================================================
# Get Latest Release
# ============================================================================
echo "Fetching latest version from GitHub..."
LATEST_TAG=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_TAG" ]; then
    echo "❌ Error: Could not find latest release."
    echo "Check: https://github.com/$REPO/releases"
    exit 1
fi

# Extract version
VERSION=${LATEST_TAG#v}
echo "Latest Version: ${VERSION}"

# ============================================================================
# Construct Download URL
# ============================================================================
# Filename format: eye-0.1.0-osx-x64.tar.gz
FILE_NAME="eye-${VERSION}-${OS_TYPE}-${ARCH_TYPE}.tar.gz"
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$LATEST_TAG/$FILE_NAME"

echo "Download URL: $DOWNLOAD_URL"

# ============================================================================
# Download Release Package
# ============================================================================
echo "Downloading Eye v${VERSION}..."
TMP_FILE="/tmp/eye-install-$$.tar.gz"

if ! curl -L -f -o "$TMP_FILE" "$DOWNLOAD_URL"; then
    echo "❌ Download failed."
    echo "Please check:"
    echo "  1. Release exists: https://github.com/$REPO/releases/tag/$LATEST_TAG"
    echo "  2. Asset exists: $FILE_NAME"
    exit 1
fi

echo "✅ Downloaded successfully"

# ============================================================================
# Extract Archive
# ============================================================================
echo "Extracting..."
TMP_DIR="/tmp/eye-extract-$$"
mkdir -p "$TMP_DIR"

tar -xzf "$TMP_FILE" -C "$TMP_DIR"

# ============================================================================
# Verify Binaries Exist
# ============================================================================
# Check both generic path and version-nested path
SOURCE_DIR="$TMP_DIR"
if [ -d "$TMP_DIR/eye-${VERSION}-${OS_TYPE}-${ARCH_TYPE}" ]; then
    SOURCE_DIR="$TMP_DIR/eye-${VERSION}-${OS_TYPE}-${ARCH_TYPE}"
elif [ -d "$TMP_DIR/eye" ]; then
    SOURCE_DIR="$TMP_DIR/eye"
fi

if [ ! -f "$SOURCE_DIR/bin/$SERVER_BINARY" ] && [ ! -f "$SOURCE_DIR/$SERVER_BINARY" ]; then
    echo "❌ Error: $SERVER_BINARY not found in package"
    ls -la "$TMP_DIR"
    exit 1
fi

# ============================================================================
# Install Binaries
# ============================================================================
echo "Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Install Server
if [ -f "$SOURCE_DIR/bin/$SERVER_BINARY" ]; then
    cp "$SOURCE_DIR/bin/$SERVER_BINARY" "$INSTALL_DIR/"
else
    cp "$SOURCE_DIR/$SERVER_BINARY" "$INSTALL_DIR/"
fi

# Install CLI
if [ -f "$SOURCE_DIR/bin/$CLI_BINARY" ]; then
    cp "$SOURCE_DIR/bin/$CLI_BINARY" "$INSTALL_DIR/"
else
    cp "$SOURCE_DIR/$CLI_BINARY" "$INSTALL_DIR/" 2>/dev/null || true
fi

# Make executable
chmod +x "$INSTALL_DIR/$SERVER_BINARY"
chmod +x "$INSTALL_DIR/$CLI_BINARY" 2>/dev/null || true

# ============================================================================
# macOS Specific: Remove Quarantine
# ============================================================================
if [[ "$OS_TYPE" == "osx" ]]; then
    echo "Removing macOS quarantine attributes..."
    xattr -d com.apple.quarantine "$INSTALL_DIR/$SERVER_BINARY" 2>/dev/null || true
    xattr -d com.apple.quarantine "$INSTALL_DIR/$CLI_BINARY" 2>/dev/null || true
fi

# ============================================================================
# Clean Up
# ============================================================================
rm -rf "$TMP_FILE" "$TMP_DIR"

# ============================================================================
# Update PATH if Needed
# ============================================================================
SHELL_CONFIG=""
case "$SHELL" in
    */zsh)  SHELL_CONFIG="$HOME/.zshrc" ;;
    */bash) SHELL_CONFIG="$HOME/.bashrc" ;;
    *)      SHELL_CONFIG="$HOME/.profile" ;;
esac

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "Adding $INSTALL_DIR to PATH in $SHELL_CONFIG..."
    echo "" >> "$SHELL_CONFIG"
    echo "# Eye Vision Capture Tool" >> "$SHELL_CONFIG"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
    
    PATH_UPDATED=true
else
    PATH_UPDATED=false
fi

# ============================================================================
# Installation Complete
# ============================================================================
echo ""
echo "========================================="
echo "✅ Eye v${VERSION} installed successfully!"
echo "========================================="
echo ""
echo "Installed binaries:"
echo "  • eye-server  → $INSTALL_DIR/$SERVER_BINARY"
echo "  • eye         → $INSTALL_DIR/$CLI_BINARY"
echo ""
echo "Quick Start:"
echo "  # Terminal 1: Start server"
echo "  eye-server"
echo ""
echo "  # Terminal 2: Start agent"
echo "  eye agent start --server http://localhost:8080 --token mytoken"
echo ""

if [ "$PATH_UPDATED" = true ]; then
    echo "⚠️  PATH updated. Apply changes with:"
    echo "  source $SHELL_CONFIG"
    echo ""
    echo "Or restart your terminal."
else
    echo "Try it now:"
    echo "  eye --help"
    echo "  eye-server --help"
fi

echo ""