import os
import shutil
from datetime import datetime


def move_file(src, dest_folder):

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    filename = os.path.basename(src)
    dest_path = os.path.join(dest_folder, filename)

    # Replace existing file
    if os.path.exists(dest_path):
        os.remove(dest_path)

    shutil.move(src, dest_path)

    return dest_path


def get_file_metadata(filepath):

    stats = os.stat(filepath)

    return {
        "size": stats.st_size,
        "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
    }
