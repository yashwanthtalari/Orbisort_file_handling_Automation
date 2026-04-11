import threading
import time
import os
from core.agents.base_agent import BaseAgent
from core.assistant.voice import listen, speak
from core.assistant.assistant import handle_command
from utils.logger import get_logger

logger = get_logger()

class VoiceAgent(BaseAgent):
    def __init__(self):
        super().__init__("VoiceAgent", subscriptions=["START_STT", "SPEAK", "FILE_ORGANIZED"])
        self.last_announce_time = 0

    def receive(self, message):
        if message.msg_type == "START_STT":
            threading.Thread(target=self.process_voice, daemon=True).start()
        elif message.msg_type == "SPEAK":
            speak(message.data)
        elif message.msg_type == "FILE_ORGANIZED":
            self.announce_organization(message.data)

    def announce_organization(self, data):
        """Spontaneously announce file organization, but not too frequently"""
        current_time = time.time()
        if current_time - self.last_announce_time > 10: # Max one alert every 10 seconds
            filename = os.path.basename(data['original'])
            # Don't speak path, just filename
            speak(f"I've just organized {filename}")
            self.last_announce_time = current_time

    def process_voice(self):
        self.send("ASSISTANT_STATUS", "Listening...")
        text = listen()
        if text and "error" not in text.lower() and "catch that" not in text.lower():
            self.send("ASSISTANT_STATUS", f"You said: {text}")
            response = handle_command(text)
            self.send("ASSISTANT_STATUS", response)
            
            # Friendly voice response
            if "📄" in response or "C:\\" in response:
                speak("I found your files! I've displayed them on the screen and I can open them if you'd like.")
            else:
                speak(response)
        else:
            self.send("ASSISTANT_STATUS", text)
            speak(text)
        
        time.sleep(4)
        self.send("ASSISTANT_STATUS", "Ready for your next command")
