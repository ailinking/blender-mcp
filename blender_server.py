import sys
import os
import logging
import asyncio
import socket
import threading
import json
import runpy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("blender_mcp")

# --- PATH CONFIGURATION ---
# Dynamically determine the path to the 'libs' directory relative to this script
current_script_dir = os.path.dirname(os.path.abspath(__file__))
libs_dir = os.path.join(current_script_dir, "libs")

if os.path.exists(libs_dir):
    if libs_dir not in sys.path:
        sys.path.insert(0, libs_dir)
    
    # --- PYWIN32 FIX ---
    # Necessary for some Windows environments where pywin32 DLLs aren't in PATH
    pywin32_sys32 = os.path.join(libs_dir, "pywin32_system32")
    if os.path.exists(pywin32_sys32):
        try:
            os.add_dll_directory(pywin32_sys32)
        except AttributeError:
            os.environ["PATH"] = pywin32_sys32 + os.pathsep + os.environ["PATH"]
            
    win32_paths = [
        os.path.join(libs_dir, "win32"),
        os.path.join(libs_dir, "win32", "lib"),
        os.path.join(libs_dir, "pythonwin"),
    ]
    for p in win32_paths:
        if os.path.exists(p) and p not in sys.path:
            sys.path.insert(0, p)

# --------------------------

try:
    import bpy
except ImportError:
    print("CRITICAL: This script must be run inside Blender.")
    # We continue for linting purposes, but it will fail later if bpy is missing

# --- CORE LOGIC ---

# 1. Tool Definitions
async def list_tools():
    return [
        {
            "name": "run_script",
            "description": "Run a Python script in Blender",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "The python script code to execute"}
                },
                "required": ["script"]
            }
        },
        {
            "name": "get_scene_info",
            "description": "Get information about the current scene",
            "inputSchema": {
                "type": "object",
                "properties": {},
            }
        },
        {
            "name": "list_objects",
            "description": "List all objects in the current scene",
            "inputSchema": {
                "type": "object",
                "properties": {},
            }
        }
    ]

# 2. Helper to run Blender API calls in the main thread
def run_in_main_thread(func, *args, **kwargs):
    result_container = {}
    event = threading.Event()
    
    def _wrapper():
        try:
            result_container['data'] = func(*args, **kwargs)
        except Exception as e:
            result_container['error'] = e
        finally:
            event.set()
            
    # Schedule on main thread
    if bpy.app.timers:
        bpy.app.timers.register(lambda: (_wrapper(), None)[1], first_interval=0.001)
    else:
        # Fallback if timers not available (rare)
        _wrapper()
    
    event.wait()
    if 'error' in result_container:
        raise result_container['error']
    return result_container.get('data')

# 3. Tool Implementation
async def call_tool(name: str, arguments: dict):
    print(f"Tool Call Received: {name}")
    
    if name == "run_script":
        script = arguments.get("script")
        if not script:
            raise ValueError("Script content is required")
        
        print("Executing Python script...")
        def _exec_script():
            import io
            from contextlib import redirect_stdout, redirect_stderr
            f_out = io.StringIO()
            f_err = io.StringIO()
            
            try:
                with redirect_stdout(f_out), redirect_stderr(f_err):
                    exec(script, {"bpy": bpy})
                
                output = f_out.getvalue()
                error = f_err.getvalue()
                return output, error, None
            except Exception as e:
                import traceback
                traceback.print_exc()
                return f_out.getvalue(), f_err.getvalue(), str(e)

        try:
            output, error, exception_msg = run_in_main_thread(_exec_script)
            
            result_text = ""
            if output: result_text += f"Output:\n{output}\n"
            if error: result_text += f"Errors:\n{error}\n"
            if exception_msg: result_text += f"Exception: {exception_msg}\n"
            if not result_text: result_text = "Script executed successfully (no output)."
            
            return [{"type": "text", "text": result_text}]
        except Exception as e:
             return [{"type": "text", "text": f"System Error: {str(e)}"}]

    elif name == "get_scene_info":
        def _get_info():
            scene = bpy.context.scene
            info = f"Scene Name: {scene.name}\n"
            info += f"Frame Current: {scene.frame_current}\n"
            info += f"Render Engine: {scene.render.engine}\n"
            return info
        
        info = run_in_main_thread(_get_info)
        return [{"type": "text", "text": info}]

    elif name == "list_objects":
        def _list_objs():
            return [obj.name for obj in bpy.context.scene.objects]
        
        objects = run_in_main_thread(_list_objs)
        return [{"type": "text", "text": f"Objects: {', '.join(objects)}"}]

    raise ValueError(f"Unknown tool: {name}")

# --- SERVER LOGIC ---

async def run_server(port=8123):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind(('localhost', port))
    except OSError:
        print(f"Port {port} is already in use. Is Blender already running this script?")
        return

    server_sock.listen(1)
    print(f"Blender MCP Server listening on localhost:{port}")

    while True:
        try:
            client_sock, addr = await asyncio.get_running_loop().sock_accept(server_sock)
            print(f"Connected to {addr}")
            
            # Manual JSON-RPC Handler
            buffer = b""
            loop = asyncio.get_running_loop()
            
            while True:
                chunk = await loop.sock_recv(client_sock, 4096)
                if not chunk: break
                buffer += chunk
                
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip(): continue
                    
                    try:
                        req = json.loads(line.decode('utf-8'))
                        # print(f"Received request: {req.get('method')} id={req.get('id')}")
                        
                        response = None
                        
                        if req.get("method") == "initialize":
                            response = {
                                "jsonrpc": "2.0",
                                "id": req.get("id"),
                                "result": {
                                    "protocolVersion": "2024-11-05",
                                    "capabilities": {
                                        "tools": {}
                                    },
                                    "serverInfo": {"name": "blender-mcp", "version": "1.0"}
                                }
                            }
                        
                        elif req.get("method") == "notifications/initialized":
                            pass
                            
                        elif req.get("method") == "tools/list":
                            tools_list = await list_tools()
                            response = {
                                "jsonrpc": "2.0",
                                "id": req.get("id"),
                                "result": {
                                    "tools": tools_list
                                }
                            }
                            
                        elif req.get("method") == "tools/call":
                            params = req.get("params", {})
                            name = params.get("name")
                            args = params.get("arguments", {})
                            
                            try:
                                content = await call_tool(name, args)
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": req.get("id"),
                                    "result": {
                                        "content": content,
                                        "isError": False
                                    }
                                }
                            except Exception as e:
                                print(f"Tool Execution Error: {e}")
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": req.get("id"),
                                    "error": {
                                        "code": -32603,
                                        "message": str(e)
                                    }
                                }
                        
                        else:
                            if "id" in req:
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": req.get("id"),
                                    "error": {"code": -32601, "message": "Method not found"}
                                }

                        if response:
                            await loop.sock_sendall(client_sock, json.dumps(response).encode('utf-8') + b"\n")
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
            
            client_sock.close()
            print("Disconnected")
            
        except Exception as e:
            logger.error(f"Server Error: {e}")
            await asyncio.sleep(1)

def start_server_thread():
    def _target():
        asyncio.run(run_server())
    t = threading.Thread(target=_target, daemon=True)
    t.start()
    print("Blender MCP Server Thread Started.")

if __name__ == "__main__":
    start_server_thread()
