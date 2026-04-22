from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os

class Message(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class Session(BaseModel):
    session_id: str
    messages: List[Message] = []

class MemoryManager:
    def __init__(self, storage_file: str = "data/memory.json"):
        self.storage_file = storage_file
        self.sessions: Dict[str, Session] = {}
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        self.load()

    def load(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    for session_id, session_data in data.items():
                        self.sessions[session_id] = Session(**session_data)
            except Exception as e:
                print(f"Error loading memory: {e}")

    def save(self):
        with open(self.storage_file, "w") as f:
            json.dump({k: v.model_dump() for k, v in self.sessions.items()}, f, indent=2)

    def get_session(self, session_id: str) -> Session:
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(session_id=session_id)
        return self.sessions[session_id]

    def add_message(self, session_id: str, message: Message):
        session = self.get_session(session_id)
        session.messages.append(message)
        self.save()
        
    def get_history(self, session_id: str) -> List[Dict]:
        session = self.get_session(session_id)
        return [msg.model_dump(exclude_none=True) for msg in session.messages]

memory = MemoryManager()
