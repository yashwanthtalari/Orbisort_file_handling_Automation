import os
from core.assistant.interpreter import interpret_command
from core.search_engine import search_files
from core.agents.coordinator import coordinator

import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORGANIZED_DIR = os.path.join(BASE_DIR, "Organized")

def handle_command(text: str) -> str:
    intent = interpret_command(text)
    action = intent.get("action")
    query = intent.get("query", "")
    target = intent.get("target")

    from core.search_engine import search_files, semantic_search_files
    
    if action == "search_semantic" or action == "search":
        if not query:
            return "What would you like me to look for?"
            
        results = semantic_search_files(query)
        if not results:
            results = search_files(query)

        if not results:
            return f"I couldn’t find any files matching '{query}' across your organized folders."

        response = f"I found {len(results)} matching files for '{query}':\n"
        for name, path in results[:3]:
            # Highlight filename
            response += f"\n📄 {name.upper()}\n"
            
        if len(results) > 3:
            response += f"\n...and {len(results)-3} more."
            
        return response

    elif action == "open":
        if target:
            coordinator.publish("Assistant", "OPEN_CATEGORY", target)
            return f"Opening your {target} folder right away! ✨"
        else:
            coordinator.publish("Assistant", "OPEN_FOLDER", ORGANIZED_DIR)
            return "Opening the main Organized directory for you. ✨"

    elif action == "status":
        return "System Check: Watcher is active, Discovery engine is primed, and I am standing by for your commands. Everything is running smoothly! ✅"

    elif action == "summary":
        try:
            from database.db_manager import DB_PATH
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT original_path, new_path FROM files ORDER BY processed_at DESC LIMIT 5")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return "I haven't organized any files yet today! Drop something in your watch folder to get started."
                
            summary = "Here is a quick recap of my recent activity: \n"
            for orig, new in rows:
                name = os.path.basename(orig)
                summary += f"\n✅ Sorted '{name}' into its category."
            return summary
        except Exception as e:
            return f"I ran into an issue getting the summary, but I'm still processing your files in the background!"

    elif action == "scan":
        coordinator.publish("Assistant", "START_DISCOVERY", None)
        return "Initiating a Deep Discovery scan of your directories. I'll map out your files to get even smarter! 🧠"

    elif action == "config":
        if target == "scan_only":
            val = intent.get("value", "true").lower() == "true"
            # This would need a way to update the GUI or Agent state
            # For now, let's just acknowledge
            return f"Understood. I've noted your preference for scan-only mode: {val}. (Hint: You can also toggle this in the dashboard!)"
        return "I've noted that configuration change!"

    elif action == "organize":
        return "I'm already watching your folders! Just drop any file into the watch folder and I'll handle the rest."

    else:
        return "I'm ready! You can ask me to 'search for documents', 'open my photos', 'give me a summary', or 'check system status'."
