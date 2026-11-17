"""Desktop launcher: runs the API on localhost with a per user SQLite database and opens the UI in the browser.

Run from the parent directory with `python perfima/desktop.py`, or as the bundled executable.
"""
import logging
import os
import secrets
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

APP_NAME = "perfima"
HOST = "127.0.0.1"
DEFAULT_PORT = 8765
# the UI sends a heartbeat every 30 seconds, after this long without one the tab is assumed closed
IDLE_TIMEOUT_SECONDS = 120
# index.html carries this tag, it tells a running Perfima apart from anything else on the port
UI_MARKER = b'<meta name="application-name" content="Perfima">'

logger = logging.getLogger("perfima.desktop")


def data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", "")
        if not os.path.isabs(base):
            base = str(Path.home() / ".local" / "share")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


# Tokens stay valid across restarts because the signing key is generated once and kept with the data
def load_secret_key(directory: Path) -> str:
    path = directory / "secret_key"
    if path.exists():
        key = path.read_text().strip()
        if key:
            return key
    key = secrets.token_urlsafe(48)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(key)
    return key


def bind(port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # lets a quick relaunch reuse the port; on Windows this flag would let two servers share it, so it's skipped
    if sys.platform != "win32":
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((HOST, port))
    except OSError:
        sock.close()
        return None
    return sock


def ui_url(port: int) -> str:
    return f"http://{HOST}:{port}/app/"


def is_perfima_running(port: int) -> bool:
    try:
        with urllib.request.urlopen(ui_url(port), timeout=2) as response:
            return UI_MARKER in response.read(4096)
    except OSError:
        return False


def open_browser(port: int):
    url = ui_url(port)
    logger.info(f"Opening {url}")
    if not webbrowser.open(url):
        print(f"Open {url} in your browser")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    directory = data_dir()
    os.environ["DATABASE_URL"] = f"sqlite:///{(directory / 'perfima.db').as_posix()}"
    os.environ["PERFIMA_LOCAL_MODE"] = "1"
    os.environ["SECRET_KEY"] = load_secret_key(directory)
    # the bundled app would otherwise give matplotlib a new temp dir and rebuild its font cache on every launch
    os.environ["MPLCONFIGDIR"] = str(directory / "matplotlib")

    sock = bind(DEFAULT_PORT)
    if sock is None:
        if is_perfima_running(DEFAULT_PORT):
            logger.info("Perfima is already running")
            open_browser(DEFAULT_PORT)
            return
        logger.info(f"Port {DEFAULT_PORT} is taken, picking a free one")
        sock = bind(0)
    port = sock.getsockname()[1]

    # imported only now, the database and auth settings are read from the environment at import time
    import uvicorn
    from perfima.main import app
    from perfima.services import local_service

    logger.info(f"Data is stored in {directory}")
    config = uvicorn.Config(app, host=HOST, port=port, loop="asyncio", http="h11", ws="none", log_level="info")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()

    while not server.started:
        if not thread.is_alive():
            sys.exit("Perfima failed to start")
        time.sleep(0.1)

    # the idle clock starts once the server is up, so a slow start doesn't count against the browser
    local_service.state.heartbeat()
    open_browser(port)

    state = local_service.state
    try:
        while not state.shutdown.is_set():
            if state.idle_seconds() > IDLE_TIMEOUT_SECONDS:
                logger.info("No heartbeat from the browser, shutting down")
                break
            state.shutdown.wait(1)
    except KeyboardInterrupt:
        pass

    server.should_exit = True
    thread.join(timeout=10)
    logger.info("Perfima stopped")


if __name__ == "__main__":
    # `python perfima/desktop.py` puts perfima/ itself on the path, but the code imports as the perfima package
    if not getattr(sys, "frozen", False):
        package_dir = Path(__file__).resolve().parent
        sys.path = [p for p in sys.path if Path(p or ".").resolve() != package_dir]
        sys.path.insert(0, str(package_dir.parent))
    main()
