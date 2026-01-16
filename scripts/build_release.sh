#!/bin/bash
set -e

VERSION="${1:-0.1.0}"
REPO="nullvoider07/the-eye"
BUILD_DIR="staging"
RELEASE_DIR="release"

echo "========================================="
echo "Building Eye v${VERSION}"
echo "========================================="

# Clean previous builds
rm -rf "$BUILD_DIR" "$RELEASE_DIR"
mkdir -p "$BUILD_DIR" "$RELEASE_DIR"

# Check for FPM (Required for deb/rpm/pkg)
if ! command -v fpm &> /dev/null; then
    echo "⚠️  WARNING: 'fpm' is not installed."
    echo "   .deb, .rpm, and .pkg files will NOT be generated."
    echo "   To fix: gem install fpm"
fi

# Create a common post-install script for system packages
# This ensures dependencies are installed after the .deb/.rpm/.pkg is installed
mkdir -p scripts
cat > scripts/postinstall.sh << 'EOF'
#!/bin/sh
if command -v pip3 >/dev/null; then
    pip3 install mss pillow requests click pyyaml || true
fi
EOF
chmod +x scripts/postinstall.sh

# ============================================================================
# Build Go Binaries (Server)
# ============================================================================

echo "[1/6] Building Go server binaries..."

platforms=(
    "linux/amd64"
    "linux/arm64"
    "darwin/amd64"
    "darwin/arm64"
    "windows/amd64"
)

for platform in "${platforms[@]}"; do
    IFS='/' read -r GOOS GOARCH <<< "$platform"
    
    output="eye-server"
    if [ "$GOOS" = "windows" ]; then
        output="eye-server.exe"
    fi
    
    echo "  Building for $GOOS/$GOARCH..."
    
    GOOS=$GOOS GOARCH=$GOARCH go build \
        -ldflags="-s -w -X main.version=${VERSION}" \
        -o "$BUILD_DIR/${GOOS}_${GOARCH}/$output" \
        cmd/server/main.go
done

# ============================================================================
# Package Python Components
# ============================================================================

echo "[2/6] Packaging Python components..."

# Create source distribution
python3 setup.py sdist bdist_wheel

