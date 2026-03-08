"""Image item model for managing image data and associated tags."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt, QPointF
from .tag import Tag


@dataclass
class ImageItem:
    """Represents an image with its file path and associated tags."""
    file_path: Path
    tags: List[Tag] = field(default_factory=list)
    masks: Dict[str, QImage] = field(default_factory=dict)
    polygons: Dict[str, List[List[QPointF]]] = field(default_factory=dict)
    keypoints: Dict[str, List[Tuple[QPointF, str]]] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        if not isinstance(self.file_path, Path):
            self.file_path = Path(self.file_path)
    
    @property
    def filename(self) -> str:
        """Return the filename without path."""
        return self.file_path.name
    
    @property
    def is_valid_image(self) -> bool:
        """Check if the file is a valid image (PNG or JPG)."""
        valid_extensions = {'.png', '.jpg', '.jpeg'}
        return self.file_path.suffix.lower() in valid_extensions
    
    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the image if not already present."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from the image."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: Tag) -> bool:
        """Check if the image has a specific tag."""
        return tag in self.tags
    
    def to_dict(self) -> dict:
        """Convert image item to dictionary for serialization."""
        return {
            "file_path": str(self.file_path),
            "tags": [tag.to_dict() for tag in self.tags],
            "masks": list(self.masks.keys()),
            "polygons": {
                tag_id: [
                    [{"x": point.x(), "y": point.y()} for point in polygon]
                    for polygon in polygons
                ]
                for tag_id, polygons in self.polygons.items()
            },
            "keypoints": {
                tag_id: [
                    {"x": kp[0].x(), "y": kp[0].y(), "name": kp[1]}
                    for kp in keypoints
                ]
                for tag_id, keypoints in self.keypoints.items()
            }
        }
    
    def ensure_mask(self, tag: Tag, size: Optional[tuple[int, int]] = None) -> QImage:
        """Ensure a mask exists for the given tag."""
        if tag.id not in self.masks:
            width, height = size if size else (1, 1)
            mask = QImage(width, height, QImage.Format.Format_ARGB32)
            mask.fill(Qt.GlobalColor.transparent)
            self.masks[tag.id] = mask
        return self.masks[tag.id]
