import sys
import socket
import json
import threading
import time

# Configuration
HOST = 'localhost'
PORT = 8123

def main():
    """
    Acts as a bridge between the IDE (Stdio) and Blender (TCP).
    """
    
    # Connect to Blender
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        sys.stderr.write(f"Error: Could not connect to Blender at {HOST}:{PORT}. Make sure 'blender_server.py' is running in Blender.\n")
        sys.exit(1)
        
    # Thread to read from Blender and write to stdout
    def listen_to_blender():
        buffer = b""
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk: break
                buffer += chunk
                
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip(): continue
                    # Forward response to IDE
                    sys.stdout.buffer.write(line + b"\n")
                    sys.stdout.buffer.flush()
        except Exception as e:
            sys.stderr.write(f"Connection lost: {e}\n")
            sys.exit(1)

    t = threading.Thread(target=listen_to_blender, daemon=True)
    t.start()
    
    # Main Loop: Read from stdin (IDE) and send to Blender
    try:
        while True:
            line = sys.stdin.readline()
            if not line: break
            
            # Forward request to Blender
            sock.sendall(line.encode('utf-8') + b"\n")
            
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

if __name__ == "__main__":
    main()
