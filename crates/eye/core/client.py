"""Python client SDK for Eye server"""
import requests
from typing import Optional, Dict, Any
from io import BytesIO

# EyeClient provides methods to interact with the Eye server.
class EyeClient:
    """Client for interacting with Eye server"""
    
    # Initialize the EyeClient with server URL and optional token
    def __init__(self, server_url: str, token: Optional[str] = None, timeout: int = 5):
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
    
    # Check server health status
    def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        response = self.session.get(
            f'{self.server_url}/health',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # Get the latest screenshot from the server
    def get_snapshot(self) -> bytes:
        """Get latest screenshot"""
        response = self.session.get(
            f'{self.server_url}/snapshot.png',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.content
    # Get metadata about the latest snapshot
    def get_snapshot_metadata(self) -> Dict[str, str]:
        """Get metadata about latest snapshot"""
        response = self.session.head(
            f'{self.server_url}/snapshot.png',
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return {
            'frame_id': response.headers.get('X-Frame-ID', ''),
            'frame_age': response.headers.get('X-Frame-Age', ''),
            'frame_size': response.headers.get('X-Frame-Size', '')
        }
    
    # Get debug information from the server
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information"""
        response = self.session.get(
            f'{self.server_url}/debug',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # Upload a frame to the server
    def upload_frame(self, frame_data: bytes, frame_id: int) -> Dict[str, Any]:
        """Upload a frame to server"""
        headers = {
            'Content-Type': 'image/png',
            'X-Frame-ID': str(frame_id)
        }
        
        response = self.session.post(
            f'{self.server_url}/upload',
            data=frame_data,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # Close the client session
    def close(self):
        """Close client session"""
        self.session.close()