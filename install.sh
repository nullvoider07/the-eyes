#!/bin/bash
# Eye One-Line Installer
# Usage: curl -sSL https://raw.githubusercontent.com/nullvoider07/the-eye/main/install.sh | bash

set -e

echo "========================================="
echo "Eye Vision Capture Tool - Installer"
echo "========================================="

# Configuration
REPO="nullvoider07/the-eye"
VERSION="${VERSION:-latest}"
INSTALL_DIR="${INSTALL_DIR:-/usr/local}"

# Detect platform
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64)  ARCH="amd64" ;;
    aarch64) ARCH="arm64" ;;
    arm64)   ARCH="arm64" ;;
    *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

case "$OS" in
    linux|darwin) ;;
    *)           echo "Unsupported OS: $OS"; exit 1 ;;
esac

echo "Detected platform: $OS/$ARCH"

# Determine download URL
if [ "$VERSION" = "latest" ]; then
    echo "Fetching latest release..."
    VERSION=$(curl -sSL "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | cut -d'"' -f4)
    VERSION=${VERSION#v}
fi

PACKAGE="eye-${VERSION}-${OS}-${ARCH}.tar.gz"
DOWNLOAD_URL="https://github.com/$REPO/releases/download/v${VERSION}/$PACKAGE"

echo "Downloading Eye v${VERSION}..."
echo "URL: $DOWNLOAD_URL"

# Download and extract
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

if ! curl -sSL "$DOWNLOAD_URL" -o eye.tar.gz; then
    echo "Error: Failed to download"
    exit 1
fi

echo "Extracting..."
tar -xzf eye.tar.gz

# Run installer
cd eye-*
export INSTALL_DIR
chmod +x install.sh
./install.sh

# Cleanup
cd /
rm -rf "$TMP_DIR"

echo ""
echo "========================================="
echo "✅ Eye installed successfully!"
echo "========================================="
echo ""
echo "Try: eye --help"
echo "      eye-server"
echo ""