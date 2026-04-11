import os
import time
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Event
from utils.logger import get_logger
from core.action_engine import OrbisortEngine
from database.db_manager import initialize_db

logger = get_logger()
MAX_WORKERS = 8


def _should_ignore(path: str) -> bool:
    ignored_segments = [".venv", "__pycache__", ".git", "logs"]
    return any(segment in path for segment in ignored_segments)


class OrbisortHandler(FileSystemEventHandler):
    def __init__(self, engine: OrbisortEngine):
        super().__init__()
        self.engine = engine
        self.executor = None

    def _queue_path(self, path: str):
        if _should_ignore(path):
            return
        logger.info("Event for file: %s", path)
        self.executor.submit(self.engine.process_file, path)

    def on_created(self, event):
        if event.is_directory:
            return
        self._queue_path(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self._queue_path(event.dest_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._queue_path(event.src_path)


def _scan_directory(path_to_scan: str, engine: OrbisortEngine, executor: ThreadPoolExecutor):
    logger.info("Running initial scan on %s", path_to_scan)

    futures = []
    for root, dirs, files in os.walk(path_to_scan):
        if _should_ignore(root):
            continue
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if _should_ignore(file_path):
                continue
            futures.append(executor.submit(engine.process_file, file_path))

    for f in futures:
        f.result()


class OrbisortWatcher:
    def __init__(self, path_to_watch: str, recursive: bool = True):
        self.path_to_watch = os.path.abspath(path_to_watch)
        self.recursive = recursive
        self.observer = Observer()
        self.stop_event = Event()
        self.engine = OrbisortEngine()
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def start(self):
        initialize_db()
        os.makedirs(self.path_to_watch, exist_ok=True)
        _scan_directory(self.path_to_watch, self.engine, self.executor)

        handler = OrbisortHandler(self.engine)
        handler.executor = self.executor
        self.observer.schedule(handler, self.path_to_watch, recursive=self.recursive)
        self.observer.start()

        logger.info(
            "Started watcher on %s (recursive=%s)", self.path_to_watch, self.recursive
        )

        try:
            while not self.stop_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, stopping watcher.")
            self.stop()

    def stop(self):
        self.stop_event.set()
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=5)

        self.executor.shutdown(wait=True)
        logger.info("Watcher stopped")


def start_watcher(path_to_watch: str, recursive: bool = True) -> OrbisortWatcher:
    watcher = OrbisortWatcher(path_to_watch, recursive=recursive)
    watcher.start()
    return watcher
