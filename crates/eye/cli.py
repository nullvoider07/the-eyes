import click
import yaml
import os
import subprocess
import requests
import sys
import platform
import tempfile
import shutil
import stat
from pathlib import Path
from eye.agent import Agent

# Define configuration paths
CONFIG_DIR = Path.home() / ".eye"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Version - Update with each release
__version__ = "0.2.0"

# GitHub repository
REPO = "nullvoider07/the-eyes"

# CLI Group
@click.group()
@click.version_option(version=__version__, prog_name="Eye Vision Capture Tool")
def cli():
    """Eye - Vision capture tool"""
    pass

# Server Commands
@cli.group()
def server():
    """Manage server"""
    pass

# Start Server Command
@server.command(name='start')
@click.option('--port', default=8080, help='Server port')
@click.option('--token', help='Auth token')
def start_server(port, token):
    """Start Rust server"""
    click.echo(f"[START] Starting Eye Server (Rust) on port {port}")
    
    env = os.environ.copy()
    env['EYE_PORT'] = str(port)
    if token:
        env['EYE_AUTH_TOKEN'] = token
    
    # Check for binary in multiple locations
    server_bin = None
    possible_locations = [
        "./bin/eye-server",
        "./target/release/eye-server",
        str(Path.home() / ".local" / "bin" / "eye-server"),
        "/usr/local/bin/eye-server",
        "eye-server",
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            server_bin = location
            click.echo(f"[INFO] Found server binary at: {location}")
            break
    
    if not server_bin:
        server_bin = "eye-server"
    
    try:
        click.echo(f"[INFO] Starting server: {server_bin}")
        subprocess.run([server_bin], env=env, check=True)
    except FileNotFoundError:
        click.echo("[ERROR] 'eye-server' binary not found!", err=True)
        click.echo("", err=True)
        click.echo("Build the Rust server with:", err=True)
        click.echo("  cd /path/to/the-eyes", err=True)
        click.echo("  cargo build --release -p eye-server", err=True)
        click.echo("", err=True)
        click.echo("Or install system-wide with:", err=True)
        click.echo("  make install", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n[INFO] Server stopped")

# Agent Commands
@cli.group()
def agent():
    """Manage agent"""
    pass

# Start Agent Command - ALREADY COMPATIBLE
@agent.command(name='start')
@click.option('--server', required=True, help='Server URL (e.g. http://localhost:8080)')
@click.option('--token', help='Auth token')
@click.option('--interval', type=float, default=1.5, help='Capture interval (seconds)')
@click.option('--format', type=click.Choice(['png', 'jpeg', 'webp', 'bmp', 'tiff']), default='png', help='Image format')
@click.option('--quality', type=int, default=95, help='Compression quality (1-100)')
@click.option('--duration', type=int, help='Auto-stop after N seconds')
@click.option('--max-frames', type=int, help='Auto-stop after N frames')
@click.option('--notify/--no-notify', default=True, help='Show or hide desktop notifications')
def start_agent(server, token, interval, format, quality, duration, max_frames, notify):
    """Start Python capture agent (compatible with Rust server)"""
    
    # Dependency Check
    try:
        import mss
        from PIL import Image
    except ImportError:
        click.echo("Missing dependencies. Run: pip install mss pillow requests", err=True)
        sys.exit(1)

    click.echo(f"[START] Starting Eye Agent (Python) -> {server}")
    click.echo(f"   Format: {format.upper()}")
    if format == 'jpeg':
        click.echo(f"   Quality: {quality}/100")
    click.echo(f"   Interval: {interval}s")
    if duration:
        click.echo(f"   Duration: {duration}s (auto-stop)")
    if max_frames:
        click.echo(f"   Max frames: {max_frames} (auto-stop)")
    click.echo(f"   Server: Rust-based Eye Server")

    try:
        # Run the Python Agent with all parameters
        bot = Agent(
            server_url=server,
            token=token,
            interval=interval,
            format=format,
            quality=quality,
            duration=duration,
            max_frames=max_frames,
            notify=notify
        )
        bot.run()
    except KeyboardInterrupt:
        click.echo("\nStopping...")

# Debug Command - COMPATIBLE
@cli.command()
def debug():
    """Show debug info from Rust server"""
    try:
        r = requests.get('http://localhost:8080/debug', timeout=2)
        click.echo(yaml.dump(r.json()))
    except:
        click.echo("[ERROR] Server not running or unreachable", err=True)

# Update Command
@cli.command()
@click.option('--check-only', is_flag=True, help='Only check for updates without installing')
def update(check_only):
    """Check for updates and install the latest version (Rust binaries)"""
    
    click.echo("Checking for updates...")
    click.echo(f"Current version: v{__version__}")
    
    try:
        # Get latest release from GitHub
        release_url = f"https://api.github.com/repos/{REPO}/releases/latest"
        response = requests.get(release_url, timeout=10)
        response.raise_for_status()
        
        latest_release = response.json()
        latest_tag = latest_release['tag_name']
        latest_version = latest_tag.lstrip('v')
        
        click.echo(f"Latest version: v{latest_version}")
        
        # Compare versions
        if latest_version == __version__:
            click.echo(click.style("[OK] You already have the latest version!", fg='green'))
            return
        
        click.echo(click.style(f"[UPDATE] New version available: v{latest_version}", fg='yellow'))
        
        if check_only:
            click.echo("\nTo install the update, run: eye update")
            return
        
        # Confirm update
        if not click.confirm('\nDo you want to update now?'):
            click.echo("Update cancelled.")
            return
        
        # Detect platform and architecture
        os_type = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map platform names
        if os_type == 'darwin':
            os_name = 'osx'
        elif os_type == 'linux':
            os_name = 'linux'
        elif os_type == 'windows':
            os_name = 'win'
        else:
            click.echo(f"[ERROR] Unsupported OS: {os_type}", err=True)
            return
        
        # Map architecture
        if machine in ['x86_64', 'amd64']:
            arch = 'x64'
        elif machine in ['arm64', 'aarch64']:
            arch = 'arm64'
        elif machine in ['i386', 'i686']:
            arch = 'x86'
        else:
            click.echo(f"[ERROR] Unsupported architecture: {machine}", err=True)
            return
        
        # Construct download URL for RUST binaries
        if os_name == 'win':
            file_name = f"eye-{latest_version}-{os_name}-{arch}.zip"
        else:
            file_name = f"eye-{latest_version}-{os_name}-{arch}.tar.gz"
        
        download_url = f"https://github.com/{REPO}/releases/download/{latest_tag}/{file_name}"
        
        click.echo(f"\nDownloading {file_name}...")
        
        # Download the release
        download_response = requests.get(download_url, stream=True, timeout=30)
        download_response.raise_for_status()
        
        # Save to temp file
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, file_name)
        
        with open(temp_file, 'wb') as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        click.echo("[OK] Download complete")
        
        # Extract archive
        click.echo("Installing update...")
        
        if os_name == 'win':
            import zipfile
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        else:
            import tarfile
            with tarfile.open(temp_file, 'r:gz') as tar_ref:
                tar_ref.extractall(temp_dir)
        
        # Determine installation directory
        if os_name == 'win':
            install_dir = Path(os.environ['LOCALAPPDATA']) / 'Programs' / 'Eye' / 'bin'
        else:
            install_dir = Path.home() / '.local' / 'bin'
        
        # Find the extracted binaries
        extracted_bin_dir = Path(temp_dir) / 'bin'
        
        if not extracted_bin_dir.exists():
            click.echo("[ERROR] Binary directory not found in archive", err=True)
            shutil.rmtree(temp_dir)
            return
        
        # Copy binaries to installation directory
        install_dir.mkdir(parents=True, exist_ok=True)
        
        if os_name == 'win':
            binaries = ['eye.exe', 'eye-server.exe', 'eye-agent.exe']
        else:
            binaries = ['eye', 'eye-server', 'eye-agent']
        
        for binary in binaries:
            src = extracted_bin_dir / binary
            dst = install_dir / binary
            
            if src.exists():
                if os_name == 'win' and dst.exists():
                    try:
                        # Rename old binary
                        old_binary = install_dir / f"{binary}.old"
                        if old_binary.exists():
                            old_binary.unlink()
                        dst.rename(old_binary)
                    except Exception as e:
                        click.echo(f"[WARNING] Could not replace {binary}: {e}", err=True)
                        click.echo("The binary might be in use. Please close all Eye processes and try again.", err=True)
                        continue
                
                shutil.copy2(src, dst)
                
                # Make executable on Unix-like systems
                if os_name != 'win':
                    os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                
                click.echo(f"[OK] Updated {binary}")
            else:
                click.echo(f"[WARNING] {binary} not found in archive", err=True)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        # Remove old binaries on Windows
        if os_name == 'win':
            for binary in binaries:
                old_binary = install_dir / f"{binary}.old"
                if old_binary.exists():
                    try:
                        old_binary.unlink()
                    except:
                        pass
        
        click.echo("\n" + "=" * 50)
        click.echo(click.style(f"[OK] Successfully updated to v{latest_version}!", fg='green'))
        click.echo("=" * 50)
        click.echo("\nRestart any running Eye processes to use the new version.")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"[ERROR] Network error: {e}", err=True)
        click.echo("Please check your internet connection and try again.", err=True)
    except Exception as e:
        click.echo(f"[ERROR] Update failed: {e}", err=True)
        import traceback
        traceback.print_exc()

