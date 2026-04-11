from core.agents.base_agent import BaseAgent
from core.action_engine import OrbisortEngine
from utils.logger import get_logger

logger = get_logger()

class OrganizerAgent(BaseAgent):
    def __init__(self):
        super().__init__("OrganizerAgent", subscriptions=["FILE_DISCOVERED"])
        self.engine = OrbisortEngine()

    def receive(self, message):
        if message.msg_type == "FILE_DISCOVERED":
            file_path = message.data
            new_path = self.engine.process_file(file_path)
            
            if new_path:
                self.send("FILE_ORGANIZED", {
                    "original": file_path,
                    "new": new_path
                })
