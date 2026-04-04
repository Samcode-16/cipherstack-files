import sys
import subprocess
from pathlib import Path

PORT = 8000

def main():
    print("=" * 80)
    print("SMART SERVER LAUNCHER")
    print("=" * 80)

    # Always use the same Python that launched this script
    python = sys.executable
    print(f"Using Python: {python}")

    cmd = [python, "-m", "uvicorn", "app:app",
           "--host", "0.0.0.0",
           "--port", str(PORT),
           "--reload"]

    print(f"Command: {' '.join(cmd)}")
    print("=" * 80)
    print("Server running. Press CTRL+C to stop.")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()