import click
import yaml
import os
import subprocess
import requests
import sys
from pathlib import Path
from eye.agent import Agent

# Define configuration paths
CONFIG_DIR = Path.home() / ".eye"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Version - Update with each release
__version__ = "0.1.0"

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
    click.echo(f"  • Python CLI:  v{__version__}")
    
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
            click.echo(f"  • Go Server:   {result.stdout.strip()}")
        else:
            click.echo(f"  • Go Server:   (installed)")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        click.echo(f"  • Go Server:   (not found)")
    
    click.echo("")
    click.echo("System Information:")
    click.echo(f"  • OS:          {platform.system()} {platform.release()}")
    click.echo(f"  • Architecture: {platform.machine()}")
    click.echo(f"  • Python:      {sys.version.split()[0]}")
    
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
            click.echo(f"  ✅ {description:25} (installed)")
        except ImportError:
            click.echo(f"  [ERROR] {description:25} (missing)", err=True)
    
    click.echo("")
    click.echo("Documentation:")
    click.echo("  https://github.com/nullvoider07/the-eyes")
    click.echo("")

# Main Entry Point
def main():
    cli()

# Run the CLI
if __name__ == '__main__':
    main()