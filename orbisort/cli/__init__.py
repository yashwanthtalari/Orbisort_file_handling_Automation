import os
from database.db_manager import initialize_db
from utils.logger import get_logger
from core.watcher import start_watcher


def main(watch_folder: str = None, recursive: bool = False):
    if watch_folder is None:
        watch_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_folder")

    watch_folder = os.path.abspath(watch_folder)
    os.makedirs(watch_folder, exist_ok=True)

    initialize_db()
    logger = get_logger()
    logger.info("Orbisort started on %s recursive=%s", watch_folder, recursive)

    start_watcher(watch_folder, recursive=recursive)


if __name__ == "__main__":
    main()
