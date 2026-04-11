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
        BaseAgent.__init__(self, "GUI", subscriptions=["FILE_ORGANIZED", "ASSISTANT_STATUS", "AGENT_STATUS_UPDATE"])
        
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
        
        # Initial status report
        self.after(3000, self.request_initial_status)

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
                elif msg.msg_type == "AGENT_STATUS_UPDATE":
                    agent_name = msg.data['name']
                    is_active = msg.data['active']
                    if agent_name in self.status_indicators:
                        color = "#22c55e" if is_active else "#ef4444"
                        self.status_indicators[agent_name].configure(text_color=color)
        except queue.Empty:
            pass
        self.after(100, self.process_ui_events)

    def request_initial_status(self):
        # We can just publish a request or just wait for them to pulse
        # For now, let's just assume they are healthy since they are initialized
        pass

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#020617", border_width=1, border_color="#1e293b")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="ORBISORT", font=("Segoe UI", 26, "bold"), text_color="#38bdf8").pack(pady=(40, 5))
        ctk.CTkLabel(self.sidebar, text="Intelligent Hub", font=("Segoe UI", 10), text_color="#64748b").pack(pady=(0, 40))
        
        self.create_nav_btn("📊 Dashboard", selected=True)
        self.create_nav_btn("📜 History")
        self.create_nav_btn("🧠 AI Console")
        self.create_nav_btn("⚙️ Settings")
        
        # Agent Status Panel
        status_frame = ctk.CTkFrame(self.sidebar, fg_color="#0f172a", corner_radius=10, border_width=1, border_color="#1e293b")
        status_frame.pack(side="bottom", fill="x", padx=15, pady=20)
        
        ctk.CTkLabel(status_frame, text="AGENT STATUS", font=("Segoe UI", 10, "bold"), text_color="#38bdf8").pack(pady=(10, 5))
        
        self.status_indicators = {}
        for agent in ["Watcher", "Organizer", "Voice", "Locator"]:
            row = ctk.CTkFrame(status_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            lbl = ctk.CTkLabel(row, text=agent, font=("Segoe UI", 11), text_color="#94a3b8")
            lbl.pack(side="left")
            ind = ctk.CTkLabel(row, text="●", text_color="#22c55e", font=("Segoe UI", 14))
            ind.pack(side="right")
            self.status_indicators[agent] = ind

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
        
        text_frame = ctk.CTkFrame(header, fg_color="transparent")
        text_frame.pack(side="left")
        ctk.CTkLabel(text_frame, text="Welcome Back,", font=("Segoe UI", 14), text_color="#94a3b8").pack(anchor="w")
        ctk.CTkLabel(text_frame, text="Management Hub", font=("Segoe UI", 32, "bold"), text_color="white").pack(anchor="w")

        # Stats Dashboard
        stats_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)
        
        self.stats = {
            "Total Sorted": "0",
            "Duplicated": "0",
            "Indexed": "0"
        }
        
        for i, (title, val) in enumerate(self.stats.items()):
            card = ctk.CTkFrame(stats_frame, fg_color="#1e293b", corner_radius=15, border_width=1, border_color="#334155", width=180, height=100)
            card.pack(side="left", padx=(0, 20), fill="both", expand=True)
            card.pack_propagate(False)
            
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"), text_color="#94a3b8").pack(pady=(15, 0))
            lbl = ctk.CTkLabel(card, text=val, font=("Segoe UI", 24, "bold"), text_color="#38bdf8")
            lbl.pack()
            self.stats[title] = lbl

        # Watch Folder Configuration
        config = ctk.CTkFrame(self.main, fg_color="#1e293b", corner_radius=15, border_width=1, border_color="#334155")
        config.pack(fill="x", pady=20)
        
        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(fill="x", padx=25, pady=15)
        
        ctk.CTkLabel(inner, text="TRACKING PATH:", font=("Segoe UI", 12, "bold"), text_color="#94a3b8").pack(side="left")
        self.folder_label = ctk.CTkLabel(inner, text="No active target selected", text_color="#38bdf8", font=("Segoe UI", 12, "italic"))
        self.folder_label.pack(side="left", padx=15)
        
        self.start_btn = ctk.CTkButton(inner, text="Launch Automation", fg_color="#3b82f6", hover_color="#2563eb", 
                                       width=180, height=45, corner_radius=12, font=("Segoe UI", 13, "bold"), command=self.toggle_watch)
        self.start_btn.pack(side="right")
        
        self.scan_only_var = ctk.BooleanVar(value=False)
        self.scan_only_check = ctk.CTkCheckBox(inner, text="Scan Only (Discovery)", variable=self.scan_only_var, 
                                               font=("Segoe UI", 11), text_color="#94a3b8", checkbox_height=18, checkbox_width=18)
        self.scan_only_check.pack(side="right", padx=15)
        
        ctk.CTkButton(inner, text="Browse", width=80, height=45, fg_color="#334155", corner_radius=12, font=("Segoe UI", 12), command=self.select_folder).pack(side="right", padx=10)
        
        # Activity Feed
        activity_header = ctk.CTkFrame(self.main, fg_color="transparent")
        activity_header.pack(fill="x", pady=(10, 10))
        ctk.CTkLabel(activity_header, text="Recent Activity", font=("Segoe UI", 18, "bold")).pack(side="left")
        self.system_status = ctk.CTkLabel(activity_header, text="Watching for changes...", font=("Segoe UI", 11), text_color="#3b82f6")
        self.system_status.pack(side="right")
        
        self.scroll_frame = ctk.CTkScrollableFrame(self.main, fg_color="#020617", corner_radius=15, border_width=1, border_color="#1e293b")
        self.scroll_frame.pack(fill="both", expand=True)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_label.configure(text=folder, font=("Segoe UI", 12, "bold"))

    def toggle_watch(self):
        folder = self.folder_label.cget("text")
        if "No active target" in folder: return
        
        if self.start_btn.cget("text") == "Launch Automation":
            data = {
                "path": folder,
                "scan_only": self.scan_only_var.get()
            }
            coordinator.publish("GUI", "START_WATCHING", data)
            self.start_btn.configure(text="Pause Service", fg_color="#ef4444")
            status_text = "Discovery Active" if self.scan_only_var.get() else "Service Active"
            self.system_status.configure(text=status_text, text_color="#22c55e")
        else:
            coordinator.publish("GUI", "STOP_WATCHING", None)
            self.start_btn.configure(text="Launch Automation", fg_color="#3b82f6")
            self.system_status.configure(text="Service Paused", text_color="#f59e0b")

    def show_assistant(self):
        if not self.assistant_win:
            self.assistant_win = AssistantWindow(self)

    def add_activity(self, original, new):
        # Update Stats
        current = int(self.stats["Total Sorted"].cget("text"))
        self.stats["Total Sorted"].configure(text=str(current + 1))
        
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#111827", border_width=1, border_color="#1e293b", height=80)
        card.pack(fill="x", pady=8, padx=10)
        
        # File Info Frame
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", padx=20, fill="y", pady=15)
        
        name = os.path.basename(original)
        ctk.CTkLabel(info, text=name, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        
        # Get a pretty display path (last two segments of the directory)
        dest_dir = os.path.dirname(new)
        path_parts = dest_dir.replace("\\", "/").split("/")
        display_path = "/".join(path_parts[-2:]) if len(path_parts) >= 2 else dest_dir
        
        ctk.CTkLabel(info, text=f"Sorted into: {display_path}", font=("Segoe UI", 11), text_color="#38bdf8").pack(anchor="w")
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=20)
        
        ctk.CTkButton(btn_frame, text="View File", width=100, height=30, fg_color="#334155", 
                       command=lambda: coordinator.publish("GUI", "OPEN_FOLDER", new)).pack(side="right")

if __name__ == "__main__":
    app = OrbisortGUI()
    app.mainloop()
