import os
import json
from pydantic import BaseModel, Field
from typing import Optional

DEFAULT_MCP_CONFIG = json.dumps({
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}, indent=2)

CONFIG_FILE_PATH = os.path.join(os.getcwd(), 'data', 'config.json')

class AppConfig(BaseModel):
    api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    base_url: str = Field(default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    model: str = Field(default=os.getenv("MODEL_ID", "gpt-4o-mini"))
    system_prompt: str = Field(default="You are a world-class AI harness agent. You have the power to do anything in the user's system via terminal access. You should assist the user using the available tools, including self-optimization using the Meta-Harness methodology.")

    mcp_config_str: str = Field(default=DEFAULT_MCP_CONFIG)
    skills_config_str: str = Field(default="{}")
    sudo_password: str = Field(default="")
    workspace_dir: str = Field(default=os.getcwd())

    def __init__(self, **data):
        super().__init__(**data)
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
            except Exception as e:
                print(f"Error loading config from {CONFIG_FILE_PATH}: {e}")

    def save_config(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
            with open(CONFIG_FILE_PATH, 'w') as f:
                # Exclude sudo_password from persistent storage for security
                dump = self.model_dump(exclude={"sudo_password"})
                json.dump(dump, f, indent=2)
        except Exception as e:
            print(f"Error saving config to {CONFIG_FILE_PATH}: {e}")

config = AppConfig()
