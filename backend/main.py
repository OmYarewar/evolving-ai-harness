from fastapi import FastAPI, Request, Body, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import json
import asyncio
import zipfile
import shutil

from .config import config
from .memory import memory
from .agent import agent
from .mcp_manager import mcp_manager

app = FastAPI()

# Get the directory of the current file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(BASE_DIR, "ui")

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

templates = Jinja2Templates(directory=UI_DIR)

@app.on_event("startup")
async def startup_event():
    # Load default MCP configuration
    asyncio.create_task(mcp_manager.reload_config(config.mcp_config_str))

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

@app.get("/api/status")
async def get_status():
    return {"status": "ok", "message": "Backend is running"}

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    async def generate():
        async for chunk in agent.chat(request.session_id, request.message):
            yield f"data: {json.dumps(chunk)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/sessions")
async def get_sessions():
    sessions = []
    for session_id, session in memory.sessions.items():
        # Get preview from first user message, or default title
        title = "New Session"
        for msg in session.messages:
            if msg.role == "user":
                title = msg.content[:30] + ("..." if len(msg.content) > 30 else "")
                break

        sessions.append({
            "id": session_id,
            "title": title,
            "message_count": len(session.messages)
        })
    # Sort descending by id assuming id has timestamp
    sessions.sort(key=lambda x: x["id"], reverse=True)
    return {"sessions": sessions}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    return {"history": memory.get_history(session_id)}

class ConfigUpdate(BaseModel):
    api_key: str
    base_url: str
    model: str
    system_prompt: str
    mcp_config_str: str
    skills_config_str: str
    workspace_dir: str

@app.get("/api/config")
async def get_config():
    return config.model_dump()

@app.post("/api/config")
async def update_config(update: ConfigUpdate):
    config.api_key = update.api_key
    config.base_url = update.base_url
    config.model = update.model
    config.system_prompt = update.system_prompt
    config.workspace_dir = update.workspace_dir
    config.skills_config_str = update.skills_config_str

    if config.mcp_config_str != update.mcp_config_str:
        config.mcp_config_str = update.mcp_config_str
        # Start reload task in background
        asyncio.create_task(mcp_manager.reload_config(config.mcp_config_str))

    return {"status": "ok"}

class SudoUpdate(BaseModel):
    sudo_password: str

@app.post("/api/sudo")
async def update_sudo(update: SudoUpdate):
    config.sudo_password = update.sudo_password
    return {"status": "ok"}

@app.post("/api/skills/upload")
async def upload_skill(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a .zip")

    skills_dir = os.path.join(config.workspace_dir, "skills")
    os.makedirs(skills_dir, exist_ok=True)

    # Sanitize the filename to prevent path traversal
    safe_filename = os.path.basename(file.filename)
    zip_path = os.path.join(config.workspace_dir, safe_filename)

    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Use our existing tool logic to extract
        from .tools import install_skill
        result = install_skill(zip_path)

        # Clean up the zip file
        os.remove(zip_path)

        return {"status": "ok", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
