import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import json
from utils.logger import get_logger

logger = get_logger()
load_dotenv()

class Intent(BaseModel):
    action: str = Field(description="The action to perform. Can be 'search_semantic', 'organize', 'open', 'summary', 'status', 'scan', 'config', or 'unknown'")
    query: str = Field(None, description="The query string, if searching or summarizing")
    target: str = Field(None, description="Target folder/category to open, or setting name")
    value: str = Field(None, description="Value for a setting or config change")

def interpret_command(text: str) -> dict:
    """
    Uses Google GenAI to parse natural language instructions into a structured dictionary.
    Fallback to rule-based logic if API key isn't provided or call fails.
    """
    text = text.lower().strip()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                f"You are the brain of Orbisort, an AI file manager. User says: '{text}'.\n"
                "Extract the intent using these capabilities:\n"
                "- 'search_semantic': Looking for specific files or topics.\n"
                "- 'open': Opening categories (images, docs, code, music) or general folders.\n"
                "- 'organize': Sorting/cleaning files in the watch folder.\n"
                "- 'status': Checking agent health or system progress.\n"
                "- 'summary': Reviewing recent activities.\n"
                "- 'scan': Triggering deep discovery/indexing.\n"
                "- 'config': Changing 'scan-only' mode or other settings."
            )
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Intent,
                    temperature=0.1
                )
            )
            data = json.loads(response.text)
            return data
        except Exception as e:
            logger.error(f"GenAI intent parsing failed: {e}")
            pass
            
    # --- Rule-Based Fallback ---
    # 1. New Status/Summary Fallbacks
    if any(word in text for word in ["status", "how are you", "health", "ready", "running"]):
        return {"action": "status"}
    if any(word in text for word in ["summary", "organized", "today", "recent", "activity"]):
        return {"action": "summary"}
    if any(word in text for word in ["scan", "index", "discover", "map"]):
        return {"action": "scan"}
    if "only" in text and "scan" in text:
        return {"action": "config", "target": "scan_only", "value": "true"}

    # Existing Open Logic
    categories = ["images", "photos", "pictures", "videos", "music", "documents", "pdf", "code", "python", "data", "csv", "organized"]
    
    if any(word in text for word in ["open", "show", "go to", "locate"]):
        # Check if any category is mentioned
        for cat in categories:
            if cat in text:
                return {"action": "open", "target": cat}
        
        # If "folder" is mentioned with a search-like word, try to extract target
        if "folder" in text:
            for cat in ["image", "photo", "picture", "video", "doc", "code", "python", "data"]:
                if cat in text:
                    mapping = {"image": "images", "photo": "images", "picture": "images", "doc": "documents"}
                    target = mapping.get(cat, cat)
                    return {"action": "open", "target": target}

    if "open" in text:
        return {"action": "open", "target": "organized" if "organized" in text else None}
        
    if any(word in text for word in ["organize", "sort", "clean", "arrange"]):
        return {"action": "organize"}
        
    if any(word in text for word in ["search", "find", "locate", "where"]):
        import re
        match = re.search(r'(search|find|locate|where is) (for )?(.*)', text)
        query = match.group(3).strip() if match else text
        query = query.replace(" folder", "").strip()
        return {"action": "search_semantic", "query": query}
        
    return {"action": "unknown"}
