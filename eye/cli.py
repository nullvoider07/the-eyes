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
__version__ = "0.1.1"

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
    """Start Go server"""
    click.echo(f"[START] Starting server on port {port}")
    
    env = os.environ.copy()
    env['EYE_PORT'] = str(port)
    if token:
        env['EYE_AUTH_TOKEN'] = token
    
    # Check for binary in local bin/ or system PATH
    if os.path.exists("bin/eye-server"):
        server_bin = "./bin/eye-server"
    else:
        server_bin = "eye-server"

    try:
        subprocess.run([server_bin], env=env, check=True)
    except FileNotFoundError:
        click.echo("[ERROR] 'eye-server' binary not found. Run: go build -o bin/eye-server cmd/server/main.go", err=True)

# Agent Commands
@cli.group()
def agent():
    """Manage agent"""
    pass

# Start Agent Command
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
    """Start Python capture agent with full configuration"""
    
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

# Debug Command
@cli.command()
def debug():
    """Show debug info"""
    try:
        r = requests.get('http://localhost:8080/debug', timeout=2)
        click.echo(yaml.dump(r.json()))
    except:
        click.echo("[ERROR] Server not running or unreachable", err=True)

# Update Command
@cli.command()
@click.option('--check-only', is_flag=True, help='Only check for updates without installing')
def update(check_only):
    """Check for updates and install the latest version"""
    
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
        
        # Construct download URL
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
            binaries = ['eye.exe', 'eye-server.exe']
        else:
            binaries = ['eye', 'eye-server']
        
        for binary in binaries:
            src = extracted_bin_dir / binary
            dst = install_dir / binary
            
            if src.exists():
                # On Windows, we might need to handle file locks
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
    
    # Try to get Go server version
    try:
        if os.path.exists("bin/eye-server"):
            server_bin = "./bin/eye-server"
        else:
            server_bin = "eye-server"
        
        # Try to run server with --version
        result = subprocess.run(
            [server_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            click.echo(f"  * Go Server:   {result.stdout.strip()}")
        else:
            click.echo(f"  * Go Server:   (installed)")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        click.echo(f"  * Go Server:   (not found)")
    
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