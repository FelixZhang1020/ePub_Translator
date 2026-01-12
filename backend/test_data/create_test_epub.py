#!/usr/bin/env python3
"""Create a test EPUB file for storage testing."""

import zipfile
from pathlib import Path

# Paths
TEST_DATA_DIR = Path(__file__).parent
BOOK_DIR = TEST_DATA_DIR / "test_book"
OUTPUT_FILE = TEST_DATA_DIR / "test_storage.epub"

def create_epub():
    """Create EPUB file from test_book directory."""

    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()
        print(f"Removed existing: {OUTPUT_FILE}")

    with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as epub:
        # Add mimetype first (uncompressed as per EPUB spec)
        mimetype_file = BOOK_DIR / "mimetype"
        epub.write(mimetype_file, "mimetype", compress_type=zipfile.ZIP_STORED)
        print(f"Added: mimetype")

        # Add all other files
        for file_path in BOOK_DIR.rglob("*"):
            if file_path.is_file() and file_path.name != "mimetype":
                # Get relative path from BOOK_DIR
                arcname = str(file_path.relative_to(BOOK_DIR))
                epub.write(file_path, arcname)
                print(f"Added: {arcname}")

    print(f"\n✅ Created: {OUTPUT_FILE}")
    print(f"Size: {OUTPUT_FILE.stat().st_size} bytes")

if __name__ == "__main__":
    create_epub()
