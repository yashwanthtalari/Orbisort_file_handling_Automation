import argparse
import os

from database.db_manager import initialize_db
from utils.logger import get_logger
from core.watcher import start_watcher


def main():
    parser = argparse.ArgumentParser(description="Orbisort file organizer")
    parser.add_argument(
        "--watch",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_folder"),
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
        help="Launch GUI interface",
    )
    args = parser.parse_args()

    if args.gui:
        from gui import OrbisortGUI
        import tkinter as tk

        root = tk.Tk()
        app = OrbisortGUI(root)
        root.mainloop()
        return

    watch_folder = os.path.abspath(args.watch)
    os.makedirs(watch_folder, exist_ok=True)

    initialize_db()
    logger = get_logger()
    logger.info("Orbisort started on %s recursive=%s", watch_folder, args.recursive)

    start_watcher(watch_folder, recursive=args.recursive)


if __name__ == "__main__":
    main()
