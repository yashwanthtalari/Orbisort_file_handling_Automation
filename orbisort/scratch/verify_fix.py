import time
import os
from core.watcher import start_watcher

def run_test():
    test_folder = os.path.join(os.getcwd(), "test_run_folder")
    print(f"Starting watcher on {test_folder}...")
    
    # Start watcher
    watcher = start_watcher(test_folder)
    
    # Wait for processing
    print("Waiting for files to be organized...")
    time.sleep(10)
    
    # Stop watcher
    watcher.stop()
    print("Test complete.")

if __name__ == "__main__":
    run_test()
