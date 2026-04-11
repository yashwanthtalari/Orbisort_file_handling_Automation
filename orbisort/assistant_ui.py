import customtkinter as ctk
from core.assistant.assistant import handle_command
from core.assistant.voice import listen, speak

class AssistantUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Orbisort AI Assistant")
        self.root.geometry("400x300")
        
        # Appearance
        ctk.set_appearance_mode("dark")
        
        self.main_frame = ctk.CTkFrame(root, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.label = ctk.CTkLabel(self.main_frame, text="How can I help you today?", font=("Segoe UI", 16, "bold"))
        self.label.pack(pady=(20, 10))
        
        self.input = ctk.CTkEntry(self.main_frame, placeholder_text="Type a command...", width=300, height=40)
        self.input.pack(pady=10)
        self.input.bind("<Return>", lambda e: self.process())
        
        self.output = ctk.CTkLabel(self.main_frame, text="", wraplength=350, text_color="#38bdf8")
        self.output.pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        self.ask_btn = ctk.CTkButton(btn_frame, text="Execute", command=self.process, width=100, fg_color="#3b82f6", hover_color="#2563eb")
        self.ask_btn.pack(side="left", padx=10)
        
        self.voice_btn = ctk.CTkButton(btn_frame, text="🎤 Speak", command=self.voice_input, width=100, fg_color="#10b981", hover_color="#059669")
        self.voice_btn.pack(side="left", padx=10)

    def process(self):
        text = self.input.get()
        if not text: return
        
        self.output.configure(text="Processing...")
        result = handle_command(text)
        self.output.configure(text=str(result))
        speak(str(result))

    def voice_input(self):
        self.output.configure(text="Listening...", text_color="#f59e0b")
        self.root.update()
        
        text = listen()
        if text and text not in ["Sorry, I didn’t catch that", "Speech service error"]:
            self.input.delete(0, 'end')
            self.input.insert(0, text)
            self.process()
        else:
            self.output.configure(text=text, text_color="#ef4444")
            speak(text)

if __name__ == "__main__":
    root = ctk.CTk()
    app = AssistantUI(root)
    root.mainloop()
