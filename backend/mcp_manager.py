import asyncio
import json
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPManager:
    def __init__(self):
        self.config = {}
        self.servers = {}
        self.exit_stack = AsyncExitStack()
        self.tools = []

    async def reload_config(self, mcp_config_str):
        print("Reloading MCP config...")
        try:
            self.config = json.loads(mcp_config_str)
        except Exception as e:
            print(f"Error parsing MCP config: {e}")
            return

        # Close existing
        await self.exit_stack.aclose()
        self.exit_stack = AsyncExitStack()
        self.servers = {}
        self.tools = []

        mcp_servers = self.config.get("mcpServers", {})
        for name, server_config in mcp_servers.items():
            cmd = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", None)

            # Merge with current env
            full_env = os.environ.copy()
            if env:
                full_env.update(env)

            server_params = StdioServerParameters(
                command=cmd,
                args=args,
                env=full_env
            )

            try:
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                read, write = stdio_transport
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()

                # Get tools
                tools_result = await session.list_tools()

                self.servers[name] = {
                    "session": session,
                    "tools": {t.name: t for t in tools_result.tools}
                }

                # Add to flat tool list
                for t in tools_result.tools:
                    self.tools.append({
                        "server": name,
                        "tool": t
                    })

                print(f"Connected to MCP server {name}")
            except Exception as e:
                print(f"Failed to connect to MCP server {name}: {e}")

    def get_tool_schemas(self):
        schemas = []
        for item in self.tools:
            t = item["tool"]
            schemas.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema
                }
            })
        return schemas

    async def call_tool(self, name, arguments):
        for item in self.tools:
            if item["tool"].name == name:
                server_name = item["server"]
                session = self.servers[server_name]["session"]
                try:
                    result = await session.call_tool(name, arguments)
                    # format result
                    out = []
                    for c in result.content:
                        if c.type == "text":
                            out.append(c.text)
                    return "\n".join(out)
                except Exception as e:
                    return f"Error calling tool {name}: {e}"
        return f"Tool {name} not found in MCP servers."

mcp_manager = MCPManager()
