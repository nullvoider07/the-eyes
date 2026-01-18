import time
import requests
import os
import sys
import tempfile
import subprocess
import socket
import struct
import platform
import signal
from io import BytesIO
from PIL import Image
from typing import Optional
from datetime import datetime, timedelta

# Check for MSS availability
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("[WARN] mss not installed. Install with: pip install mss")

# Universal Capture Agent (Linux, Windows, macOS).
class Agent:
    """
    Universal Capture Agent (Linux, Windows, macOS).
    Now with: format control, quality settings, duration/frame limits
    """
    
    # Initialization
    def __init__(
        self,
        server_url: Optional[str] = None,
        token: Optional[str] = None,
        interval: float = 1.5,
        format: str = "png",
        quality: int = 95,
        duration: Optional[int] = None,
        max_frames: Optional[int] = None,
        notify: bool = True
    ):
        self.interval = interval
        self.format = format.lower()
        self.quality = max(1, min(100, quality))
        self.duration = duration
        self.max_frames = max_frames
        self.notify = notify
        
        self.frame_id = 0
        self.retry_delay = 1
        self.token = token
        self.os_type = platform.system()
        self.running = False
        self.start_time = None
        self.stop_time = None
        
        # Validate format
        if self.format not in ['png', 'jpeg', 'jpg', 'webp', 'bmp', 'tiff']:
            raise ValueError(f"Unsupported format: {format}. Use 'png' or 'jpeg'")
        if self.format == 'jpg':
            self.format = 'jpeg'
        
        # Resolve Server URL
        if server_url:
            self.server_url = server_url.rstrip('/')
            print(f"[INFO] Server URL set via CLI: {self.server_url}")
        else:
            self.server_url = self.detect_mediator()
            
        self.upload_endpoint = f"{self.server_url}/upload"
        
        print(f"[INFO] Eye Agent initializing on {self.os_type}...")
        print(f"[INFO] Target: {self.upload_endpoint}")
        print(f"[INFO] Format: {self.format.upper()}")
        if self.format == 'jpeg':
            print(f"[INFO] Quality: {self.quality}/100")
        print(f"[INFO] Interval: {self.interval}s")
        if self.duration:
            print(f"[INFO] Duration: {self.duration}s (auto-stop)")
        if self.max_frames:
            print(f"[INFO] Max frames: {self.max_frames} (auto-stop)")
        
        # 2. Detect Capture Method
        self.capture_method = self._detect_capture_method()
        print(f"[INFO] Capture Strategy: {self.capture_method}")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    # Signal Handler
    def _signal_handler(self, signum, frame):
        """Handle stop signals gracefully"""
        print("\n[INFO] Stop signal received...")
        self.stop()
    
    # Mediator Detection
    def detect_mediator(self) -> str:
        """Robust discovery strategy"""
        env_url = os.environ.get("MEDIATOR_URL")
        if env_url:
            return env_url.rstrip('/')

        print("[*] Auto-detecting Server...")
        candidates = [
            "http://localhost:8080",
            "http://mediator:8080",
            "http://host.docker.internal:8080"
        ]

        # Linux-specific Gateway Detection
        if self.os_type == "Linux":
            try:
                with open("/proc/net/route") as fh:
                    for line in fh:
                        fields = line.strip().split()
                        if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                            continue
                        gateway_ip = socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
                        candidates.append(f"http://{gateway_ip}:8080")
                        break
            except Exception:
                pass

        for url in candidates:
            try:
                requests.get(f"{url}/health", timeout=1)
                print(f"[*] Found server at: {url}")
                return url
            except:
                continue

        return "http://localhost:8080"
    
    # Capture Method Detection
    def _detect_capture_method(self) -> str:
        """Determine best capture method based on OS"""
        
        # Linux Wayland Check (Needs external tools)
        if self.os_type == "Linux":
            if os.environ.get('WAYLAND_DISPLAY') or os.environ.get('XDG_SESSION_TYPE') == 'wayland':
                return "linux_system"
        
        # Cross-Platform MSS (Best for Win/Mac/Linux X11)
        if MSS_AVAILABLE:
            try:
                from mss import mss 
                with mss() as sct:
                    sct.monitors
                return "mss"
            except Exception:
                pass
        
        # OS-Specific Fallbacks
        if self.os_type == "Darwin":
            return "macos_screencapture"
        elif self.os_type == "Linux":
            return "linux_system"
            
        return "test_pattern"

    # Wait for Server
    def wait_for_server(self, timeout: Optional[int] = None) -> bool:
        """Block until server is healthy"""
        print("[INFO] Waiting for server...")
        attempt = 0
        start_time = time.time()
        while True:
            if timeout and (time.time() - start_time > timeout):
                print("[ERROR] Server not reachable (Timeout).")
                return False
            attempt += 1
            try:
                response = requests.get(f"{self.server_url}/health", timeout=2)
                if response.status_code == 200:
                    print(f"[INFO] ✅ Server ready! (Connected on attempt {attempt})")
                    return True
            except Exception:
                pass
            if attempt % 10 == 0:
                print(f"[INFO] Still waiting for server... (Attempt {attempt})")
                time.sleep(2)
    
    # Auto-Stop Check
    def _should_stop(self) -> bool:
        """Check if agent should stop based on limits"""
        if not self.running:
            return True
        
        # Duration limit
        if self.duration and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed >= self.duration:
                print(f"\n[INFO] Duration limit reached ({self.duration}s)")
                return True
        
        # Frame limit
        if self.max_frames and self.frame_id >= self.max_frames:
            print(f"\n[INFO] Frame limit reached ({self.max_frames} frames)")
            return True
        
        return False
    
    # Screen Capture
    def capture_screen(self) -> bytes:
        """Capture and encode in configured format"""
        if self.capture_method == "mss":
            return self._capture_mss()
        elif self.capture_method == "linux_system":
            return self._capture_linux_fallback()
        elif self.capture_method == "macos_screencapture":
            return self._capture_macos()
        else:
            return self._generate_test_pattern()

    # Encode Image
    def _encode_image(self, img: Image.Image) -> bytes:
        """Encode image in configured format and quality"""
        buffer = BytesIO()
        fmt = self.format.upper()
        
        if self.format == 'png':
            img.save(buffer, format='PNG', optimize=True)
        elif fmt == 'WEBP':
            img.save(buffer, format='WEBP', quality=self.quality, lossless=(self.quality == 100))
        elif fmt == 'BMP':
            img.save(buffer, format='BMP')
        elif fmt == 'TIFF':
            img.save(buffer, format='TIFF')
        else:
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            img.save(buffer, format='JPEG', quality=self.quality, optimize=True)
        
        return buffer.getvalue()

    # MSS Capture
    def _capture_mss(self) -> bytes:
        try:
            from mss import mss
            with mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                return self._encode_image(img)
        except Exception:
            # Fallback to OS specific tools if MSS crashes
            if self.os_type == "Linux":
                return self._capture_linux_fallback()
            elif self.os_type == "Darwin":
                return self._capture_macos()
            return self._generate_test_pattern()
    
    # Linux Fallback Capture
    def _capture_linux_fallback(self) -> bytes:
        """
        Linux Fallback: Standard execution with minimal environment cleanup.
        Removes LD_LIBRARY_PATH/LD_PRELOAD to fix Snap/VS Code compatibility issues
        """
        temp_file = tempfile.mktemp(suffix=".png")
        
        # 1. Sanitize Environment
        clean_env = os.environ.copy()
        clean_env.pop('LD_LIBRARY_PATH', None)
        clean_env.pop('LD_PRELOAD', None)

        if 'XDG_CURRENT_DESKTOP' not in clean_env:
            clean_env['XDG_CURRENT_DESKTOP'] = 'GNOME'

        flameshot_cmd = ["flameshot", "full", "-p", temp_file]
        if not self.notify:
            flameshot_cmd.insert(2, "-n")

        # 2. Try Standard Tools
        commands = [
            flameshot_cmd,
            ["gnome-screenshot", "-f", temp_file],
        ]
        
        for cmd in commands:
            try:
                subprocess.run(
                    cmd, 
                    env=clean_env, 
                    capture_output=True, 
                    timeout=10
                )
                
                if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                    # Load and re-encode in configured format
                    img = Image.open(temp_file)
                    os.remove(temp_file)
                    return self._encode_image(img)
            except Exception:
                continue
        
        return self._generate_test_pattern()

    # macOS Capture
    def _capture_macos(self) -> bytes:
        """macOS: Uses native screencapture tool"""
        temp_file = tempfile.mktemp(suffix=".png")
        try:
            subprocess.run(["screencapture", "-x", "-C", temp_file], check=True, timeout=5)
            
            # Load and re-encode in configured format
            img = Image.open(temp_file)
            os.remove(temp_file)
            return self._encode_image(img)
        except Exception:
            return self._generate_test_pattern()
    
    # Test Pattern Generation
    def _generate_test_pattern(self) -> bytes:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (1920, 1080), color='#c0392b')
        d = ImageDraw.Draw(img)
        d.text((50, 50), f"CAPTURE FAILED - {self.os_type}\nFrame {self.frame_id}\nFormat: {self.format.upper()}", fill='white')
        return self._encode_image(img)

    def upload_frame(self, image_data: bytes) -> bool:
        try:
            mime_type = f"image/{self.format}"
            filename = f"frame.{self.format}"
            
            files = {'image': (filename, image_data, mime_type)}
            data = {
                'frame_id': str(self.frame_id),
                'timestamp': str(int(time.time())),
                'format': self.format
            }
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            response = requests.post(
                self.upload_endpoint,
                files=files,
                data=data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                self.retry_delay = 1
                result = response.json()

                if 'config' in result:
                    remote = result['config']
                    
                    # 1. Update Interval
                    new_interval = float(remote.get('interval', self.interval))
                    if new_interval != self.interval:
                        print(f"\n[CMD] Interval update: {self.interval}s -> {new_interval}s")
                        self.interval = new_interval
                        
                    # 2. Update Format
                    new_format = remote.get('format', self.format).lower()
                    if new_format != self.format:
                        print(f"\n[CMD] Format update: {self.format} -> {new_format}")
                        self.format = new_format
                        
                    # 3. Update Quality
                    new_quality = int(remote.get('quality', self.quality))
                    if new_quality != self.quality:
                        print(f"\n[CMD] Quality update: {self.quality} -> {new_quality}")
                        self.quality = new_quality

                size_kb = result.get('size_kb', len(image_data) / 1024)
                print(f"\r[OK] Frame #{self.frame_id}: {size_kb:.1f} KB ({self.format.upper()})", end="", flush=True)
                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            if self.retry_delay < 10:
                print(f"\n[!] Upload Failed: {e}. Backing off {self.retry_delay}s...")
            time.sleep(self.retry_delay)
            self.retry_delay = min(self.retry_delay * 2, 30)
            return False

    # Start Agent
    def start(self):
        """Start the agent"""
        if not self.wait_for_server():
            return False
        
        self.running = True
        self.start_time = datetime.now()
        
        if self.duration:
            self.stop_time = self.start_time + timedelta(seconds=self.duration)
            print(f"[INFO] Will stop at: {self.stop_time.strftime('%H:%M:%S')}")
        
        print("[INFO] 🚀 Agent Active.")
        return True
    
    # Stop Agent
    def stop(self):
        """Stop the agent"""
        if self.running:
            self.running = False
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            print(f"\n[INFO] ⏹️ Agent stopped")
            print(f"[INFO] Captured {self.frame_id} frames in {elapsed:.1f}s")

    # Main Loop
    def run(self):
        """Main loop with auto-stop support"""
        if not self.start():
            sys.exit(1)
        
        try:
            while not self._should_stop():
                loop_start = time.time()
                
                try:
                    data = self.capture_screen()
                    if self.upload_frame(data):
                        self.frame_id += 1
                except Exception as e:
                    print(f"\n[ERROR] Loop Error: {e}")
                    time.sleep(2)
                
                elapsed = time.time() - loop_start
                sleep_time = max(0, self.interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()