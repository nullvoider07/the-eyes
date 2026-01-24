"""Session management for Eye"""
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

# Session represents a capture session.
class Session:
    """Represents a capture session"""

    # Initialize the Session with ID, name, and duration
    def __init__(self, session_id: str, name: Optional[str] = None, duration: Optional[int] = None):
        self.session_id = session_id
        self.name = name or f"session_{session_id[:8]}"
        self.duration = duration
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.frame_count = 0
        self.status = "active"
    
    # Convert session to dictionary
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "duration": self.duration,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "frame_count": self.frame_count,
            "status": self.status
        }

# SessionManager manages multiple capture sessions.
class SessionManager:
    """Manages capture sessions"""
    
    # Initialize the SessionManager
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    # Create a new session
    def create_session(self, name: Optional[str] = None, duration: Optional[int] = None) -> Session:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        session = Session(session_id, name, duration)
        self.sessions[session_id] = session
        return session
    
    # Get a session by ID
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    # Stop a session by ID
    def stop_session(self, session_id: str):
        """Stop a session"""
        session = self.sessions.get(session_id)
        if session:
            session.end_time = datetime.now()
            session.status = "stopped"
    
    # List all sessions
    def list_sessions(self) -> list[Session]:
        """List all sessions"""
        return list(self.sessions.values())
    
    # Get all active sessions
    def get_active_sessions(self) -> list[Session]:
        """Get all active sessions"""
        return [s for s in self.sessions.values() if s.status == "active"]