from agents.mcp import MCPServerStdio

def create_opennutrition_mcp_server():
  opennutrition_mcp_server_params = {
    "command": "node",
    "args": ["../mcp-opennutrition/build/index.js"]
  }

  return MCPServerStdio(params=opennutrition_mcp_server_params, client_session_timeout_seconds=60)
