# Blender MCP

**Model Context Protocol (MCP) Server for Blender.**

This project allows you to control Blender 3D from any MCP-compatible IDE (such as Trae, Cursor, Claude Desktop, etc.). You can use natural language to create objects, run Python scripts, and query scene data.

## Features

- **Natural Language 3D Creation**: Ask your AI assistant to "create a red cube" or "generate a procedural city".
- **Full Python API Access**: The AI can execute any valid `bpy` script.
- **Universal Compatibility**: Works with any MCP client via a simple TCP bridge.

## Architecture

1.  **Blender Server (`blender_server.py`)**: A script running inside Blender that listens for TCP connections and executes commands.
2.  **MCP Connector (`connector.py`)**: A Python script running in your IDE that translates standard Input/Output (Stdio) MCP messages to TCP, communicating with Blender.

## Dependencies

The Blender Server requires the `mcp` Python package to be available within Blender's Python environment.
On Windows, `pywin32` is also recommended.

We provide automated scripts to handle this for you.

## Installation & Setup

### 1. Install Dependencies

You can install the required libraries directly into a local `libs` folder, so you don't need to modify Blender's system files.

**Windows Users:**
1.  Run `setup_dependencies.bat`.
2.  Check `install_log.txt` to confirm success.

**Manual Installation (Mac/Linux/Windows):**
Open a terminal or command prompt and run:
```bash
# Replace 'blender' with the path to your Blender executable
blender -b --python install_dependencies.py
```

### 2. Configure Blender

1.  Open Blender (version 3.0+ recommended).
2.  Switch to the **Scripting** tab.
3.  Open `blender_server.py` in the text editor.
4.  Click **Run Script** (Play button).
5.  Open **Window > Toggle System Console** to see logs. You should see: `Blender MCP Server listening on localhost:8123`.

### 3. Configure Your IDE

You need to tell your IDE to run the `connector.py` script as an MCP server.

#### For Trae / VS Code (Generic MCP)

Add this to your MCP configuration (e.g., `mcp.json`):

```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": [
        "/absolute/path/to/blender-mcp/connector.py"
      ]
    }
  }
}
```

*Note: Ensure you use the absolute path to `connector.py`.*

## Usage

Once connected, you can ask your AI Assistant:

- "Create a monkey head with subdivision surface."
- "List all objects in the scene."
- "Move the camera to (0, -5, 2)."
- "Create a grid of 100 cubes with random colors."

## Security Note

This tool allows remote execution of Python code within Blender via a local TCP port.
*   **Only run this on your local machine.**
*   **Do not expose port 8123 to the internet.**

## License

MIT License. See [LICENSE](LICENSE) file for details.
