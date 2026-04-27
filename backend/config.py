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

class AppConfig(BaseModel):
    api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    base_url: str = Field(default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    model: str = Field(default=os.getenv("MODEL_ID", "gpt-4o-mini"))
    system_prompt: str = Field(default="You are a world-class AI harness agent. You have the power to do anything in the user's system via terminal access. You should assist the user using the available tools, including self-optimization using the Meta-Harness methodology.")

    mcp_config_str: str = Field(default=DEFAULT_MCP_CONFIG)
    skills_config_str: str = Field(default="{}")
    sudo_password: str = Field(default="")
    workspace_dir: str = Field(default=os.getcwd())

config = AppConfig()
