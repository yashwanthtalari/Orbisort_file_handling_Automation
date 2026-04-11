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
        if not event.is_directory:
            self.agent.send("FILE_DISCOVERED", event.src_path)

class WatcherAgent(BaseAgent):
    def __init__(self, path_to_watch=None):
        super().__init__("WatcherAgent", subscriptions=["START_WATCHING", "STOP_WATCHING"])
        self.observer = None
        self.path = path_to_watch

    def receive(self, message):
        if message.msg_type == "START_WATCHING":
            self.path = message.data
            self.start()
        elif message.msg_type == "STOP_WATCHING":
            self.stop()

    def start(self):
        if not self.path: return
        self.stop()
        
        self.observer = Observer()
        handler = WatcherHandler(self)
        self.observer.schedule(handler, self.path, recursive=True)
        self.observer.start()
        logger.info(f"WatcherAgent started: {self.path}")
        
        # Optimized Initial Scan
        for root, dirs, files in os.walk(self.path):
            if "Organized" in root: continue
            for file in files:
                self.send("FILE_DISCOVERED", os.path.join(root, file))

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=1)
            self.observer = None
