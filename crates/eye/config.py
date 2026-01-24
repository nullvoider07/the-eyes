"""Configuration management for Eye"""
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration values
CONFIG_DIR = Path.home() / ".eye"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Default configuration structure
DEFAULT_CONFIG = {
    "capture": {
        "interval": 1.5,
        "format": "png",
        "quality": 100,
        "resolution": {"width": 1920, "height": 1080}
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "protocol": "http"
    },
    "auth": {
        "enabled": True,
        "method": "token"
    },
    "storage": {
        "mode": "memory",
        "max_frames": 100,
        "retention": "1h"
    },
    "safety": {
        "rate_limit": {
            "max_fps": 2.0,
            "burst": 5
        },
        "resource_limits": {
            "max_cpu_percent": 10,
            "max_memory_mb": 512,
            "max_bandwidth_mbps": 10
        }
    }
}

# Configuration management class
class ConfigManager:
    """Manages Eye configuration"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_path.exists():
            return DEFAULT_CONFIG.copy()
        
        with open(self.config_path, 'r') as f:
            user_config = yaml.safe_load(f) or {}
        
        # Merge with defaults
        config = DEFAULT_CONFIG.copy()
        self._deep_merge(config, user_config)
        return config
    
    # Helper method for deep merging dictionaries
    def _deep_merge(self, base: dict, override: dict):
        """Deep merge override into base"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    # Save configuration to file
    def save(self):
        """Save configuration to file"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    # Get configuration value by dot-notation key
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    # Set configuration value by dot-notation key
    def set(self, key: str, value: Any):
        """Set config value by dot-notation key"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    # Reset configuration to defaults
    def reset(self):
        """Reset to default configuration"""
        self.config = DEFAULT_CONFIG.copy()
        self.save()