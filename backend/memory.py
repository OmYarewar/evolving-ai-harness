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
    def __init__(self, storage_dir: str = "data/sessions"):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, Session] = {}
        os.makedirs(self.storage_dir, exist_ok=True)
        self.load()

    def _get_file_path(self, session_id: str) -> str:
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def load(self):
        # Backwards compatibility: check for old monolithic memory.json
        legacy_file = "data/memory.json"
        if os.path.exists(legacy_file):
            try:
                with open(legacy_file, "r") as f:
                    data = json.load(f)
                    for session_id, session_data in data.items():
                        self.sessions[session_id] = Session(**session_data)

                # Migrate to individual files
                self.save_all()

                # Rename old file so it won't be read again
                os.rename(legacy_file, legacy_file + ".bak")
            except Exception as e:
                print(f"Error loading legacy memory: {e}")

        # Load individual session files
        if os.path.exists(self.storage_dir):
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    session_id = filename[:-5]
                    try:
                        with open(self._get_file_path(session_id), "r") as f:
                            session_data = json.load(f)
                            self.sessions[session_id] = Session(**session_data)
                    except Exception as e:
                        print(f"Error loading session file {filename}: {e}")

    def save_session(self, session_id: str):
        if session_id in self.sessions:
            with open(self._get_file_path(session_id), "w") as f:
                json.dump(self.sessions[session_id].model_dump(), f, indent=2)

    def save_all(self):
        for session_id in self.sessions:
            self.save_session(session_id)

    def save(self):
        # Keep save() around just in case any other code calls it
        self.save_all()

    def get_session(self, session_id: str) -> Session:
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(session_id=session_id)
        return self.sessions[session_id]

    def add_message(self, session_id: str, message: Message):
        session = self.get_session(session_id)
        session.messages.append(message)
        self.save_session(session_id)
        
    def get_history(self, session_id: str) -> List[Dict]:
        session = self.get_session(session_id)
        return [msg.model_dump(exclude_none=True) for msg in session.messages]

memory = MemoryManager()