@cli.command()
@click.option('--purge', is_flag=True, help='Also remove configuration files and data')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
def uninstall(purge, yes):
    """Uninstall Eye Vision Capture Tool from your system"""
    
    click.echo("=" * 60)
    click.echo("Eye Vision Capture Tool - Uninstall")
    click.echo("=" * 60)
    click.echo("")
    
    # Detect OS
    os_type = platform.system().lower()
    
    # Define paths to check
    paths_to_remove = []
    
    # 1. Rust binaries
    if os_type == 'windows':
        binary_locations = [
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Eye' / 'bin',
            Path.home() / '.local' / 'bin',
        ]
        binary_names = ['eye-server.exe', 'eye-agent.exe']
    else:
        binary_locations = [
            Path('/usr/local/bin'),
            Path.home() / '.local' / 'bin',
            Path('./bin'),
            Path('./target/release'),
        ]
        binary_names = ['eye-server', 'eye-agent']
    
    # Find installed binaries
    found_binaries = []
    for location in binary_locations:
        if location.exists():
            for binary in binary_names:
                binary_path = location / binary
                if binary_path.exists():
                    found_binaries.append(binary_path)
                    paths_to_remove.append(binary_path)
                
                # Also check for .old versions
                old_binary = location / f"{binary}.old"
                if old_binary.exists():
                    paths_to_remove.append(old_binary)
    
    # 2. Python package
    python_package_info = None
    try:
        import pkg_resources
        try:
            dist = pkg_resources.get_distribution('eye-capture')
            python_package_info = {
                'name': dist.project_name,
                'version': dist.version,
                'location': dist.location
            }
        except pkg_resources.DistributionNotFound:
            pass
    except ImportError:
        pass
    
    # 3. Configuration files (only if --purge)
    config_paths = []
    if purge:
        config_dir = Path.home() / '.eye'
        if config_dir.exists():
            config_paths.append(config_dir)
    
    # Display what will be removed
    click.echo("The following components will be removed:")
    click.echo("")
    
    if found_binaries:
        click.echo(click.style("Rust Binaries:", fg='yellow', bold=True))
        for binary in found_binaries:
            click.echo(f"  - {binary}")
        click.echo("")
    else:
        click.echo(click.style("Rust Binaries:", fg='yellow', bold=True))
        click.echo("  - None found")
        click.echo("")
    
    if python_package_info:
        click.echo(click.style("Python Package:", fg='yellow', bold=True))
        click.echo(f"  - {python_package_info['name']} v{python_package_info['version']}")
        click.echo(f"    Location: {python_package_info['location']}")
        click.echo("")
    else:
        click.echo(click.style("Python Package:", fg='yellow', bold=True))
        click.echo("  - Not installed via pip")
        click.echo("")
    
    if config_paths:
        click.echo(click.style("Configuration & Data:", fg='yellow', bold=True))
        for path in config_paths:
            click.echo(f"  - {path}")
        click.echo("")
    
    # Calculate total size
    total_size = 0
    for path in paths_to_remove + config_paths:
        if path.exists():
            if path.is_file():
                total_size += path.stat().st_size
            elif path.is_dir():
                total_size += sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    
    if total_size > 0:
        size_mb = total_size / (1024 * 1024)
        click.echo(f"Total disk space to be freed: {size_mb:.2f} MB")
        click.echo("")
    
    # Nothing to remove
    if not found_binaries and not python_package_info and not config_paths:
        click.echo(click.style("✓ Eye is not installed on this system", fg='green'))
        return
    
    # Confirm removal
    if not yes:
        click.echo(click.style("⚠ This action cannot be undone!", fg='red', bold=True))
        if not click.confirm('Do you want to continue?'):
            click.echo("\nUninstall cancelled.")
            return
    
    click.echo("")
    click.echo("Uninstalling...")
    click.echo("")
    
    # Track what was removed
    removed = []
    failed = []
    
    # 1. Remove Rust binaries
    for binary_path in paths_to_remove:
        try:
            if binary_path.exists():
                binary_path.unlink()
                removed.append(str(binary_path))
                click.echo(f"  ✓ Removed: {binary_path}")
        except PermissionError:
            failed.append((str(binary_path), "Permission denied"))
            click.echo(click.style(f"  ✗ Failed: {binary_path} (Permission denied)", fg='red'))
        except Exception as e:
            failed.append((str(binary_path), str(e)))
            click.echo(click.style(f"  ✗ Failed: {binary_path} ({e})", fg='red'))
    
    # 2. Uninstall Python package
    if python_package_info:
        try:
            click.echo(f"\n  Uninstalling Python package: {python_package_info['name']}...")
            import subprocess
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', 'eye-capture'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                removed.append(f"Python package: {python_package_info['name']}")
                click.echo(f"  ✓ Uninstalled Python package")
            else:
                failed.append(("Python package", result.stderr))
                click.echo(click.style(f"  ✗ Failed to uninstall Python package", fg='red'))
        except Exception as e:
            failed.append(("Python package", str(e)))
            click.echo(click.style(f"  ✗ Failed: {e}", fg='red'))
    
    # 3. Remove configuration (if --purge)
    if config_paths:
        click.echo("")
        for config_path in config_paths:
            try:
                if config_path.exists():
                    if config_path.is_dir():
                        shutil.rmtree(config_path)
                    else:
                        config_path.unlink()
                    removed.append(str(config_path))
                    click.echo(f"  ✓ Removed: {config_path}")
            except Exception as e:
                failed.append((str(config_path), str(e)))
                click.echo(click.style(f"  ✗ Failed: {config_path} ({e})", fg='red'))
    
    # 4. Remove empty parent directories (Windows)
    if os_type == 'windows':
        eye_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Eye'
        try:
            if eye_dir.exists() and not any(eye_dir.iterdir()):
                eye_dir.rmdir()
                click.echo(f"  ✓ Removed empty directory: {eye_dir}")
        except Exception:
            pass
    
    # Summary
    click.echo("")
    click.echo("=" * 60)
    
    if removed and not failed:
        click.echo(click.style("✓ Uninstall completed successfully!", fg='green', bold=True))
        click.echo("")
        click.echo(f"Removed {len(removed)} item(s):")
        for item in removed[:5]:
            click.echo(f"  - {item}")
        if len(removed) > 5:
            click.echo(f"  ... and {len(removed) - 5} more")
    
    elif removed and failed:
        click.echo(click.style("⚠ Uninstall partially completed", fg='yellow', bold=True))
        click.echo("")
        click.echo(f"Successfully removed: {len(removed)} item(s)")
        click.echo(f"Failed to remove: {len(failed)} item(s)")
        click.echo("")
        click.echo("Failed items:")
        for path, error in failed:
            click.echo(f"  - {path}: {error}")
        click.echo("")
        if os_type != 'windows':
            click.echo("Tip: Try running with sudo for system-wide installations:")
            click.echo("  sudo eye uninstall -y")
    
    elif not removed and failed:
        click.echo(click.style("✗ Uninstall failed", fg='red', bold=True))
        click.echo("")
        for path, error in failed:
            click.echo(f"  - {path}: {error}")
    
    else:
        click.echo(click.style("✓ Nothing to remove", fg='green'))
    
    click.echo("=" * 60)
    
    # Offer feedback
    if removed or failed:
        click.echo("")
        click.echo("Thank you for using Eye Vision Capture Tool!")
        click.echo("I'd appreciate your feedback: https://github.com/nullvoider07/the-eyes/issues")

