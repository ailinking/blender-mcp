import sys
import os
import runpy

def install():
    # Target directory for libraries (relative to this script)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    libs_dir = os.path.join(current_dir, "libs")
    log_file = os.path.join(current_dir, "install_log.txt")
    
    with open(log_file, "w") as f_log:
        def log(msg):
            print(msg)
            f_log.write(msg + "\n")
            f_log.flush()

        log(f"Starting installation...")
        
        if not os.path.exists(libs_dir):
            os.makedirs(libs_dir)
        
        log(f"Installing dependencies to {libs_dir}...")
        
        # Ensure pip is available
        try:
            import pip
        except ImportError:
            log("pip not found. Attempting to ensurepip...")
            try:
                import ensurepip
                ensurepip.bootstrap()
            except Exception as e:
                log(f"Failed to ensurepip: {e}")
                return

        # Dependencies to install
        # 'mcp' is the core library.
        # 'pywin32' is required on Windows for named pipes/event loops used by some libs,
        # though we use TCP, 'mcp' might internally depend on platform specific things.
        packages = ["mcp"]
        if sys.platform == "win32":
            packages.append("pywin32")
        
        sys.argv = [
            "pip", "install", 
            *packages,
            "--target", libs_dir,
            "--no-user"
        ]
        
        # Capture stdout/stderr of pip
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # Redirect stdout/stderr to log file
        sys.stdout = f_log
        sys.stderr = f_log
        
        try:
            log(f"Running pip install {' '.join(packages)}...")
            runpy.run_module("pip", run_name="__main__")
            log("Installation successful.")
        except SystemExit as e:
            if e.code == 0:
                log("Installation successful (exit code 0).")
            else:
                log(f"Installation failed with exit code {e.code}")
        except Exception as e:
            log(f"Installation failed with error: {e}")
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

if __name__ == "__main__":
    install()
