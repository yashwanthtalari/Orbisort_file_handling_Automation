import speech_recognition as sr
import pyttsx3
import threading
import sounddevice as sd
import numpy as np
import io
from scipy.io.wavfile import write

def speak(text):
    """Voice feedback"""
    def _speak():
        try:
            engine = pyttsx3.init()
            # Set voice properties for a more 'premium' feel
            voices = engine.getProperty('voices')
            if len(voices) > 1:
                engine.setProperty('voice', voices[1].id) # Often a more natural voice
            engine.setProperty('rate', 170)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass
    
    threading.Thread(target=_speak, daemon=True).start()

def listen():
    """Microphone listener using sounddevice to avoid PyAudio dependency"""
    recognizer = sr.Recognizer()
    fs = 44100  # Sample rate
    seconds = 5  # Duration of recording
    
    try:
        print("Recording...")
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is finished
        
        # Save to buffer
        buffer = io.BytesIO()
        write(buffer, fs, recording)
        buffer.seek(0)
        
        with sr.AudioFile(buffer) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
            
    except Exception as e:
        print(f"Voice capture error: {e}")
        return "Voice device not ready"
