import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import threading
import os
from core.watcher import OrbisortWatcher
from utils.logger import get_logger


class OrbisortGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Orbisort - File Organizer")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e1e")

        # Dark theme colors
        self.bg_color = "#1e1e1e"
        self.surface_color = "#2d2d2d"
        self.accent_color = "#007acc"
        self.text_color = "#ffffff"
        self.secondary_text = "#cccccc"
        self.border_color = "#404040"

        # Set style for dark theme
        style = ttk.Style()

        # Configure ttk styles for dark theme
        style.configure("TFrame", background=self.bg_color)
        style.configure(
            "Card.TFrame", background=self.surface_color, relief="raised", borderwidth=1
        )
        style.configure(
            "TLabel",
            background=self.bg_color,
            foreground=self.text_color,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=self.accent_color
        )
        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 12, "bold"),
            foreground=self.secondary_text,
        )
        style.configure(
            "Status.TLabel", font=("Segoe UI", 10), foreground=self.secondary_text
        )
        style.configure(
            "TButton", font=("Segoe UI", 10, "bold"), padding=8, relief="flat"
        )
        style.map(
            "TButton",
            background=[("active", self.accent_color), ("!active", self.surface_color)],
            foreground=[("active", self.text_color), ("!active", self.text_color)],
        )
        style.configure(
            "TEntry",
            font=("Segoe UI", 10),
            fieldbackground=self.surface_color,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelframe",
            background=self.bg_color,
            foreground=self.text_color,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=self.bg_color,
            foreground=self.accent_color,
            font=("Segoe UI", 11, "bold"),
        )

        self.watcher = None
        self.watching = False
        self.logger = get_logger()

        # Main container
        main_container = ttk.Frame(root, style="TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header section
        header_frame = ttk.Frame(main_container, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(header_frame, text="📁 Orbisort", style="Title.TLabel")
        title_label.pack(pady=15)

        subtitle_label = ttk.Label(
            header_frame,
            text="Intelligent File Organization System",
            style="Subtitle.TLabel",
        )
        subtitle_label.pack(pady=(0, 15))

        # Separator
        ttk.Separator(main_container, orient="horizontal").pack(fill=tk.X, pady=(0, 20))

        # Folder selection card
        folder_card = ttk.LabelFrame(
            main_container, text="📂 Folder Selection", style="TLabelframe", padding=15
        )
        folder_card.pack(fill=tk.X, pady=(0, 20))

        folder_inner = ttk.Frame(folder_card, style="TFrame")
        folder_inner.pack(fill=tk.X)

        self.folder_label = ttk.Label(folder_inner, text="Watch Directory:")
        self.folder_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.folder_entry = ttk.Entry(folder_inner, width=50)
        self.folder_entry.grid(row=0, column=1, padx=(10, 5), pady=5, sticky=tk.EW)

        self.select_button = ttk.Button(
            folder_inner, text="Browse", command=self.select_folder
        )
        self.select_button.grid(row=0, column=2, padx=(0, 5), pady=5)

        folder_inner.columnconfigure(1, weight=1)

        # Controls card
        control_card = ttk.LabelFrame(
            main_container, text="🎮 Controls", style="TLabelframe", padding=15
        )
        control_card.pack(fill=tk.X, pady=(0, 20))

        button_frame = ttk.Frame(control_card, style="TFrame")
        button_frame.pack()

        self.start_button = ttk.Button(
            button_frame,
            text="▶️ Start Watching",
            command=self.start_watching,
            state=tk.DISABLED,
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))

        self.stop_button = ttk.Button(
            button_frame,
            text="⏹️ Stop Watching",
            command=self.stop_watching,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT)

        # Status card
        status_card = ttk.Frame(main_container, style="Card.TFrame")
        status_card.pack(fill=tk.X, pady=(0, 20))

        status_inner = ttk.Frame(status_card, style="TFrame")
        status_inner.pack(pady=10, padx=15, fill=tk.X)

        status_icon = ttk.Label(status_inner, text="📊", font=("Segoe UI", 14))
        status_icon.pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = ttk.Label(
            status_inner, text="Status: Not watching", style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT)

        # Activity log card
        log_card = ttk.LabelFrame(
            main_container, text="📋 Activity Log", style="TLabelframe", padding=15
        )
        log_card.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_card,
            width=70,
            height=15,
            font=("Consolas", 9),
            bg=self.surface_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.accent_color,
            selectforeground=self.text_color,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Redirect logger to GUI
        self.setup_logging()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.start_button.config(state=tk.NORMAL)

    def start_watching(self):
        folder = self.folder_entry.get()
        if not folder or not os.path.exists(folder):
            self.log("Invalid folder selected")
            return

        self.watching = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Watching")

        self.watcher = OrbisortWatcher(folder, recursive=True)
        self.watcher_thread = threading.Thread(target=self.watcher.start)
        self.watcher_thread.daemon = True
        self.watcher_thread.start()

        self.log(f"Started watching {folder}")

    def stop_watching(self):
        if self.watcher:
            self.watcher.stop()
            self.watching = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Status: Not watching")
            self.log("Stopped watching")

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def setup_logging(self):
        # This is a simple way; in a real app, use logging handlers
        import logging

        class GUITextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                self.text_widget.insert(tk.END, msg + "\n")
                self.text_widget.see(tk.END)

        handler = GUITextHandler(self.log_text)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)


if __name__ == "__main__":
    root = tk.Tk()
    app = OrbisortGUI(root)
    root.mainloop()
