from typing import Callable, Dict, Any, List
import json
import subprocess
import os
import sys
import urllib.request
from bs4 import BeautifulSoup
from .config import config

def read_file(filepath: str) -> str:
    """Reads the content of a file."""
    try:
        path = filepath
        if not os.path.isabs(path):
             path = os.path.join(config.workspace_dir, path)
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a file."""
    try:
        path = filepath
        if not os.path.isabs(path):
             path = os.path.join(config.workspace_dir, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return f"File {path} written successfully."
    except Exception as e:
        return f"Error writing file: {e}"

def execute_terminal_command(command: str) -> str:
    """Executes a command in the terminal and returns the output."""
    try:
        cmd_to_run = command
        # Auto-inject sudo password if required
        if "sudo " in command and config.sudo_password:
             cmd_to_run = command.replace("sudo ", f"echo '{config.sudo_password}' | sudo -S ") if "sudo " in command else command

        result = subprocess.run(cmd_to_run, shell=True, capture_output=True, text=True, cwd=config.workspace_dir, timeout=60)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Error executing command: {e}"

def restart_harness() -> str:
    """Restarts the harness application to apply changes."""
    print("Restarting harness...")
    os.execv(sys.executable, ['python'] + sys.argv)
    return "Restarting..."

def evaluate_harness(test_command: str) -> str:
    """Runs a harness test command and captures the output/trace for optimization."""
    try:
        cmd_to_run = test_command
        # Auto-inject sudo password if required
        if "sudo " in test_command and config.sudo_password:
             cmd_to_run = test_command.replace("sudo ", f"echo '{config.sudo_password}' | sudo -S ") if "sudo " in test_command else test_command

        result = subprocess.run(cmd_to_run, shell=True, capture_output=True, text=True, cwd=config.workspace_dir, timeout=60)
        output = "--- Test Execution Trace ---\n"
        output += f"Command: {test_command}\n"
        output += f"Exit Code: {result.returncode}\n\n"
        output += f"--- STDOUT ---\n{result.stdout}\n\n"
        output += f"--- STDERR ---\n{result.stderr}\n\n"

        import re
        score_match = re.search(r"score:\s*([0-9.]+)", result.stdout, re.IGNORECASE)
        if score_match:
            output += f"Extracted Score: {score_match.group(1)}\n"

        return output
    except Exception as e:
        return f"Error executing harness evaluation: {e}"

def get_recent_ai_papers() -> str:
    """Scrapes recent AI papers from arxiv."""
    try:
        url = "https://arxiv.org/list/cs.AI/recent"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
             html = response.read()

        soup = BeautifulSoup(html, 'html.parser')
        papers = []
        for dl in soup.find_all('dl'):
             titles = dl.find_all('div', class_='list-title')
             authors = dl.find_all('div', class_='list-authors')

             for title, author in zip(titles, authors):
                 paper_title = title.text.replace('Title:', '').strip()
                 paper_author = author.text.replace('Authors:', '').replace('\n', '').strip()
                 papers.append(f"Title: {paper_title}\nAuthors: {paper_author}")
                 if len(papers) >= 10: # Limit to 10 recent
                     break
             if len(papers) >= 10:
                 break
        return "\n\n".join(papers)
    except Exception as e:
        return f"Error fetching papers: {e}"

AVAILABLE_TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "execute_terminal_command": execute_terminal_command,
    "restart_harness": restart_harness,
    "evaluate_harness": evaluate_harness,
    "get_recent_ai_papers": get_recent_ai_papers
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a file. Use this to read source code or config files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "The path to the file to read"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes content to a file. Use this to modify source code, UI files, or config.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "The path to the file to write to"},
                    "content": {"type": "string", "description": "The complete new content of the file"}
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_terminal_command",
            "description": "Executes a command in the terminal and returns the output. Use this to run tests, install packages, or list directories. Gives you the power to do anything in the user's system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_harness",
            "description": "Restarts the backend server to apply code changes made to the backend python files.",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_harness",
            "description": "Runs a test command to evaluate the current harness and captures the execution trace, output, and score. This is essential for the Meta-Harness optimization process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_command": {"type": "string", "description": "The shell command to run the tests and generate the trace."}
                },
                "required": ["test_command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_ai_papers",
            "description": "Fetches a list of the most recent AI papers from arxiv.",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    }
]

def execute_tool_call(tool_call: Dict[str, Any]) -> str:
    func_name = tool_call["function"]["name"]
    arguments_str = tool_call["function"]["arguments"]
    
    try:
        arguments = json.loads(arguments_str)
    except json.JSONDecodeError:
        return "Error: Invalid JSON in arguments"

    if func_name in AVAILABLE_TOOLS:
        func = AVAILABLE_TOOLS[func_name]
        try:
            return str(func(**arguments))
        except Exception as e:
            return f"Error executing tool {func_name}: {str(e)}"
    return f"Error: Tool {func_name} not found locally."
