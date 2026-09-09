"""
WATERSCOPE Unified Development Server Launcher
Starts both the FastAPI Backend (:8000) and the Vite Frontend (:5173).
Usage:
    python dev.py
"""
import sys
import os
import subprocess
import signal
import time

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    print("=" * 60)
    print("  Starting WATERSCOPE Unified Development Environment")
    print("=" * 60)
    print("  Backend API:  http://127.0.0.1:8000")
    print("  Frontend UI:  http://localhost:5173")
    print("  Press Ctrl+C to stop both servers.")
    print("=" * 60 + "\n")

    # Start FastAPI backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=root_dir)

    # Start Vite frontend
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_proc = subprocess.Popen([npm_cmd, "run", "dev"], cwd=frontend_dir)

    try:
        while True:
            time.sleep(1)
            # If any process exits unexpectedly, exit both
            if backend_proc.poll() is not None:
                print("\n[WATERSCOPE] Backend process stopped.")
                break
            if frontend_proc.poll() is not None:
                print("\n[WATERSCOPE] Frontend process stopped.")
                break
    except KeyboardInterrupt:
        print("\n[WATERSCOPE] Shutting down servers...")
    finally:
        for proc in [backend_proc, frontend_proc]:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        print("[WATERSCOPE] Servers stopped.")

if __name__ == "__main__":
    main()
