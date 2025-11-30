from typing import Dict, List, Any, Optional
from src.utils.logger import setup_logger

logger = setup_logger("session_manager")

class InMemorySessionService:
    """
    Manages short-term conversation history for active user sessions.
    
    This service fulfills the 'Sessions & State Management' requirement by providing
    a lightweight, in-memory store for chat history. It allows Agents to maintain
    context across multiple turns of conversation (e.g., answering follow-up questions).
    
    Attributes:
        _sessions (Dict[str, List[Dict[str, Any]]]): Internal storage mapping session IDs 
                                                      to lists of message objects.
        _max_history (int): The maximum number of messages to retain per session to prevent 
                            unbounded memory growth.
    """
    
    def __init__(self, max_history: int = 20):
        """
        Initializes the session service.

        Args:
            max_history (int): The limit on messages stored per session (default: 20).
        """
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}
        self._max_history = max_history

    def create_session(self, session_id: str) -> None:
        """
        Initializes a new empty session if one does not already exist.

        Args:
            session_id (str): Unique identifier for the user session.
        """
        if session_id not in self._sessions:
            logger.info(f"🆕 Creating new session: {session_id}")
            self._sessions[session_id] = []

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Appends a new message to the specified session's history.
        
        Automatically creates the session if it doesn't exist and enforces the
        history size limit by discarding the oldest messages (FIFO).

        Args:
            session_id (str): Unique identifier for the user session.
            role (str): The speaker's role (e.g., 'user', 'model', 'system').
            content (str): The text content of the message.
        """
        if session_id not in self._sessions:
            self.create_session(session_id)
            
        entry = {"role": role, "content": content}
        self._sessions[session_id].append(entry)
        
        # Enforce history limit (Rolling Window)
        if len(self._sessions[session_id]) > self._max_history:
            self._sessions[session_id].pop(0)

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the conversation history for a session.

        Args:
            session_id (str): Unique identifier for the user session.

        Returns:
            List[Dict[str, Any]]: A list of message dictionaries (e.g., [{'role': 'user', ...}]).
                                  Returns an empty list if the session does not exist.
        """
        history = self._sessions.get(session_id, [])
        logger.debug(f"📜 Retrieved {len(history)} messages for session {session_id}")
        return history

    def clear_session(self, session_id: str) -> bool:
        """
        Deletes a session and its history.

        Args:
            session_id (str): Unique identifier for the user session.

        Returns:
            bool: True if the session existed and was deleted, False otherwise.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"🗑️ Cleared session: {session_id}")
            return True
        return False

# Global Singleton Instance
# Using a singleton ensures all parts of the app share the same memory state.
session_service = InMemorySessionService()

if __name__ == "__main__":
    # Internal Unit Test
    print("🧪 Testing Session Manager...")
    service = InMemorySessionService(max_history=3)
    
    sid = "test_user_123"
    service.add_message(sid, "user", "Hello")
    service.add_message(sid, "model", "Hi there")
    service.add_message(sid, "user", "How are you?")
    service.add_message(sid, "model", "I am good") # Should trigger pop(0)
    
    history = service.get_history(sid)
    print(f"History length (Expected 3): {len(history)}")
    print(f"First message (Expected 'Hi there'): {history[0]['content']}")