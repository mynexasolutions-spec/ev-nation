import os
import sqlite3
import subprocess
import sys
from pathlib import Path

# Ensure Pillow is installed
try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed. Installing it now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

# Configuration
MEDIA_DIR = Path("media/products")
DB_PATH = "data/ev_nation.db"
QUALITY = 80
MAX_WIDTH = 1200
MAX_HEIGHT = 1200

def compress_and_convert_images():
    if not MEDIA_DIR.exists():
        print(f"Error: {MEDIA_DIR} directory not found.")
        return

    if not Path(DB_PATH).exists():
        print(f"Error: Database {DB_PATH} not found.")
        return

    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_freed_kb = 0
    files_processed = 0

    print("Starting image compression and conversion to WebP...")

    # Iterate through all files in the media/products directory recursively
    for filepath in MEDIA_DIR.rglob("*"):
        if filepath.is_file() and filepath.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            old_path_str = str(filepath)
            
            # The database path usually looks like /media/products/X/filename.png
            # We construct the db string to replace:
            db_path = "/" + str(filepath.as_posix())
            new_db_path = db_path.rsplit('.', 1)[0] + '.webp'

            new_filepath = filepath.with_suffix('.webp')
            
            try:
                # Open, resize and save the image as WebP
                with Image.open(filepath) as img:
                    # Convert RGBA to RGB for JPEG-like WebP compression if needed, 
                    # but WebP supports alpha, so we keep it.
                    
                    # Resize if too large
                    img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)
                    
                    # Save as WebP
                    img.save(new_filepath, "WEBP", quality=QUALITY, method=4)
                
                # Calculate size difference
                old_size = os.path.getsize(filepath)
                new_size = os.path.getsize(new_filepath)
                saved_kb = (old_size - new_size) / 1024
                total_freed_kb += saved_kb
                
                # Delete the old image
                os.remove(filepath)
                
                # Update the database tables
                cursor.execute(
                    "UPDATE product_images SET image_path = ? WHERE image_path = ?",
                    (new_db_path, db_path)
                )
                cursor.execute(
                    "UPDATE variants SET image_path = ? WHERE image_path = ?",
                    (new_db_path, db_path)
                )
                
                print(f"Converted {filepath.name} -> {new_filepath.name} (Saved: {saved_kb:.1f} KB)")
                files_processed += 1

            except Exception as e:
                print(f"Failed to process {filepath}: {e}")

    # Commit database changes and close
    conn.commit()
    conn.close()

    print("\n--- Compression Summary ---")
    print(f"Total files processed: {files_processed}")
    print(f"Total space saved: {total_freed_kb / 1024:.2f} MB")
    print("---------------------------")
    print("Done! You can now run deploy.sh to sync the updated images and database to the server.")

if __name__ == "__main__":
    compress_and_convert_images()
