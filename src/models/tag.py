"""Tag model for managing tag data."""
from dataclasses import dataclass, field
from typing import Optional
from PyQt6.QtGui import QColor


@dataclass
class Tag:
    """Represents a tag with name, color, and classification."""
    name: str
    color: QColor = field(default_factory=lambda: QColor(100, 100, 100))
    classification: str = "General"
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = f"{self.classification}_{self.name}"
    
    def to_dict(self) -> dict:
        """Convert tag to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color.name(),
            "classification": self.classification
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Tag':
        """Create a Tag from dictionary."""
        return cls(
            name=data["name"],
            color=QColor(data["color"]),
            classification=data["classification"],
            id=data.get("id")
        )
