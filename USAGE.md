# Smart Server Launcher - Usage Guide

## Problem Solved ✅

Previously, after making code changes, restarting the server would fail with:
```
ERROR: [Errno 10048] only one usage of each socket address
```

This happened because the previous server process was still holding port 8000. You'd need to manually run `taskkill` before restarting.

## Solution

Two smart launchers automatically clean up the port before starting the server:

### Option 1: Python Launcher (Recommended)

**Command:**
```bash
python run_server.py
```

**What it does:**
- Detects if port 8000 is in use
- Kills the existing process (if any)
- Waits for the port to be released
- Starts the server with auto-reload enabled
- Continues running until you press `CTRL+C`

**Example output:**
```
================================================================================
SMART SERVER LAUNCHER
================================================================================
⚠  Port 8000 is in use...
⚠  Port 8000 still in use, but attempting to start server...

✓ Port 8000 is free
🚀 Starting server...

================================================================================
Server running. Press CTRL+C to stop.

INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Advantages:**
- Cross-platform compatible (Windows, Mac, Linux)
- Single command
- Cleaner output

---

### Option 2: PowerShell Launcher

**Command:**
```powershell
powershell -ExecutionPolicy Bypass -File .\run_server.ps1
```

**What it does:**
- Same functionality as Python launcher
- Windows-native implementation
- Automatic port cleanup

**Advantages:**
- Windows-native (no Python subprocess overhead)
- Can be called from batch files or Windows Task Scheduler

---

### Option 3: Manual (Old Way - Not Recommended)

```bash
# This may fail with port binding error
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**If this fails, manually kill the process:**
```powershell
# PowerShell
Get-NetTCPConnection -LocalPort 8000 | Foreach-Object {Stop-Process -Id $_.OwningProcess -Force}

# Or Command Prompt
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Recommended Workflow

1. **Start the server:**
   ```bash
   python run_server.py
   ```

2. **Make code changes** in your editor

3. **Server auto-reloads** (no manual restart needed)

4. **Stop the server:**
   - Press `CTRL+C` in the terminal

5. **Make more changes and restart:**
   - Just run `python run_server.py` again
   - No port binding errors! ✅

---

## Advanced Usage

### Using a Custom Port

```bash
# Python launcher (custom port 9000)
python run_server.py 9000

# Or with PowerShell
powershell -ExecutionPolicy Bypass -File .\run_server.ps1 -Port 9000
```

### Disable Auto-Reload

```bash
# Python launcher
python run_server.py

# PowerShell launcher
powershell -ExecutionPolicy Bypass -File .\run_server.ps1 -NoReload
```

---

## Troubleshooting

### "Port 8000 is still in use, but attempting to start server..."

This message means the launcher tried to kill the process but couldn't (possibly due to permissions or the process is essential). The server will still try to start. If it fails, there may be another application using port 8000.

**Solution:** Kill it manually:
```powershell
Get-Process python | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

### "Cannot overwrite variable PID"

This error (now fixed) was due to PowerShell's reserved variable name. If you see this, update your `run_server.ps1` file to use the latest version.

---

## Under the Hood

Both launchers implement this logic:

1. **Check port status**: Is port 8000 in use?
2. **Kill process if needed**: Use `taskkill` (Python) or `Stop-Process` (PowerShell)
3. **Wait for cleanup**: Give the OS 1-2 seconds to release the port
4. **Start server**: Run `uvicorn` with auto-reload
5. **Monitor**: Display server logs until user stops it

This eliminates the manual port cleanup step entirely! 🎉

---

## Files

- `run_server.py` - Python launcher (recommended)
- `run_server.ps1` - PowerShell launcher
- `app.py` - Main FastAPI application
- `keys.json` - Auto-generated encryption keys (git-ignored)

