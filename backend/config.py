import os
from pydantic import BaseModel, Field
from typing import Optional

class AppConfig(BaseModel):
    api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    base_url: str = Field(default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    model: str = Field(default=os.getenv("MODEL_ID", "gpt-4o-mini"))
    system_prompt: str = Field(default="You are a world-class AI harness agent. You have the power to rewrite your own code and evolve. You should assist the user using the available tools.")

config = AppConfig()
