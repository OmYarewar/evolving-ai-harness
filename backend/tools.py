from typing import Callable, Dict, Any, List
import json
import subprocess
import os
import sys

def read_file(filepath: str) -> str:
    """Reads the content of a file."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filepath: str, content: str) -> str:
    """Writes content to a file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return f"File {filepath} written successfully."
    except Exception as e:
        return f"Error writing file: {e}"

def execute_terminal_command(command: str) -> str:
    """Executes a command in the terminal and returns the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
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
        result = subprocess.run(test_command, shell=True, capture_output=True, text=True)
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

AVAILABLE_TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "execute_terminal_command": execute_terminal_command,
    "restart_harness": restart_harness,
    "evaluate_harness": evaluate_harness
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
    return f"Error: Tool {func_name} not found."
