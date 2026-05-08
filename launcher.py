"""Native-window launcher for Projectizer.

Starts the FastAPI server in a background thread and opens a native
desktop window (via pywebview) pointing at it. Closing the window
exits the process and tears down the server.

This is an *alternative* entry point to ``run.sh`` / ``python app.py``,
which keep working unchanged for users who prefer the browser flow.
"""
import os
import sys
import time
import threading
import urllib.request
import urllib.error

# When launched from a sandboxed macOS .app bundle, the wrapper script runs
# us with cwd=/tmp (because the project may live in a TCC-protected folder
# like ~/Documents and Python's startup chokes on getcwd() there). Once
# Python is up, chdir to the project root so app.py's relative paths
# (config.json, uploads/, static/) resolve correctly.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

PORT = int(os.environ.get("PORT", 8899))
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}"


def _run_server():
    import uvicorn
    from app import app

    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    # uvicorn installs SIGINT/SIGTERM handlers on the main thread. We're
    # not on the main thread here, so disable them — pywebview owns the
    # process lifecycle.
    server.install_signal_handlers = lambda: None
    server.run()


def _wait_for_server(timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(URL, timeout=1).read()
            return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.15)
    return False


def main() -> int:
    threading.Thread(target=_run_server, daemon=True).start()

    if not _wait_for_server():
        sys.stderr.write(f"Projectizer server did not start within 30s on {URL}\n")
        return 1

    import webview
    webview.create_window(
        "Projectizer",
        URL,
        width=1280,
        height=900,
        min_size=(900, 600),
    )
    # private_mode=False: pywebview's default uses a private WKWebView session
    # which strips navigator.mediaDevices.getUserMedia. We need it for the mic
    # recording feature, so disable private mode. Cookies/localStorage also
    # persist across launches as a side effect.
    webview.start(private_mode=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
