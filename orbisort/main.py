import argparse
import os
import sys

from database.db_manager import initialize_db
from utils.logger import get_logger
from core.watcher import start_watcher
from core.assistant.voice import speak

def main():
    parser = argparse.ArgumentParser(description="Orbisort | Intelligent File Automation")
    parser.add_argument(
        "--watch",
        default=os.path.join(os.getcwd(), "test_folder"),
        help="Folder to watch",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Watch folders recursively",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch Modern GUI interface",
    )
    args = parser.parse_args()

    # Ensure DB is ready
    initialize_db()

    if args.gui:
        from gui import OrbisortGUI
        print("Launching Orbisort Premium UI...")
        app = OrbisortGUI()
        app.mainloop()
        return

    watch_folder = os.path.abspath(args.watch)
    os.makedirs(watch_folder, exist_ok=True)

    logger = get_logger()
    logger.info("Orbisort Service started on %s", watch_folder)
    speak("Orbisort service is starting in background mode.")

    start_watcher(watch_folder, recursive=args.recursive)

if __name__ == "__main__":
    main()
