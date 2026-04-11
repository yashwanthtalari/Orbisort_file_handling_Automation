import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import queue

# Agents
from core.agents.coordinator import coordinator
from core.agents.watcher_agent import WatcherAgent
from core.agents.organizer_agent import OrganizerAgent
from core.agents.voice_agent import VoiceAgent
from core.agents.locator_agent import LocatorAgent
from core.agents.assistant_window import AssistantWindow
from core.agents.base_agent import BaseAgent

from database.db_manager import initialize_db

ctk.set_appearance_mode("dark")

class OrbisortGUI(ctk.CTk, BaseAgent):
    def __init__(self):
        ctk.CTk.__init__(self)
        BaseAgent.__init__(self, "GUI", subscriptions=["FILE_ORGANIZED", "ASSISTANT_STATUS"])
        
        self.title("Orbisort Premium | Multi-Agent Edition")
        self.geometry("1100x750")
        
        initialize_db()
        self.ui_queue = queue.Queue()
        
        # Initialize Agents
        self.watcher = WatcherAgent()
        self.organizer = OrganizerAgent()
        self.voice = VoiceAgent()
        self.locator = LocatorAgent()
        
        # Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.build_sidebar()
        self.build_main()
        
        # Floating Assistant
        self.assistant_win = None
        self.after(2000, self.show_assistant)
        
        # Listener for UI thread updates
        self.process_ui_events()

    def receive(self, msg):
        self.ui_queue.put(msg)

    def process_ui_events(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg.msg_type == "FILE_ORGANIZED":
                    self.add_activity(msg.data['original'], msg.data['new'])
                elif msg.msg_type == "ASSISTANT_STATUS" and self.assistant_win:
                    self.assistant_win.set_status(msg.data)
        except queue.Empty:
            pass
        self.after(500, self.process_ui_events)

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#020617")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="ORBISORT", font=("Segoe UI", 26, "bold"), text_color="#38bdf8").pack(pady=40)
        
        self.create_nav_btn("📊 Dashboard", selected=True)
        self.create_nav_btn("📜 History")
        self.create_nav_btn("⚙️ Settings")
        
        ctk.CTkLabel(self.sidebar, text="PRO VERSION", font=("Segoe UI", 10), text_color="#475569").pack(side="bottom", pady=20)

    def create_nav_btn(self, text, selected=False):
        color = "#1e293b" if selected else "transparent"
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color=color, anchor="w", height=45, corner_radius=10, 
                             font=("Segoe UI", 13), hover_color="#334155")
        btn.pack(fill="x", padx=15, pady=5)

    def build_main(self):
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=40, pady=30)
        
        # Welcome Section
        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Welcome Back,", font=("Segoe UI", 14), text_color="#94a3b8").pack(anchor="w")
        ctk.CTkLabel(header, text="Management Hub", font=("Segoe UI", 28, "bold")).pack(anchor="w")

        # Watch Folder Configuration
        config = ctk.CTkFrame(self.main, fg_color="#1e293b", corner_radius=15, border_width=1, border_color="#334155")
        config.pack(fill="x", pady=10)
        
        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(fill="x", padx=25, pady=15)
        
        ctk.CTkLabel(inner, text="Target Monitor:", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.folder_label = ctk.CTkLabel(inner, text="No folder selected", text_color="#38bdf8", font=("Segoe UI", 12))
        self.folder_label.pack(side="left", padx=15)
        
        self.start_btn = ctk.CTkButton(inner, text="Start Automating", fg_color="#3b82f6", hover_color="#2563eb", 
                                       width=160, height=40, corner_radius=20, font=("Segoe UI", 12, "bold"), command=self.toggle_watch)
        self.start_btn.pack(side="right")
        
        ctk.CTkButton(inner, text="Browse", width=80, fg_color="#334155", font=("Segoe UI", 12), command=self.select_folder).pack(side="right", padx=10)
        
        # Activity Feed
        activity_header = ctk.CTkFrame(self.main, fg_color="transparent")
        activity_header.pack(fill="x", pady=(30, 10))
        ctk.CTkLabel(activity_header, text="Live Activity Feed", font=("Segoe UI", 18, "bold")).pack(side="left")
        ctk.CTkLabel(activity_header, text="System is currently observing...", font=("Segoe UI", 11), text_color="#475569").pack(side="right")
        
        self.scroll_frame = ctk.CTkScrollableFrame(self.main, fg_color="#020617", corner_radius=15)
        self.scroll_frame.pack(fill="both", expand=True)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_label.configure(text=folder)

    def toggle_watch(self):
        folder = self.folder_label.cget("text")
        if folder == "No folder selected": return
        
        if self.start_btn.cget("text") == "Start Automating":
            coordinator.publish("GUI", "START_WATCHING", folder)
            self.start_btn.configure(text="Stop Live Feed", fg_color="#ef4444")
        else:
            coordinator.publish("GUI", "STOP_WATCHING", None)
            self.start_btn.configure(text="Start Automating", fg_color="#3b82f6")

    def show_assistant(self):
        if not self.assistant_win:
            self.assistant_win = AssistantWindow(self)

    def add_activity(self, original, new):
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#111827", border_width=1, border_color="#1f2937", height=80)
        card.pack(fill="x", pady=8, padx=10)
        
        # File Info Frame
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", padx=20, fill="y", pady=15)
        
        name = os.path.basename(original)
        ctk.CTkLabel(info, text=name, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        
        rel_dest = os.path.dirname(new).split("Organized")[-1]
        ctk.CTkLabel(info, text=f"Sorted into: Organized{rel_dest}", font=("Segoe UI", 11), text_color="#38bdf8").pack(anchor="w")
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=20)
        
        ctk.CTkButton(btn_frame, text="View File", width=100, height=30, fg_color="#334155", 
                       command=lambda: coordinator.publish("GUI", "OPEN_FOLDER", new)).pack(side="right")

if __name__ == "__main__":
    app = OrbisortGUI()
    app.mainloop()
