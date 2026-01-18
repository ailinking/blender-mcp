@echo off
REM ================================================================
REM Blender MCP Dependency Installer
REM ================================================================
REM This script helps install the required Python packages ('mcp')
REM directly into a local 'libs' folder using Blender's Python.
REM ================================================================

REM Try to detect Blender Launcher from Microsoft Store
set "BLENDER_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\blender-launcher.exe"

REM Check if it exists, otherwise ask user to set it
if not exist "%BLENDER_EXE%" (
    echo [INFO] Blender Launcher not found in default Windows Store location.
    echo [INFO] Trying standard 'blender' command...
    set "BLENDER_EXE=blender"
)

echo.
echo Using Blender executable: %BLENDER_EXE%
echo.
echo Installing dependencies...
echo This process runs in the background. Please wait...
echo.

"%BLENDER_EXE%" -b --python "%~dp0install_dependencies.py"

echo.
echo Installation process finished.
echo Please check "install_log.txt" to verify success.
echo.
pause
