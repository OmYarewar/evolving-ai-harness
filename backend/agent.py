from openai import AsyncOpenAI
import json
from .config import config
from .memory import memory, Message
from .tools import TOOLS_SCHEMA, execute_tool_call, AVAILABLE_TOOLS
from .mcp_manager import mcp_manager

class Agent:
    def __init__(self):
        self._last_api_key = None
        self._last_base_url = None
        self.client = None
        self._init_client()

    def _init_client(self):
        # Only reinitialize if configuration has changed to preserve HTTP connection pool
        if self._last_api_key != config.api_key or self._last_base_url != config.base_url or self.client is None:
            self.client = AsyncOpenAI(
                api_key=config.api_key or "dummy-key",
                base_url=config.base_url
            )
            self._last_api_key = config.api_key
            self._last_base_url = config.base_url

    async def chat(self, session_id: str, user_message: str):
        # Refresh client in case config changed
        self._init_client()

        # Add user message to memory
        memory.add_message(session_id, Message(role="user", content=user_message))

        while True:
            # Prepare messages payload
            messages = [{"role": "system", "content": config.system_prompt}]
            messages.extend(memory.get_history(session_id))

            # Combine static tools and MCP dynamic tools
            current_tools_schema = TOOLS_SCHEMA.copy()
            current_tools_schema.extend(mcp_manager.get_tool_schemas())

            try:
                # Call LLM
                response = await self.client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    tools=current_tools_schema,
                    tool_choice="auto"
                )
            except Exception as e:
                error_msg = f"API Error: {str(e)}"
                memory.add_message(session_id, Message(role="assistant", content=error_msg))
                yield {"role": "assistant", "content": error_msg}
                break

            response_message = response.choices[0].message
            
            # Save assistant message
            assistant_msg = Message(
                role="assistant",
                content=response_message.content or "",
            )
            if response_message.tool_calls:
                assistant_msg.tool_calls = [
                    {
                        "id": t.id,
                        "type": "function",
                        "function": {
                            "name": t.function.name,
                            "arguments": t.function.arguments
                        }
                    }
                    for t in response_message.tool_calls
                ]
            memory.add_message(session_id, assistant_msg)

            # Yield partial response (useful for streaming/UI updates)
            yield assistant_msg.model_dump(exclude_none=True)

            # Handle tool calls
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    arguments_str = tool_call.function.arguments

                    if func_name in AVAILABLE_TOOLS:
                        tool_result = execute_tool_call({
                            "function": {
                                "name": func_name,
                                "arguments": arguments_str
                            }
                        })
                    else:
                        try:
                            args = json.loads(arguments_str)
                            tool_result = await mcp_manager.call_tool(func_name, args)
                        except Exception as e:
                            tool_result = f"Error evaluating MCP tool {func_name}: {e}"
                    
                    tool_msg = Message(
                        role="tool",
                        content=str(tool_result),
                        tool_call_id=tool_call.id,
                        name=func_name
                    )
                    memory.add_message(session_id, tool_msg)
                    yield tool_msg.model_dump(exclude_none=True)
            else:
                # No more tool calls, exit loop
                break

agent = Agent()