# Version Command
@cli.command()
def version():
    """Show detailed version information"""
    import platform
    import sys
    
    click.echo("=" * 50)
    click.echo(f"Eye Vision Capture Tool v{__version__}")
    click.echo("=" * 50)
    click.echo("")
    click.echo("Components:")
    click.echo(f"  * Python CLI:  v{__version__}")
    
    # Try to get Rust server version
    try:
        # Look for Rust binary
        possible_locations = [
            "./target/release/eye-server",
            str(Path.home() / ".local" / "bin" / "eye-server"),
            "/usr/local/bin/eye-server",
            "eye-server"
        ]
        
        server_bin = None
        for location in possible_locations:
            if os.path.exists(location):
                server_bin = location
                break
        
        if not server_bin:
            server_bin = "eye-server"
        
        if os.path.exists(server_bin) or shutil.which(server_bin):
            click.echo(f"  * Rust Server: (installed at {server_bin})")
        else:
            click.echo(f"  * Rust Server: (not found)")
    except Exception:
        click.echo(f"  * Rust Server: (not found)")
    
    click.echo("")
    click.echo("System Information:")
    click.echo(f"  * OS:          {platform.system()} {platform.release()}")
    click.echo(f"  * Architecture: {platform.machine()}")
    click.echo(f"  * Python:      {sys.version.split()[0]}")
    
    # Check dependencies
    click.echo("")
    click.echo("Dependencies:")
    
    deps = {
        'mss': 'Screen capture',
        'PIL': 'Image processing (Pillow)',
        'requests': 'HTTP client',
        'click': 'CLI framework',
        'yaml': 'Configuration'
    }
    
    for module, description in deps.items():
        try:
            if module == 'PIL':
                __import__('PIL')
            elif module == 'yaml':
                __import__('yaml')
            else:
                __import__(module)
            click.echo(f"  [OK] {description:25} (installed)")
        except ImportError:
            click.echo(f"  [ERROR] {description:25} (missing)", err=True)
    
    click.echo("")
    click.echo("Documentation:")
    click.echo("  https://github.com/nullvoider07/the-eyes")
    click.echo("")
    click.echo("To check for updates, run: eye update --check-only")
    click.echo("")

# Main Entry Point
def main():
    cli()

# Run the CLI
if __name__ == '__main__':
    main()