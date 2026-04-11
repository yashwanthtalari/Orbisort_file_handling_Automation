import os
import sqlite3
from datetime import datetime
from typing import Optional

from utils.hashing import generate_hash
from utils.file_utils import move_file, get_file_metadata
from utils.logger import get_logger
from database.db_manager import DB_PATH
from core.rule_engine import load_rules, match_rule
from core.document_parser import extract_text
from database.vector_store import vector_store
from core.assistant.voice import speak

logger = get_logger()

import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORGANIZED_DIR = os.path.join(BASE_DIR, "Organized")


class OrbisortEngine:
    def __init__(self, db_path: str = DB_PATH, base_dir: str = BASE_DIR):
        self.db_path = db_path
        self.base_dir = base_dir
        self.organized_dir = os.path.join(self.base_dir, "Organized")

    def _execute_db(self, query: str, params: tuple = (), fetch_one: bool = False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)

        result = cursor.fetchone() if fetch_one else None
        if not fetch_one:
            conn.commit()

        conn.close()
        return result

    def is_duplicate(self, file_hash: str) -> bool:
        result = self._execute_db(
            "SELECT id FROM files WHERE file_hash = ?", (file_hash,), fetch_one=True
        )
        return result is not None

    def log_to_db(
        self,
        original_path: str,
        new_path: str,
        metadata: dict,
        file_hash: str,
        status: str,
    ) -> None:
        self._execute_db(
            """
            INSERT INTO files (
                original_path,
                new_path,
                file_hash,
                size,
                created_at,
                processed_at,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                original_path,
                new_path,
                file_hash,
                metadata.get("size"),
                metadata.get("created_at"),
                datetime.now().isoformat(),
                status,
            ),
        )

    def determine_target_folder(self, extension: str, filepath: str) -> str:
        extension = extension.strip().lower().lstrip(".")
        ext_key = f".{extension}" if extension else ""

        rules = load_rules()
        rule = match_rule(ext_key, rules)

        if rule:
            target = rule.get("action", {}).get("move_to")
        elif extension:
            target = os.path.join("Organized", "Others", extension)
        else:
            target = os.path.join("Organized", "Others", "Unknown")

        if not target:
            target = os.path.join("Organized", "Others", "Unknown")

        if not os.path.isabs(target):
            target = os.path.join(self.base_dir, target)

        # Intelligent folder depth: 
        # Only create year/month/day subfolders if the target category has > 5 files
        # This keeps simple collections clean while scaling for large ones.
        os.makedirs(target, exist_ok=True)
        existing_files = [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
        
        if len(existing_files) > 5:
            try:
                timestamp = os.path.getctime(filepath)
            except Exception:
                timestamp = os.path.getmtime(filepath)

            dt = datetime.fromtimestamp(timestamp)
            year = str(dt.year)
            month = f"{dt.month:02d}"
            target = os.path.join(target, year, month)
            
            # Sub-divide by day only if month has > 20 files
            os.makedirs(target, exist_ok=True)
            month_files = [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
            if len(month_files) > 20:
                day = f"{dt.day:02d}"
                target = os.path.join(target, day)

        return os.path.normpath(target)

    def process_file(self, filepath: str) -> Optional[str]:
        try:
            if not os.path.exists(filepath):
                logger.debug("process_file called on nonexistent path: %s", filepath)
                return None

            abs_path = os.path.abspath(filepath)
            if os.path.commonpath([abs_path, self.organized_dir]) == self.organized_dir:
                logger.debug("Skipping already organized file: %s", abs_path)
                return None

            _, ext = os.path.splitext(filepath)
            extension = ext.lstrip(".").lower()

            target_folder = self.determine_target_folder(extension, filepath)
            os.makedirs(target_folder, exist_ok=True)

            filename = os.path.basename(filepath)
            dest_path = os.path.join(target_folder, filename)

            if os.path.exists(dest_path):
                os.remove(dest_path)

            file_hash = generate_hash(filepath)
            if self.is_duplicate(file_hash):
                logger.warning("Duplicate detected: %s", filepath)
                self.log_to_db(
                    filepath,
                    dest_path,
                    get_file_metadata(filepath),
                    file_hash,
                    "duplicate",
                )
                return None

            new_path = move_file(filepath, target_folder)
            metadata = get_file_metadata(new_path)

            self.log_to_db(filepath, new_path, metadata, file_hash, "moved")
            logger.info("File moved → %s", new_path)
            speak(f"Organized {filename}")
            
            # Extract content and add to vector store for semantic search
            try:
                extracted_text = extract_text(new_path)
                if extracted_text:
                    vector_store.add_document(new_path, extracted_text, {"file_name": filename, "extension": extension})
                    logger.info(f"Indexed content for semantic search: {new_path}")
            except Exception as e:
                logger.error(f"Failed to index {new_path}: {e}")

            return new_path

        except Exception as exc:
            logger.exception("Error processing file %s", filepath)
            return None


def process_file(filepath: str) -> Optional[str]:
    engine = OrbisortEngine()
    return engine.process_file(filepath)
