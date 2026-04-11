import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger()

class WatcherHandler(FileSystemEventHandler):
    def __init__(self, agent):
        self.agent = agent

    def on_created(self, event):
        if not event.is_directory and not getattr(self.agent, 'scan_only', False):
            self.agent.send("FILE_DISCOVERED", event.src_path)

class WatcherAgent(BaseAgent):
    def __init__(self, path_to_watch=None):
        super().__init__("WatcherAgent", subscriptions=["START_WATCHING", "STOP_WATCHING", "START_DISCOVERY"])
        self.observer = None
        self.path = path_to_watch
        self.scan_only = False
        self.report_status(True)

    def receive(self, message):
        if message.msg_type == "START_WATCHING":
            if isinstance(message.data, dict):
                self.path = message.data.get("path")
                self.scan_only = message.data.get("scan_only", False)
            else:
                self.path = message.data
                self.scan_only = False
            self.start()
        elif message.msg_type == "STOP_WATCHING":
            self.stop()
        elif message.msg_type == "START_DISCOVERY":
            if self.path:
                import threading
                threading.Thread(target=self.deep_discovery, args=(self.path,), daemon=True).start()

    def start(self):
        if not self.path: return
        self.stop()
        
        self.observer = Observer()
        handler = WatcherHandler(self)
        self.observer.schedule(handler, self.path, recursive=True)
        self.observer.start()
        logger.info(f"WatcherAgent started on: {self.path} (Scan Only: {self.scan_only})")
        
        # Phase 1: Immediate Organization (Only if NOT scan_only)
        if not self.scan_only:
            import threading
            threading.Thread(target=self._initial_queue, args=(self.path,), daemon=True).start()
        
        # Phase 2: Deep Discovery for intelligence
        import threading
        threading.Thread(target=self.deep_discovery, args=(self.path,), daemon=True).start()

    def _initial_queue(self, path):
        for root, dirs, files in os.walk(path):
            if any(s in root for s in [".venv", "__pycache__", ".git", "Organized"]): continue
            for file in files:
                self.send("FILE_DISCOVERED", os.path.join(root, file))

    def deep_discovery(self, path_to_scan):
        logger.info(f"Deep Discovery started for: {path_to_scan}")
        self.send("ASSISTANT_STATUS", "Starting Deep Discovery...")
        
        from database.db_manager import DB_PATH
        import sqlite3
        import json
        from datetime import datetime
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        count = 0
        for root, dirs, files in os.walk(path_to_scan):
            # Skip hidden or environment folders
            if any(s in root for s in [".venv", "__pycache__", ".git", "AppData", "Windows"]): continue
            
            folder_name = os.path.basename(root)
            if not folder_name: folder_name = root
            
            ext_counts = {}
            for file in files:
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
            
            # Persist to DB
            try:
                cursor.execute(
                    """
                    INSERT INTO system_map (path, name, extensions, file_count, last_scanned)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                    extensions=excluded.extensions,
                    file_count=excluded.file_count,
                    last_scanned=excluded.last_scanned
                    """,
                    (root, folder_name, json.dumps(ext_counts), len(files), datetime.now().isoformat())
                )
                count += 1
                if count % 100 == 0: 
                    conn.commit()
                    self.send("ASSISTANT_STATUS", f"Discovery progress: {count} folders mapped...")
            except Exception as e:
                logger.error(f"Failed to index folder {root}: {e}")

        conn.commit()
        conn.close()
        
        self.send("ASSISTANT_STATUS", f"Deep Discovery complete! Mapped {count} folders.")
        self.send("SYSTEM_MAP_UPDATED", None) # Notify agents to reload from DB
        logger.info(f"Deep Discovery complete: mapped {count} folders")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=1)
            self.observer = None
