#!/usr/bin/env python3
"""
Smart server launcher - Automatically kills existing process on port 8000 before starting server.
Run this script instead of running uvicorn directly.
"""

import subprocess
import sys
import time
import socket
import os

def is_port_in_use(port):
    """Check if a port is in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def get_process_on_port(port):
    """Get PID of process using the port (Windows)."""
    try:
        result = subprocess.run(
            f'Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess',
            shell=True,
            capture_output=True,
            text=True,
            executable='powershell.exe'
        )
        if result.stdout.strip():
            return int(result.stdout.strip())
    except:
        pass
    return None

def kill_port(port):
    """Kill process on the given port (Windows)."""
    pid = get_process_on_port(port)
    if pid:
        try:
            print(f"🔪 Killing process {pid} on port {port}...")
            os.system(f'taskkill /PID {pid} /F >nul 2>&1')
            time.sleep(1)  # Wait for port to be released
            print(f"✓ Process killed, port {port} released")
            return True
        except Exception as e:
            print(f"✗ Failed to kill process: {e}")
            return False
    return False

def start_server(port=8000, reload=True):
    """Start the FastAPI server."""
    print("="*80)
    print(f"SMART SERVER LAUNCHER")
    print("="*80)
    
    # Check if port is in use
    if is_port_in_use(port):
        print(f"⚠  Port {port} is in use...")
        kill_port(port)
        time.sleep(1)  # Wait for port to be released
    
    # Double-check port is free before starting
    if is_port_in_use(port):
        print(f"⚠  Port {port} still in use, but attempting to start server...")
        time.sleep(2)
    
    print(f"\n✓ Port {port} is free")
    print("🚀 Starting server...\n")
    
    # Build command
    cmd = [
        sys.executable, 
        '-m', 
        'uvicorn', 
        'app:app',
        '--host', '0.0.0.0',
        '--port', str(port),
    ]
    
    if reload:
        cmd.append('--reload')
    
    print(f"Command: {' '.join(cmd)}\n")
    print("="*80)
    print("Server running. Press CTRL+C to stop.\n")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        sys.exit(0)

if __name__ == "__main__":
    # Optional: accept custom port as argument
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [port]")
            sys.exit(1)
    
    start_server(port=port)
