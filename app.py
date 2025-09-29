from pathlib import Path
import sys

# Ensure the project root (which contains the ``harmony`` package) is on the
# import path when the module is executed directly. This mirrors the behaviour
# of ``python -m`` and prevents ``ModuleNotFoundError`` when running the script
# from environments where the working directory is different from the file's
# location (e.g. PowerShell on Windows).
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Harmony import create_app, socketio

app = create_app()


if __name__ == "__main__":
    socketio.run(app, debug=True)
