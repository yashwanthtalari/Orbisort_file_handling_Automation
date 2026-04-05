import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
import os
from core.watcher import OrbisortWatcher
from utils.logger import get_logger


class OrbisortGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Orbisort")
        self.root.geometry("1000x650")
        self.root.configure(bg="#0f172a")

        self.logger = get_logger()
        self.watcher = None
        self.search_var = tk.StringVar()
        self.full_log_content = ""  # Store complete log for filtering

        # Colors (React-like dark theme)
        self.bg = "#0f172a"
        self.sidebar = "#020617"
        self.card = "#111827"
        self.accent = "#38bdf8"
        self.green = "#22c55e"
        self.red = "#ef4444"
        self.text = "#e5e7eb"
        self.muted = "#9ca3af"

        # LAYOUT
        self.main_frame = tk.Frame(root, bg=self.bg)
        self.main_frame.pack(fill="both", expand=True)

        self.build_sidebar()
        self.build_content()

    # ---------------- SIDEBAR ----------------
    def build_sidebar(self):
        self.sidebar_frame = tk.Frame(self.main_frame, bg=self.sidebar, width=200)
        self.sidebar_frame.pack(side="left", fill="y")

        tk.Label(
            self.sidebar_frame,
            text="Orbisort",
            bg=self.sidebar,
            fg=self.accent,
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=20)

        self.create_sidebar_btn("Dashboard")
        self.create_sidebar_btn("Logs")
        self.create_sidebar_btn("Settings")

    def create_sidebar_btn(self, text):
        tk.Button(
            self.sidebar_frame,
            text=text,
            bg=self.sidebar,
            fg=self.text,
            relief="flat",
            anchor="w",
            padx=20,
            pady=10,
        ).pack(fill="x")

    # ---------------- CONTENT ----------------
    def build_content(self):
        self.content = tk.Frame(self.main_frame, bg=self.bg)
        self.content.pack(fill="both", expand=True)

        self.build_topbar()
        self.build_dashboard()

    # ---------------- TOPBAR ----------------
    def build_topbar(self):
        topbar = tk.Frame(self.content, bg=self.bg)
        topbar.pack(fill="x", pady=10, padx=20)

        self.status = tk.Label(
            topbar,
            text="● Stopped",
            fg=self.red,
            bg=self.bg,
            font=("Segoe UI", 10, "bold"),
        )
        self.status.pack(side="left")

        # Search bar
        search_frame = tk.Frame(topbar, bg=self.bg)
        search_frame.pack(side="left", padx=20)

        tk.Label(search_frame, text="🔍", bg=self.bg, fg=self.muted).pack(side="left")
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg="#1f2933",
            fg="#9ca3af",
            relief="flat",
            font=("Segoe UI", 9),
            width=25,
        )
        self.search_entry.pack(side="left", ipady=4, padx=(5, 0))
        self.search_entry.insert(0, "Search logs...")
        self.search_entry.bind("<FocusIn>", self.on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self.on_search_focus_out)
        self.search_var.trace("w", self.filter_logs)
        tk.Button(
            topbar,
            text="Start",
            bg=self.green,
            fg="white",
            relief="flat",
            command=self.start_watching,
        ).pack(side="right", padx=5)

        tk.Button(
            topbar,
            text="Stop",
            bg=self.red,
            fg="white",
            relief="flat",
            command=self.stop_watching,
        ).pack(side="right")

    # ---------------- DASHBOARD ----------------
    def build_dashboard(self):
        dash = tk.Frame(self.content, bg=self.bg)
        dash.pack(fill="both", expand=True, padx=20)

        # Stats cards
        stats_frame = tk.Frame(dash, bg=self.bg)
        stats_frame.pack(fill="x", pady=(0, 20))

        self.build_stat_card(
            stats_frame, "Files Organized", get_file_count(), "#38bdf8"
        )
        self.build_stat_card(stats_frame, "Active Rules", 5, "#22c55e")  # Placeholder
        self.build_stat_card(stats_frame, "Watch Folders", 1, "#f59e0b")

        # Folder card
        folder_card = self.card_frame(dash)
        folder_card.pack(fill="x", pady=10)

        tk.Label(
            folder_card,
            text="Watch Folder",
            bg=self.card,
            fg=self.text,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=10, pady=5)

        row = tk.Frame(folder_card, bg=self.card)
        row.pack(fill="x", padx=10, pady=10)

        self.folder_entry = tk.Entry(row, bg="#1f2933", fg="white", relief="flat")
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=6)

        tk.Button(
            row,
            text="Browse",
            bg=self.accent,
            fg="black",
            relief="flat",
            command=self.select_folder,
        ).pack(side="right", padx=10)

        # Logs card
        log_card = self.card_frame(dash)
        log_card.pack(fill="both", expand=True, pady=10)

        tk.Label(
            log_card,
            text="Activity Logs",
            bg=self.card,
            fg=self.text,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(
            log_card,
            bg="#020617",
            fg="#d1d5db",
            relief="flat",
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.setup_logging()

    # ---------------- HELPERS ----------------
    def card_frame(self, parent):
        return tk.Frame(parent, bg=self.card, bd=0)

    def build_stat_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg=self.card, relief="flat", bd=1)
        card.pack(side="left", fill="x", expand=True, padx=5)

        tk.Label(
            card, text=title, bg=self.card, fg=self.muted, font=("Segoe UI", 9)
        ).pack(pady=(10, 5))
        tk.Label(
            card, text=str(value), bg=self.card, fg=color, font=("Segoe UI", 18, "bold")
        ).pack(pady=(0, 10))

    def on_search_focus_in(self, event):
        if self.search_entry.get() == "Search logs...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="white")

    def on_search_focus_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search logs...")
            self.search_entry.config(fg="#9ca3af")
            self.filter_logs()

    def filter_logs(self, *args):
        search_term = self.search_var.get().strip().lower()
        if not search_term or search_term == "search logs...":
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, self.full_log_content)
            self.log_text.see(tk.END)
            return

        lines = self.full_log_content.split("\n")
        filtered_lines = [line for line in lines if search_term in line.lower()]

        self.log_text.delete(1.0, tk.END)
        if filtered_lines:
            self.log_text.insert(tk.END, "\n".join(filtered_lines) + "\n")
        else:
            self.log_text.insert(tk.END, f"No logs found containing: '{search_term}'\n")
        self.log_text.see(tk.END)

    # ---------------- LOGIC ----------------
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

    def start_watching(self):
        folder = self.folder_entry.get()

        if not os.path.exists(folder):
            self.log("Invalid folder")
            return

        self.status.config(text="● LIVE", fg=self.green)

        self.watcher = OrbisortWatcher(folder, recursive=True)

        thread = threading.Thread(target=self.watcher.start)
        thread.daemon = True
        thread.start()

        self.log(f"Watching {folder}")

    def stop_watching(self):
        if self.watcher:
            self.watcher.stop()

        self.status.config(text="● STOPPED", fg=self.red)
        self.log("Stopped")

    def log(self, msg):
        self.full_log_content += msg + "\n"
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

        search_term = self.search_var.get().strip().lower()
        if search_term and search_term != "search logs...":
            self.filter_logs()

    def setup_logging(self):
        import logging


def get_file_count():
    try:
        import sqlite3

        conn = sqlite3.connect("orbisort.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM files")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


if __name__ == "__main__":
    root = tk.Tk()
    app = OrbisortGUI(root)
    root.mainloop()
