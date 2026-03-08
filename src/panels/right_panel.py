"""Right panel for tag management."""
from typing import List, Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QComboBox, QColorDialog, QDialog, QFormLayout,
    QDialogButtonBox, QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from ..models.tag import Tag


class CreateTagDialog(QDialog):
    """Dialog for creating a new tag."""
    
    def __init__(self, classifications: List[str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Tag")
        self._classifications = classifications
        self._selected_color = QColor(100, 100, 100)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QFormLayout(self)
        
        # Tag name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter tag name")
        layout.addRow("Name:", self.name_input)
        
        # Classification selector
        self.classification_combo = QComboBox()
        self.classification_combo.addItems(self._classifications)
        self.classification_combo.setEditable(True)
        layout.addRow("Classification:", self.classification_combo)
        
        # Color picker
        color_layout = QHBoxLayout()
        
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet(
            f"background-color: {self._selected_color.name()}; border: 1px solid black;"
        )
        color_layout.addWidget(self.color_preview)
        
        self.choose_color_btn = QPushButton("Choose Color")
        self.choose_color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self.choose_color_btn)
        
        color_layout.addStretch()
        layout.addRow("Color:", color_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        self.setLayout(layout)
    
    def _choose_color(self) -> None:
        """Open color picker dialog."""
        color = QColorDialog.getColor(
            self._selected_color, 
            self, 
            "Select Tag Color"
        )
        if color.isValid():
            self._selected_color = color
            self.color_preview.setStyleSheet(
                f"background-color: {self._selected_color.name()}; "
                f"border: 1px solid black;"
            )
    
    def get_tag_data(self) -> Optional[dict]:
        """Get the entered tag data."""
        name = self.name_input.text().strip()
        if not name:
            return None
        
        return {
            "name": name,
            "color": self._selected_color,
            "classification": self.classification_combo.currentText()
        }


class ClassificationManager(QWidget):
    """Widget for managing classifications."""
    
    classification_added = pyqtSignal(str)
    classification_removed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Classifications")
        header.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(header)
        layout.addLayout(header_layout)
        
        # Add classification input
        add_layout = QHBoxLayout()
        self.classification_input = QLineEdit()
        self.classification_input.setPlaceholderText("New classification...")
        add_layout.addWidget(self.classification_input)
        
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedWidth(30)
        add_layout.addWidget(self.add_btn)
        
        layout.addLayout(add_layout)
        
        # Classification list
        self.classification_list = QListWidget()
        self.classification_list.setMaximumHeight(100)
        layout.addWidget(self.classification_list)
        
        # Remove button
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setEnabled(False)
        layout.addWidget(self.remove_btn)
        
        self.setLayout(layout)
    
    def _connect_signals(self) -> None:
        """Connect signals."""
        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.classification_input.returnPressed.connect(self._on_add)
        self.classification_list.itemSelectionChanged.connect(
            lambda: self.remove_btn.setEnabled(
                self.classification_list.currentItem() is not None
            )
        )
    
    def _on_add(self) -> None:
        """Add a new classification."""
        name = self.classification_input.text().strip()
        if name:
            self.add_classification(name)
            self.classification_added.emit(name)
            self.classification_input.clear()
    
    def _on_remove(self) -> None:
        """Remove selected classification."""
        item = self.classification_list.currentItem()
        if item:
            name = item.text()
            self.classification_list.takeItem(
                self.classification_list.row(item)
            )
            self.classification_removed.emit(name)
    
    def add_classification(self, name: str) -> None:
        """Add a classification to the list."""
        # Check if already exists
        for i in range(self.classification_list.count()):
            if self.classification_list.item(i).text() == name:
                return
        self.classification_list.addItem(name)
    
    def get_classifications(self) -> List[str]:
        """Get all classification names."""
        return [
            self.classification_list.item(i).text()
            for i in range(self.classification_list.count())
        ]


class TagListWidget(QWidget):
    """Widget for displaying and managing tags."""
    
    tag_selected = pyqtSignal(object)  # Emits Tag
    tag_deleted = pyqtSignal(object)   # Emits Tag
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tags: List[Tag] = []
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("Tags")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)
        
        # Tag list
        self.tag_list = QListWidget()
        layout.addWidget(self.tag_list)
        
        # Delete button
        self.delete_btn = QPushButton("Delete Selected Tag")
        self.delete_btn.setEnabled(False)
        layout.addWidget(self.delete_btn)
        
        self.setLayout(layout)
    
    def _connect_signals(self) -> None:
        """Connect signals."""
        self.tag_list.itemClicked.connect(self._on_item_clicked)
        self.delete_btn.clicked.connect(self._on_delete)
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle tag item click."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        if tag:
            self.tag_selected.emit(tag)
    
    def _on_delete(self) -> None:
        """Delete selected tag."""
        item = self.tag_list.currentItem()
        if item:
            tag = item.data(Qt.ItemDataRole.UserRole)
            if tag:
                self.remove_tag(tag)
                self.tag_deleted.emit(tag)
    
    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the list."""
        self._tags.append(tag)
        item = QListWidgetItem(tag.name)
        item.setData(Qt.ItemDataRole.UserRole, tag)
        
        # Set color indicator
        color = tag.color
        item.setBackground(color.lighter(150))
        item.setForeground(color.darker(200))
        
        self.tag_list.addItem(item)
    
    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from the list."""
        self._tags.remove(tag)
        for i in range(self.tag_list.count()):
            item = self.tag_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tag:
                self.tag_list.takeItem(i)
                break
    
    def get_tags(self) -> List[Tag]:
        """Get all tags."""
        return self._tags.copy()
    
    def clear_tags(self) -> None:
        """Clear all tags."""
        self._tags.clear()
        self.tag_list.clear()


class TagManagerPanel(QWidget):
    """Right panel for managing tags and classifications."""
    
    # Signals
    tags_changed = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tags: List[Tag] = []
        self._classifications: List[str] = ["General"]
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Tag Manager")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Create tag button
        self.create_tag_btn = QPushButton("Create New Tag")
        self.create_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3a8eef;
            }
        """)
        layout.addWidget(self.create_tag_btn)
        
        # Classification manager
        self.classification_manager = ClassificationManager()
        self.classification_manager.add_classification("General")
        layout.addWidget(self.classification_manager)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Tag list
        self.tag_list_widget = TagListWidget()
        layout.addWidget(self.tag_list_widget, 1)
        
        # Stats label
        self.stats_label = QLabel("Tags: 0")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(200)
    
    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self.create_tag_btn.clicked.connect(self._on_create_tag)
        self.classification_manager.classification_added.connect(
            self._on_classification_added
        )
        self.classification_manager.classification_removed.connect(
            self._on_classification_removed
        )
        self.tag_list_widget.tag_deleted.connect(self._on_tag_deleted)
    
    def _on_create_tag(self) -> None:
        """Open dialog to create a new tag."""
        classifications = self.classification_manager.get_classifications()
        dialog = CreateTagDialog(classifications, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_tag_data()
            if data:
                tag = Tag(
                    name=data["name"],
                    color=data["color"],
                    classification=data["classification"]
                )
                self._tags.append(tag)
                self.tag_list_widget.add_tag(tag)
                self._update_stats()
                self.tags_changed.emit()
    
    def _on_classification_added(self, name: str) -> None:
        """Handle classification addition."""
        if name not in self._classifications:
            self._classifications.append(name)
    
    def _on_classification_removed(self, name: str) -> None:
        """Handle classification removal."""
        if name in self._classifications and name != "General":
            self._classifications.remove(name)
    
    def _on_tag_deleted(self, tag: Tag) -> None:
        """Handle tag deletion."""
        if tag in self._tags:
            self._tags.remove(tag)
            self._update_stats()
            self.tags_changed.emit()
    
    def _update_stats(self) -> None:
        """Update the stats label."""
        self.stats_label.setText(f"Tags: {len(self._tags)}")
    
    def get_tags(self) -> List[Tag]:
        """Get all available tags."""
        return self._tags.copy()
    
    def get_classifications(self) -> List[str]:
        """Get all classifications."""
        return self._classifications.copy()
    
    def add_default_tags(self) -> None:
        """Add some default tags for demonstration."""
        default_tags = [
            Tag("Important", QColor(255, 100, 100), "Priority"),
            Tag("Review", QColor(255, 200, 100), "Status"),
            Tag("Approved", QColor(100, 255, 100), "Status"),
            Tag("Landscape", QColor(100, 200, 255), "Category"),
            Tag("Portrait", QColor(200, 100, 255), "Category"),
        ]
        
        for tag in default_tags:
            self._tags.append(tag)
            self.tag_list_widget.add_tag(tag)
        
        # Add classifications
        for tag in default_tags:
            self.classification_manager.add_classification(tag.classification)
        
        self._update_stats()