# Copy to build dir
cp dist/*.whl "$BUILD_DIR/"
cp dist/*.tar.gz "$BUILD_DIR/"

# ============================================================================
# Create Platform-Specific Packages
# ============================================================================

echo "[3/6] Creating platform packages..."

create_package() {
    local os=$1
    local arch=$2
    local pkg_name="eye-${VERSION}-${os}-${arch}"
    local pkg_dir="$BUILD_DIR/$pkg_name"
    
    # --- Standard Tarball/Zip Setup (Preserved) ---
    mkdir -p "$pkg_dir/bin"
    mkdir -p "$pkg_dir/lib"
    mkdir -p "$pkg_dir/scripts"
    
    # Copy Go binary
    if [ "$os" = "windows" ]; then
        cp "$BUILD_DIR/${os}_${arch}/eye-server.exe" "$pkg_dir/bin/"
    else
        cp "$BUILD_DIR/${os}_${arch}/eye-server" "$pkg_dir/bin/"
        chmod +x "$pkg_dir/bin/eye-server"
    fi
    
    # Copy Python package
    cp eye/*.py "$pkg_dir/lib/"
    cp -r eye/core "$pkg_dir/lib/" 2>/dev/null || true
    cp -r eye/integrations "$pkg_dir/lib/" 2>/dev/null || true
    cp -r eye/utils "$pkg_dir/lib/" 2>/dev/null || true
    
    # Copy config
    cp -r config "$pkg_dir/"
    
    # Create install script
    if [ "$os" != "windows" ]; then
        create_unix_installer "$pkg_dir" "$os"
    else
        create_windows_installer "$pkg_dir"
    fi
    
    # Create README
    create_package_readme "$pkg_dir" "$os" "$arch"
    
    # --- Generate Primary Archive (.zip / .tar.gz) ---
    if [ "$os" = "windows" ]; then
        (cd "$BUILD_DIR" && zip -r "$RELEASE_DIR/${pkg_name}.zip" "$pkg_name")
        echo "  ✓ Created ${pkg_name}.zip"
    else
        tar -czf "$RELEASE_DIR/${pkg_name}.tar.gz" -C "$BUILD_DIR" "$pkg_name"
        echo "  ✓ Created ${pkg_name}.tar.gz"
    fi

    # --- NEW: Generate System Packages (.deb, .rpm, .pkg) ---
    if command -v fpm >/dev/null && [ "$os" != "windows" ]; then
        local fpm_root="$BUILD_DIR/fpm_${pkg_name}"
        
        # 1. Create System Directory Structure (FHS Compliant)
        mkdir -p "$fpm_root/usr/local/bin"
        mkdir -p "$fpm_root/usr/local/lib/eye"
        
        # 2. Copy Files to System Paths
        cp "$pkg_dir/bin/eye-server" "$fpm_root/usr/local/bin/"
        cp -r "$pkg_dir/lib/"* "$fpm_root/usr/local/lib/eye/"
        
        # 3. Create System Wrapper Script
        # (This differs from the tarball installer; it must point to the absolute path)
        cat > "$fpm_root/usr/local/bin/eye" << 'WRAPPER_EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/local/lib/eye')
from cli import main
main()
WRAPPER_EOF
        chmod +x "$fpm_root/usr/local/bin/eye"

        # 4. Build Linux Packages
        if [ "$os" = "linux" ]; then
            # DEB
            fpm -s dir -t deb \
                -n eye -v "${VERSION}" -a "$arch" \
                --description "Eye Vision Capture Tool" \
                --url "https://github.com/$REPO" \
                -C "$fpm_root" \
                -p "$RELEASE_DIR/${pkg_name}.deb" \
                --after-install scripts/postinstall.sh \
                usr/local/bin usr/local/lib
            echo "  ✓ Created ${pkg_name}.deb"

            # RPM
            fpm -s dir -t rpm \
                -n eye -v "${VERSION}" -a "$arch" \
                --description "Eye Vision Capture Tool" \
                --url "https://github.com/$REPO" \
                -C "$fpm_root" \
                -p "$RELEASE_DIR/${pkg_name}.rpm" \
                --after-install scripts/postinstall.sh \
                usr/local/bin usr/local/lib
            echo "  ✓ Created ${pkg_name}.rpm"
        fi

        # 5. Build macOS Packages
        if [ "$os" = "darwin" ]; then
            # PKG
            fpm -s dir -t osxpkg \
                -n eye -v "${VERSION}" -a "$arch" \
                --identifier "com.nullvoider07.eye" \
                --description "Eye Vision Capture Tool" \
                -C "$fpm_root" \
                -p "$RELEASE_DIR/${pkg_name}.pkg" \
                usr/local/bin usr/local/lib
            echo "  ✓ Created ${pkg_name}.pkg"
        fi

        # Cleanup FPM staging
        rm -rf "$fpm_root"
    fi
}

create_unix_installer() {
    local pkg_dir=$1
    local os=$2
    
    cat > "$pkg_dir/install.sh" << 'INSTALLER_EOF'
#!/bin/bash
set -e

echo "Installing Eye Vision Capture Tool..."

INSTALL_DIR="${INSTALL_DIR:-/usr/local}"
BIN_DIR="$INSTALL_DIR/bin"
LIB_DIR="$INSTALL_DIR/lib/eye"

# Check permissions
if [ ! -w "$INSTALL_DIR" ]; then
    echo "Error: Need write permission to $INSTALL_DIR"
    echo "Run with sudo or set INSTALL_DIR to writable location"
    exit 1
fi

# Install Go binary
echo "[1/3] Installing server binary..."
mkdir -p "$BIN_DIR"
cp bin/eye-server "$BIN_DIR/"
chmod +x "$BIN_DIR/eye-server"

# Install Python library
echo "[2/3] Installing Python library..."
mkdir -p "$LIB_DIR"
cp -r lib/* "$LIB_DIR/"

# Install Python package
echo "[3/3] Installing Python CLI..."
if command -v pip3 &> /dev/null; then
    pip3 install mss pillow requests click pyyaml
    
    # Create wrapper script
    cat > "$BIN_DIR/eye" << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '$LIB_DIR')
from cli import main
main()
EOF
    chmod +x "$BIN_DIR/eye"
else
    echo "Warning: pip3 not found. Install Python dependencies manually:"
    echo "  pip3 install mss pillow requests click pyyaml"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Installed to: $INSTALL_DIR"
echo "  - eye-server: $BIN_DIR/eye-server"
echo "  - eye CLI: $BIN_DIR/eye"
echo ""
echo "Try: eye --help"
INSTALLER_EOF
    
    chmod +x "$pkg_dir/install.sh"
}

create_windows_installer() {
    local pkg_dir=$1
    
    cat > "$pkg_dir/install.bat" << 'INSTALLER_EOF'
@echo off
echo Installing Eye Vision Capture Tool...

set INSTALL_DIR=%ProgramFiles%\Eye

echo [1/2] Installing server binary...
if not exist "%INSTALL_DIR%\bin" mkdir "%INSTALL_DIR%\bin"
copy bin\eye-server.exe "%INSTALL_DIR%\bin\"

echo [2/2] Installing Python library...
if not exist "%INSTALL_DIR%\lib" mkdir "%INSTALL_DIR%\lib"
xcopy /E /I lib "%INSTALL_DIR%\lib"

echo.
echo Installation complete!
echo.
echo Installed to: %INSTALL_DIR%
echo.
echo Add to PATH: %INSTALL_DIR%\bin
echo.
echo Install Python dependencies:
echo    pip install mss pillow requests click pyyaml
pause
INSTALLER_EOF
}

create_package_readme() {
    local pkg_dir=$1
    local os=$2
    local arch=$3
    
    cat > "$pkg_dir/README.txt" << README_EOF
Eye Vision Capture Tool v${VERSION}
Platform: ${os}/${arch}

INSTALLATION
============

Unix/Linux/macOS:
  ./install.sh

Windows:
  Run install.bat as Administrator

QUICK START
===========

1. Start server:
   eye-server
   
   Or with auth:
   export EYE_AUTH_TOKEN="your-token"
   eye-server

2. Start agent:
   eye agent start --server http://localhost:8080 --token TOKEN

3. Test:
   curl http://localhost:8080/health

DOCUMENTATION
=============

Full documentation: https://github.com/${REPO}

System Requirements:
- Python 3.11+
- For capture: Display server (X11/Wayland/native)
- Linux: gnome-screenshot or flameshot
- Dependencies: mss, pillow, requests, click, pyyaml

LICENSE
=======

MIT License - See https://github.com/${REPO}/blob/main/LICENSE
README_EOF
}

# Build all platforms
for platform in "${platforms[@]}"; do
    IFS='/' read -r os arch <<< "$platform"
    create_package "$os" "$arch"
done

# ============================================================================
# Create Universal Installer Script
# ============================================================================

echo "[4/6] Creating universal installer..."

cat > "$RELEASE_DIR/install.sh" << 'UNIVERSAL_INSTALLER_EOF'
#!/bin/bash
# Eye Universal Installer
# Detects platform and downloads appropriate version

set -e

VERSION="${VERSION:-latest}"
REPO="nullvoider07/the-eye"
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

echo "Detected: $OS/$ARCH"

# Download URL
if [ "$VERSION" = "latest" ]; then
    DOWNLOAD_URL="https://github.com/$REPO/releases/latest/download/eye-${OS}-${ARCH}.tar.gz"
else
    DOWNLOAD_URL="https://github.com/$REPO/releases/download/v${VERSION}/eye-${VERSION}-${OS}-${ARCH}.tar.gz"
fi

echo "Downloading Eye..."
curl -L "$DOWNLOAD_URL" -o /tmp/eye.tar.gz

echo "Extracting..."
tar -xzf /tmp/eye.tar.gz -C /tmp

echo "Installing..."
cd /tmp/eye-*
./install.sh

echo "Cleaning up..."
rm -rf /tmp/eye*

echo "✅ Eye installed successfully!"
UNIVERSAL_INSTALLER_EOF

chmod +x "$RELEASE_DIR/install.sh"

# ============================================================================
# Create Checksums
# ============================================================================

echo "[5/6] Creating checksums..."

cd "$RELEASE_DIR"
sha256sum * > SHA256SUMS
cd -

# ============================================================================
# Create Release Notes
# ============================================================================

echo "[6/6] Creating release notes..."

cat > "$RELEASE_DIR/RELEASE_NOTES.md" << NOTES_EOF
# Eye v${VERSION}

Vision capture tool for AI/CUA workflows.

## What's New

- Cross-platform support (Linux, macOS, Windows)
- PNG and JPEG capture formats
- Configurable quality settings
- Auto-stop via duration or frame limits
- Wayland and X11 support
- OAuth-ready authentication
- Memory-optimized ring buffer

## Installation

### Quick Install (Unix/Linux/macOS)

\`\`\`bash
curl -sSL https://raw.githubusercontent.com/$REPO/main/install.sh | bash
\`\`\`

### Manual Download

Download the appropriate package for your platform and run the installer.

### From Source

\`\`\`bash
git clone https://github.com/$REPO
cd eye
make build
sudo make install
\`\`\`

## Usage

\`\`\`bash
# Start server
eye-server

# Start agent
eye agent start --server http://localhost:8080

# With all options
eye agent start \\
  --server http://localhost:8080 \\
  --token TOKEN \\
  --interval 2.0 \\
  --format jpeg \\
  --quality 85 \\
  --duration 300
\`\`\`

## Checksums

See SHA256SUMS file for package verification.

## Support

- Issues: https://github.com/$REPO/issues
- Documentation: https://github.com/$REPO#readme
NOTES_EOF

echo ""
echo "========================================="
echo "Build Complete!"
echo "========================================="
echo "Release files in: $RELEASE_DIR/"
ls -lh "$RELEASE_DIR"