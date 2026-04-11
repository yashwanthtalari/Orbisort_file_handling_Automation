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
            # Send specialized message to LocatorAgent
            coordinator.publish("Assistant", "OPEN_CATEGORY", target)
            return f"Opening your {target} folder right away! ✨"
        else:
            coordinator.publish("Assistant", "OPEN_FOLDER", ORGANIZED_DIR)
            return "Opening the main Organized directory for you. ✨"

    elif action == "organize":
        return "I'm already watching your folders! Just drop any file into the watch folder and I'll handle the rest."

    else:
        return "I'm ready! You can ask me to 'search for documents', 'open my photos', or 'find the latest invoice'."
