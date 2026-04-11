import os
import subprocess
from core.agents.base_agent import BaseAgent
from database.vector_store import vector_store
from utils.logger import get_logger

logger = get_logger()

class LocatorAgent(BaseAgent):
    def __init__(self):
        # We also need the Organized directory reference
        from core.action_engine import ORGANIZED_DIR
        self.organized_dir = ORGANIZED_DIR
        super().__init__("LocatorAgent", subscriptions=["OPEN_FOLDER", "SEARCH_FILE", "OPEN_CATEGORY"])

    def receive(self, message):
        if message.msg_type == "OPEN_FOLDER":
            path = message.data
            self._open_path(path)
        
        elif message.msg_type == "OPEN_CATEGORY":
            category = message.data.lower()
            target_path = self.resolve_category_path(category)
            if target_path:
                self._open_path(target_path)
        
        elif message.msg_type == "SEARCH_FILE":
            query = message.data
            results = vector_store.semantic_search(query) 
            self.send("SEARCH_RESULTS", results)

    def resolve_category_path(self, category):
        """Intelligently map common names to organized folders"""
        mapping = {
            "images": "Media/Images",
            "photos": "Media/Images",
            "pictures": "Media/Images",
            "pdf": "Documents/PDF",
            "documents": "Documents",
            "code": "Code",
            "python": "Code/Python",
            "data": "Data",
            "csv": "Data/CSV"
        }
        
        sub_path = mapping.get(category)
        if sub_path:
            full_path = os.path.join(self.organized_dir, sub_path)
            if os.path.exists(full_path):
                return full_path
        
        # Fallback: check if the name matches any existing folder in Organized
        if os.path.exists(self.organized_dir):
            for root, dirs, files in os.walk(self.organized_dir):
                for d in dirs:
                    if d.lower() == category:
                        return os.path.join(root, d)
        
        return self.organized_dir

    def _open_path(self, path):
        try:
            if os.path.exists(path):
                # If it's a file, open the directory and select the file
                if os.path.isfile(path):
                    subprocess.run(['explorer', '/select,', os.path.normpath(path)])
                else:
                    os.startfile(os.path.normpath(path))
                logger.info(f"LocatorAgent opened: {path}")
            else:
                logger.warning(f"LocatorAgent failed: Path does not exist {path}")
        except Exception as e:
            logger.error(f"LocatorAgent shell error: {e}")
