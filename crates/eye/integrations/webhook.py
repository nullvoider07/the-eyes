"""Webhook integration for Eye"""
import requests
from typing import Dict, Any, Optional

# WebhookManager manages webhook notifications.
class WebhookManager:
    """Manages webhook notifications"""
    
    # Initialize the WebhookManager
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    # Send notification about new frame
    def send_frame_notification(self, frame_id: int, metadata: Dict[str, Any]):
        """Send notification about new frame"""
        payload = {
            "event": "frame_captured",
            "frame_id": frame_id,
            "metadata": metadata
        }
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers=self.headers,
            timeout=5
        )
        response.raise_for_status()
    
    # Send session event
    def send_session_event(self, event_type: str, session_id: str, data: Dict[str, Any]):
        """Send session event"""
        payload = {
            "event": event_type,
            "session_id": session_id,
            "data": data
        }
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers=self.headers,
            timeout=5
        )
        response.raise_for_status()