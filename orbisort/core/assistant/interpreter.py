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
    action: str = Field(description="The action to perform. Can be 'search_semantic', 'organize', 'open', 'summarize', or 'unknown'")
    query: str = Field(None, description="The query string, if searching or summarizing")
    target: str = Field(None, description="Target folder to open, if applicable")

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
            # Instruct the model to return JSON matching the Intent schema
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Extract the intent from this user request: '{text}'",
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
            # Fall through to rule-based fallback
            pass
            
    # --- Rule-Based Fallback ---
    if "open" in text:
        target = "organized" if "organize" in text else None
        return {"action": "open", "target": target}
        
    if any(word in text for word in ["organize", "sort", "clean", "arrange"]):
        return {"action": "organize"}
        
    if any(word in text for word in ["search", "find", "locate", "where"]):
        # Extract query roughly
        import re
        match = re.search(r'(search|find|locate|where is) (for )?(.*)', text)
        query = match.group(3).strip() if match else text
        return {"action": "search_semantic", "query": query}
        
    return {"action": "unknown"}
