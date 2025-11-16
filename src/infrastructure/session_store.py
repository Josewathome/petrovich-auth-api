import logging
from typing import Dict, Any, Optional
from src.domain.models import SessionData
from src.domain.exceptions import SessionCreationError

logger = logging.getLogger(__name__)

class InMemorySessionStore:
    """In-memory session storage (replaces MongoDB)"""
    
    def __init__(self):
        self.sessions = {}
        self.current_session_id = 0
    
    async def create_session(self, session_data: SessionData) -> str:
        """Create new session and return session ID"""
        session_id = str(self.current_session_id)
        self.sessions[session_id] = session_data
        self.current_session_id += 1
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    async def update_session(self, session_id: str, session_data: SessionData):
        """Update existing session"""
        if session_id in self.sessions:
            self.sessions[session_id] = session_data
            logger.info(f"Updated session: {session_id}")
        else:
            raise SessionCreationError(f"Session not found: {session_id}")
    
    async def get_any_session(self) -> Optional[SessionData]:
        """Get any available session (for simple cases)"""
        if self.sessions:
            return next(iter(self.sessions.values()))
        return None