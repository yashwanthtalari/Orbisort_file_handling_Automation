import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import threading
import os
from core.watcher import OrbisortWatcher
from utils.logger import get_logger


class OrbisortGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Orbisort")
        self.root.geometry("900x600")
        self.root.configure(bg="#121212")

        self.logger = get_logger()
        self.watcher = None
        self.watching = False

        # Colors
        self.bg = "#121212"
        self.card = "#1e1e1e"
        self.accent = "#4cc2ff"
        self.green = "#22c55e"
        self.red = "#ef4444"
        self.text = "#ffffff"
        self.subtext = "#a1a1aa"

        style = ttk.Style()
        style.theme_use("default")

        # MAIN CONTAINER
        self.container = tk.Frame(root, bg=self.bg)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # HEADER
        header = tk.Frame(self.container, bg=self.bg)
        header.pack(fill="x", pady=(0, 15))

        tk.Label(
            header,
            text="📁 Orbisort",
            fg=self.text,
            bg=self.bg,
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Smart File Automation",
            fg=self.subtext,
            bg=self.bg,
            font=("Segoe UI", 10),
        ).pack(anchor="w")

        # STATUS BAR
        self.status_frame = tk.Frame(self.container, bg=self.card)
        self.status_frame.pack(fill="x", pady=10)

        self.status_label = tk.Label(
            self.status_frame,
            text="● STOPPED",
            fg=self.red,
            bg=self.card,
            font=("Segoe UI", 10, "bold"),
        )
        self.status_label.pack(padx=10, pady=8, anchor="w")

        # FOLDER CARD
        folder_card = tk.Frame(self.container, bg=self.card)
        folder_card.pack(fill="x", pady=10)

        tk.Label(
            folder_card,
            text="Watch Folder",
            fg=self.text,
            bg=self.card,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        inner = tk.Frame(folder_card, bg=self.card)
        inner.pack(fill="x", padx=10, pady=(0, 10))

        self.folder_entry = tk.Entry(
            inner,
            bg="#2a2a2a",
            fg="white",
            insertbackground="white",
            relief="flat",
        )
        self.folder_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 10), ipady=6
        )

        tk.Button(
            inner,
            text="Browse",
            bg=self.accent,
            fg="black",
            relief="flat",
            command=self.select_folder,
        ).pack(side="right")

        # CONTROL BUTTONS
        control = tk.Frame(self.container, bg=self.bg)
        control.pack(pady=10)

        self.start_btn = tk.Button(
            control,
            text="Start",
            bg=self.green,
            fg="white",
            relief="flat",
            width=12,
            command=self.start_watching,
            state="disabled",
        )
        self.start_btn.pack(side="left", padx=10, ipady=6)

        self.stop_btn = tk.Button(
            control,
            text="Stop",
            bg=self.red,
            fg="white",
            relief="flat",
            width=12,
            command=self.stop_watching,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=10, ipady=6)

        # LOG CARD
        log_card = tk.Frame(self.container, bg=self.card)
        log_card.pack(fill="both", expand=True, pady=10)

        tk.Label(
            log_card,
            text="Activity",
            fg=self.text,
            bg=self.card,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(
            log_card,
            bg="#111111",
            fg="#d4d4d4",
            insertbackground="white",
            relief="flat",
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.setup_logging()

    # -------------------------

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.start_btn.config(state="normal")

    def start_watching(self):
        folder = self.folder_entry.get()

        if not os.path.exists(folder):
            self.log("Invalid folder")
            return

        self.watching = True

        self.status_label.config(text="● LIVE", fg=self.green)

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        self.watcher = OrbisortWatcher(folder, recursive=True)

        thread = threading.Thread(target=self.watcher.start)
        thread.daemon = True
        thread.start()

        self.log(f"Watching {folder}")

    def stop_watching(self):
        if self.watcher:
            self.watcher.stop()

        self.status_label.config(text="● STOPPED", fg=self.red)

        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        self.log("Stopped watching")

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def setup_logging(self):
        import logging

        class Handler(logging.Handler):
            def __init__(self, widget):
                super().__init__()
                self.widget = widget

            def emit(self, record):
                msg = self.format(record)
                self.widget.insert(tk.END, msg + "\n")
                self.widget.see(tk.END)

        handler = Handler(self.log_text)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)


if __name__ == "__main__":
    root = tk.Tk()
    app = OrbisortGUI(root)
    root.mainloop()
