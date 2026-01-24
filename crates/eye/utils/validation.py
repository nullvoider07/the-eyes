"""Configuration validation for Eye"""
from typing import Dict, Any, List

# Validate configuration and return list of errors
def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate configuration and return list of errors"""
    errors = []
    
    # Validate capture settings
    if 'capture' in config:
        interval = config['capture'].get('interval')
        if interval is not None and interval <= 0:
            errors.append("capture.interval must be positive")
        
        format_type = config['capture'].get('format')
        if format_type not in ['png', 'jpeg', None]:
            errors.append("capture.format must be 'png' or 'jpeg'")
    
    # Validate server settings
    if 'server' in config:
        port = config['server'].get('port')
        if port is not None and (port < 1 or port > 65535):
            errors.append("server.port must be between 1 and 65535")
    
    # Validate storage settings
    if 'storage' in config:
        max_frames = config['storage'].get('max_frames')
        if max_frames is not None and max_frames < 1:
            errors.append("storage.max_frames must be at least 1")
    
    return errors