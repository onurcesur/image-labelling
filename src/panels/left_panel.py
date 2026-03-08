"""Left panel for file and folder browsing."""
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTreeView, QFileDialog, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDir
from PyQt6.QtGui import QFileSystemModel, QStandardItemModel, QStandardItem


SUPPORTED_FORMATS = ['*.png', '*.jpg', '*.jpeg']


class FileBrowserPanel(QWidget):
    """Panel for browsing and selecting files/folders."""
    
    # Signals
    folder_selected = pyqtSignal(str)  # Emits folder path
    file_selected = pyqtSignal(str)    # Emits file path
    files_added = pyqtSignal(list)     # Emits list of file paths
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("File Browser")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Buttons for folder and file selection
        button_layout = QHBoxLayout()
        
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setToolTip("Open a folder containing images")
        button_layout.addWidget(self.open_folder_btn)
        
        self.open_files_btn = QPushButton("Open Files")
        self.open_files_btn.setToolTip("Select individual image files")
        button_layout.addWidget(self.open_files_btn)
        
        layout.addLayout(button_layout)
        
        # Search/filter input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.search_input)
        
        # File tree view
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setAlternatingRowColors(True)
        layout.addWidget(self.tree_view)
        
        # File list model
        self.file_model = QStandardItemModel()
        self.file_model.setHorizontalHeaderLabels(["Files"])
        self.tree_view.setModel(self.file_model)
        
        # Status label
        self.status_label = QLabel("No files loaded")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(200)
    
    def _connect_signals(self) -> None:
        """Connect button signals to slots."""
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        self.open_files_btn.clicked.connect(self._on_open_files)
        self.tree_view.selectionModel().selectionChanged.connect(self._on_tree_selection_changed)
        self.search_input.textChanged.connect(self._on_search_changed)
    
    def _on_open_folder(self) -> None:
        """Handle open folder button click."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder_path:
            self._load_folder(folder_path)
            self.folder_selected.emit(folder_path)
    
    def _on_open_files(self) -> None:
        """Handle open files button click."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            f"Images ({' '.join(SUPPORTED_FORMATS)})"
        )
        if file_paths:
            self._load_files(file_paths)
            self.files_added.emit(file_paths)
    
    def _load_folder(self, folder_path: str) -> None:
        """Load all images from a folder."""
        folder = Path(folder_path)
        image_files = []
        
        for ext in SUPPORTED_FORMATS:
            image_files.extend(folder.glob(ext))
        
        self._populate_file_list([str(f) for f in image_files])
        self.status_label.setText(f"{len(image_files)} images loaded")
    
    def _load_files(self, file_paths: List[str]) -> None:
        """Load specific files into the list."""
        valid_files = [
            f for f in file_paths 
            if Path(f).suffix.lower() in ['.png', '.jpg', '.jpeg']
        ]
        self._populate_file_list(valid_files)
        self.status_label.setText(f"{len(valid_files)} images loaded")
    
    def _populate_file_list(self, file_paths: List[str]) -> None:
        """Populate the file list with given paths."""
        self.file_model.clear()
        self.file_model.setHorizontalHeaderLabels(["Files"])
        
        for file_path in file_paths:
            item = QStandardItem(Path(file_path).name)
            item.setData(file_path, Qt.ItemDataRole.UserRole)
            item.setToolTip(file_path)
            self.file_model.appendRow(item)
    
    def _on_tree_selection_changed(self) -> None:
        """Handle tree item selection change."""
        indexes = self.tree_view.selectedIndexes()
        if not indexes:
            return
        item = self.file_model.itemFromIndex(indexes[0])
        if item:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.file_selected.emit(file_path)
    
    def _on_search_changed(self, text: str) -> None:
        """Filter files based on search text."""
        # TODO: Implement file filtering
        pass
    
    def get_selected_file(self) -> Optional[str]:
        """Get the currently selected file path."""
        indexes = self.tree_view.selectedIndexes()
        if indexes:
            item = self.file_model.itemFromIndex(indexes[0])
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None
