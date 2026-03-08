"""Main application window."""
from typing import List, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QStatusBar, QMenuBar, QMenu, QToolBar, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

from .panels.left_panel import FileBrowserPanel
from .panels.middle_panel import ImageViewerPanel
from .panels.right_panel import TagManagerPanel
from .models.image_item import ImageItem
from .models.tag import Tag


class ImageTaggingApp(QMainWindow):
    """Main application window for the image tagging application."""
    
    def __init__(self):
        super().__init__()
        self._image_items: List[ImageItem] = []
        self._current_image_index: int = -1
        
        self._setup_ui()
        self._setup_menus()
        self._connect_signals()
        self._load_defaults()
    
    def _setup_ui(self) -> None:
        """Set up the main user interface."""
        self.setWindowTitle("Image Tagger")
        self.setMinimumSize(1200, 800)
        
        # Create central widget with splitter
        central_widget = QWidget()
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - File Browser
        self.left_panel = FileBrowserPanel()
        splitter.addWidget(self.left_panel)
        
        # Middle panel - Image Viewer
        self.middle_panel = ImageViewerPanel()
        splitter.addWidget(self.middle_panel)
        
        # Right panel - Tag Manager
        self.right_panel = TagManagerPanel()
        splitter.addWidget(self.right_panel)
        
        # Set initial sizes (left: 20%, middle: 55%, right: 25%)
        splitter.setSizes([240, 660, 300])
        
        layout.addWidget(splitter)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _setup_menus(self) -> None:
        """Set up application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_folder_action = QAction("Open Folder...", self)
        open_folder_action.setShortcut(QKeySequence.StandardKey.Open)
        open_folder_action.triggered.connect(self._on_open_folder)
        file_menu.addAction(open_folder_action)
        
        open_files_action = QAction("Open Files...", self)
        open_files_action.triggered.connect(self._on_open_files)
        file_menu.addAction(open_files_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        clear_tags_action = QAction("Clear All Tags", self)
        clear_tags_action.triggered.connect(self._on_clear_tags)
        edit_menu.addAction(clear_tags_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        next_image_action = QAction("Next Image", self)
        next_image_action.setShortcut(QKeySequence("Right"))
        next_image_action.triggered.connect(self._on_next_image)
        view_menu.addAction(next_image_action)
        
        prev_image_action = QAction("Previous Image", self)
        prev_image_action.setShortcut(QKeySequence("Left"))
        prev_image_action.triggered.connect(self._on_previous_image)
        view_menu.addAction(prev_image_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self) -> None:
        """Connect signals between panels."""
        # Left panel signals
        self.left_panel.file_selected.connect(self._on_file_selected)
        self.left_panel.files_added.connect(self._on_files_added)
        
        # Right panel signals
        self.right_panel.tags_changed.connect(self._on_tags_changed)
        
        # Middle panel signals
        self.middle_panel.next_image_requested.connect(self._on_next_image)
        self.middle_panel.previous_image_requested.connect(self._on_previous_image)
    
    def _load_defaults(self) -> None:
        """Load default tags and settings."""
        self.right_panel.add_default_tags()
        self._update_available_tags()
    
    def _on_open_folder(self) -> None:
        """Handle open folder action."""
        self.left_panel._on_open_folder()
    
    def _on_open_files(self) -> None:
        """Handle open files action."""
        self.left_panel._on_open_files()
    
    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection from left panel."""
        # Find or create ImageItem
        for i, item in enumerate(self._image_items):
            if str(item.file_path) == file_path:
                self._current_image_index = i
                break
        else:
            # Create new ImageItem
            item = ImageItem(file_path=file_path)
            self._image_items.append(item)
            self._current_image_index = len(self._image_items) - 1
        
        self._display_current_image()
    
    def _on_files_added(self, file_paths: List[str]) -> None:
        """Handle multiple files added."""
        self._image_items.clear()
        self._current_image_index = -1
        
        for path in file_paths:
            item = ImageItem(file_path=path)
            self._image_items.append(item)
        
        if self._image_items:
            self._current_image_index = 0
            self._display_current_image()
            self.status_bar.showMessage(f"Loaded {len(self._image_items)} images")
    
    def _display_current_image(self) -> None:
        """Display the current image."""
        if 0 <= self._current_image_index < len(self._image_items):
            item = self._image_items[self._current_image_index]
            self.middle_panel.load_image(item)
            self._update_navigation()
            self.status_bar.showMessage(
                f"Image {self._current_image_index + 1} of {len(self._image_items)}"
            )
    
    def _update_navigation(self) -> None:
        """Update navigation button states."""
        has_prev = self._current_image_index > 0
        has_next = self._current_image_index < len(self._image_items) - 1
        self.middle_panel.set_navigation_enabled(has_prev, has_next)
    
    def _on_next_image(self) -> None:
        """Navigate to next image."""
        if self._current_image_index < len(self._image_items) - 1:
            self._current_image_index += 1
            self._display_current_image()
    
    def _on_previous_image(self) -> None:
        """Navigate to previous image."""
        if self._current_image_index > 0:
            self._current_image_index -= 1
            self._display_current_image()
    
    def _on_tags_changed(self) -> None:
        """Handle tags changed in right panel."""
        self._update_available_tags()
    
    def _update_available_tags(self) -> None:
        """Update available tags in middle panel."""
        tags = self.right_panel.get_tags()
        self.middle_panel.set_available_tags(tags)
    
    def _on_clear_tags(self) -> None:
        """Clear all tags from current image."""
        current = self.middle_panel.get_current_image()
        if current:
            current.tags.clear()
            self.middle_panel.load_image(current)
            self.status_bar.showMessage("Tags cleared")
    
    def _on_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Image Tagger",
            "Image Tagger v1.0\n\n"
            "A desktop application for tagging and organizing images.\n\n"
            "Features:\n"
            "• Browse and load image folders/files\n"
            "• Create custom tags with colors\n"
            "• Organize tags by classification\n"
            "• Support for PNG and JPG images"
        )
