import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
import os
from core.watcher import OrbisortWatcher
from utils.logger import get_logger


class OrbisortGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Orbisort - File Organizer")
        self.root.geometry("600x400")

        self.watcher = None
        self.watching = False
        self.logger = get_logger()

        # Folder selection
        self.folder_label = tk.Label(root, text="Watch Folder:")
        self.folder_label.pack(pady=5)

        self.folder_entry = tk.Entry(root, width=50)
        self.folder_entry.pack(pady=5)

        self.select_button = tk.Button(
            root, text="Select Folder", command=self.select_folder
        )
        self.select_button.pack(pady=5)

        # Control buttons
        self.start_button = tk.Button(
            root, text="Start Watching", command=self.start_watching, state=tk.DISABLED
        )
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(
            root, text="Stop Watching", command=self.stop_watching, state=tk.DISABLED
        )
        self.stop_button.pack(pady=5)

        # Status
        self.status_label = tk.Label(root, text="Status: Not watching")
        self.status_label.pack(pady=5)

        # Log display
        self.log_text = scrolledtext.ScrolledText(root, width=70, height=15)
        self.log_text.pack(pady=5)

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
