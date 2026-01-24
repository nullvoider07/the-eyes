"""Real-time streaming functionality"""
import asyncio
from typing import Callable, Optional
import websockets

# StreamManager manages real-time frame streaming.
class StreamManager:
    """Manages real-time frame streaming"""
    
    # Initialize the StreamManager
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.running = False
    
    # Start streaming frames
    async def stream_frames(self, callback: Callable[[bytes], None]):
        """Stream frames via WebSocket"""
        ws_url = self.server_url.replace('http://', 'ws://').replace('https://', 'wss://')
        
        self.running = True
        async with websockets.connect(f"{ws_url}/stream") as websocket:
            while self.running:
                frame_data = await websocket.recv()
                if isinstance(frame_data, str):
                    frame_data = frame_data.encode('utf-8')
                callback(frame_data)
    
    # Stop streaming frames
    def stop(self):
        """Stop streaming"""
        self.running = False