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
        self.current_watch_path = None
        self.system_map = {}
        super().__init__("LocatorAgent", subscriptions=["OPEN_FOLDER", "SEARCH_FILE", "OPEN_CATEGORY", "START_WATCHING", "SYSTEM_MAP_DISCOVERED"])
        self.report_status(True)

    def receive(self, message):
        if message.msg_type == "START_WATCHING":
            self.current_watch_path = message.data
        
        elif message.msg_type == "SYSTEM_MAP_UPDATED":
            logger.info("LocatorAgent notified of system map update in DB")
            
        elif message.msg_type == "OPEN_FOLDER":
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
        """Intelligently map common names to discovered or organized folders"""
        mapping = {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            "photos": [".jpg", ".jpeg", ".png"],
            "videos": [".mp4", ".mkv", ".mov", ".avi"],
            "music": [".mp3", ".wav", ".flac", ".m4a"],
            "documents": [".docx", ".pdf", ".txt", ".xlsx"],
            "pdf": [".pdf"],
            "code": [".py", ".js", ".html", ".css", ".cpp", ".java"],
            "python": [".py"],
            "data": [".csv", ".json", ".xml", ".sql"],
            "csv": [".csv"]
        }
        
        # 1. Advanced Discovery: Query DB for folders that PRIMARILY contain these types
        target_exts = mapping.get(category)
        if target_exts:
            try:
                from database.db_manager import DB_PATH
                import sqlite3
                import json
                
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT path, extensions FROM system_map")
                rows = cursor.fetchall()
                
                best_match = None
                highest_count = 0
                
                for path, ext_json in rows:
                    ext_counts = json.loads(ext_json)
                    match_count = sum(ext_counts.get(ext, 0) for ext in target_exts)
                    
                    if match_count > highest_count:
                        highest_count = match_count
                        best_match = path
                
                conn.close()
                if best_match:
                    logger.info(f"Discovery Match (DB): Found category '{category}' in {best_match}")
                    return best_match
            except Exception as e:
                logger.error(f"LocatorAgent DB discovery failed: {e}")

        # 2. Rule-based Sub-path Mapping (for Organized folders)
        # This is what we used before, keep as fallback
        organized_sub_mapping = {
            "images": "Media/Images", "image": "Media/Images", "photos": "Media/Images",
            "videos": "Media/Videos", "music": "Media/Music", "pdf": "Documents/PDF",
            "documents": "Documents", "code": "Code", "data": "Data", "organized": ""
        }
        
        sub_path = organized_sub_mapping.get(category)
        if sub_path:
            # First, check in current watch path
            if self.current_watch_path:
                local_path = os.path.join(self.current_watch_path, sub_path)
                if os.path.exists(local_path):
                    return local_path
            
            # Fallback to central Organized folder
            full_path = os.path.join(self.organized_dir, sub_path)
            if os.path.exists(full_path):
                return full_path
        
        # 3. Comprehensive name-based discovery
        if self.system_map:
            for path, info in self.system_map.items():
                if info['name'].lower() == category:
                    return path

        return self.current_watch_path or self.organized_dir

    def _open_path(self, path):
        try:
            path = os.path.normpath(path)
            
            # If path doesn't exist but is within our controlled directories, try to create it
            if not os.path.exists(path):
                should_create = False
                if self.organized_dir and self.organized_dir in path: should_create = True
                if self.current_watch_path and self.current_watch_path in path: should_create = True
                
                if should_create:
                    os.makedirs(path, exist_ok=True)
                    logger.info(f"LocatorAgent created missing directory: {path}")
                else:
                    logger.warning(f"LocatorAgent failed: Path does not exist {path}")
                    return

            # Open folder or select file
            if os.path.isfile(path):
                # Using Popen with a string ensures the comma-select syntax works correctly on all Windows vers
                subprocess.Popen(f'explorer /select,"{path}"')
            else:
                os.startfile(path)
                
            logger.info(f"LocatorAgent opened: {path}")
            
        except Exception as e:
            logger.error(f"LocatorAgent shell error: {e}")
