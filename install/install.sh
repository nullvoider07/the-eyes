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
    Darwin*)    OS_TYPE="osx";;
    *)          echo "❌ Unsupported OS: ${OS}"; exit 1;;
esac

# ============================================================================
# Detect Architecture
# ============================================================================
ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64)    ARCH_TYPE="x64";;
    arm64)     ARCH_TYPE="arm64";;
    aarch64)   ARCH_TYPE="arm64";;
    *)         echo "❌ Unsupported Architecture: ${ARCH}"; exit 1;;
esac

# --- NEW: Check for Rosetta (macOS) ---
# If we are on macOS and detected x64, check if we are actually on Apple Silicon
if [[ "$OS_TYPE" == "osx" && "$ARCH_TYPE" == "x64" ]]; then
    if [[ $(sysctl -n sysctl.proc_translated 2>/dev/null) == "1" ]]; then
        echo "⚠️  Rosetta environment detected."
        echo "   Switching to native ARM64 build for better performance."
        ARCH_TYPE="arm64"
    fi
fi

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

VERSION=${LATEST_TAG#v}
echo "Latest Version: ${VERSION}"

# ============================================================================
# Download Release Package (With Fallback)
# ============================================================================
TMP_FILE="/tmp/eye-install-$$.tar.gz"

# Function to try downloading a specific filename
try_download() {
    local os=$1
    local arch=$2
    local filename="eye-${VERSION}-${os}-${arch}.tar.gz"
    local url="https://github.com/$REPO/releases/download/$LATEST_TAG/$filename"
    
    echo "Attempting download: $filename"
    if curl -L -f -s -o "$TMP_FILE" "$url"; then
        return 0
    else
        return 1
    fi
}

# 1. Try Primary (e.g., eye-0.1.0-osx-x64.tar.gz)
if try_download "$OS_TYPE" "$ARCH_TYPE"; then
    echo "✅ Downloaded successfully"

# 2. Try Fallback Naming (e.g., eye-0.1.0-darwin-amd64.tar.gz)
#    (Handles cases where build script uses standard Go naming)
elif [ "$OS_TYPE" == "osx" ] && try_download "darwin" "amd64"; then
    echo "✅ Downloaded successfully (using 'darwin-amd64' fallback)"
    
elif [ "$ARCH_TYPE" == "x64" ] && try_download "$OS_TYPE" "amd64"; then
    echo "✅ Downloaded successfully (using 'amd64' fallback)"

else
    echo "❌ Download failed."
    echo "Could not find a release asset for your platform."
    echo "Tried: eye-${VERSION}-${OS_TYPE}-${ARCH_TYPE}.tar.gz"
    exit 1
fi

# ============================================================================
# Extract Archive
# ============================================================================
echo "Extracting..."
TMP_DIR="/tmp/eye-extract-$$"
mkdir -p "$TMP_DIR"

tar -xzf "$TMP_FILE" -C "$TMP_DIR"

# ============================================================================
# Verify & Install
# ============================================================================
# Smart search for binaries in extracted folder
find_binary() {
    local name=$1
    find "$TMP_DIR" -type f -name "$name" | head -n 1
}

SERVER_PATH=$(find_binary "$SERVER_BINARY")
CLI_PATH=$(find_binary "$CLI_BINARY")

if [ -z "$SERVER_PATH" ]; then
    echo "❌ Error: Could not find $SERVER_BINARY in the package."
    exit 1
fi

echo "Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

cp "$SERVER_PATH" "$INSTALL_DIR/"
[ -n "$CLI_PATH" ] && cp "$CLI_PATH" "$INSTALL_DIR/"

chmod +x "$INSTALL_DIR/$SERVER_BINARY"
[ -n "$CLI_PATH" ] && chmod +x "$INSTALL_DIR/$CLI_BINARY"

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
# Update PATH
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
# Done
# ============================================================================
echo ""
echo "========================================="
echo "✅ Eye v${VERSION} installed successfully!"
echo "========================================="
echo ""
if [ "$PATH_UPDATED" = true ]; then
    echo "⚠️  PATH updated. Please restart your terminal or run:"
    echo "  source $SHELL_CONFIG"
else
    echo "Run 'eye --help' to get started."
fi
echo ""