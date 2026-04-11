import customtkinter as ctk
from core.agents.coordinator import coordinator

class AssistantWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Premium Styling
        self.title("Orbisort Assistant")
        self.geometry("300x150")
        self.overrideredirect(True) # Borderless for premium feel
        self.attributes("-topmost", True)
        self.configure(fg_color="#0f172a")
        
        # Position Lower Right
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{sw - 320}+{sh - 200}")
        
        # Main Frame with Glow Effect
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, border_width=2, border_color="#38bdf8")
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.header = ctk.CTkLabel(self.main_frame, text="AI Assistant LIVE", font=("Segoe UI", 10, "bold"), text_color="#38bdf8")
        self.header.pack(pady=(10, 0))
        
        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready", font=("Segoe UI", 14, "bold"), wraplength=250)
        self.status_label.pack(expand=True, pady=10)
        
        self.mic_btn = ctk.CTkButton(self.main_frame, text="🎤 Speak Now", height=35, corner_radius=20, font=("Segoe UI", 12, "bold"), 
                                    fg_color="#3b82f6", hover_color="#2563eb", command=self.activate_voice)
        self.mic_btn.pack(pady=(0, 15), padx=20)
        
        # Dragging functionality (since no title bar)
        self.main_frame.bind("<B1-Motion>", self.on_drag)
        self.header.bind("<B1-Motion>", self.on_drag)

    def on_drag(self, event):
        x = self.winfo_x() + event.x - 150
        y = self.winfo_y() + event.y - 10
        self.geometry(f"+{x}+{y}")

    def activate_voice(self):
        coordinator.publish("AssistantWindow", "START_STT", None)

    def set_status(self, text):
        self.status_label.configure(text=text)
        if "Listening" in text:
            self.main_frame.configure(border_color="#f59e0b")
            self.status_label.configure(text_color="#f59e0b")
        elif "You said" in text:
            self.main_frame.configure(border_color="#22c55e")
            self.status_label.configure(text_color="#22c55e")
        elif "Organized" in text or "Search" in text:
            self.main_frame.configure(border_color="#38bdf8")
            self.status_label.configure(text_color="#38bdf8")
        else:
            self.main_frame.configure(border_color="#38bdf8")
            self.status_label.configure(text_color="white")
