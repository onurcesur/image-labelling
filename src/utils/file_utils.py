"""Utility functions for file operations."""
from pathlib import Path
from typing import List

SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


def is_image_file(file_path: Path) -> bool:
    """Check if a file is a supported image file."""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def get_image_files(directory: Path) -> List[Path]:
    """Get all image files from a directory."""
    if not directory.is_dir():
        return []
    
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        image_files.extend(directory.glob(f"*{ext}"))
        image_files.extend(directory.glob(f"*{ext.upper()}"))
    
    return sorted(image_files)


def get_unique_filename(directory: Path, base_name: str, extension: str) -> Path:
    """Generate a unique filename in a directory."""
    counter = 1
    file_path = directory / f"{base_name}{extension}"
    
    while file_path.exists():
        file_path = directory / f"{base_name}_{counter}{extension}"
        counter += 1
    
    return file_path
