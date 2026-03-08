"""Middle panel for image viewing and tagging."""
from pathlib import Path
from typing import List, Optional, Tuple
import io
from PIL import Image as PILImage, ImageEnhance, ImageQt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QComboBox,
    QSpacerItem, QSizePolicy, QSlider, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect, QPointF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QCursor, QPainterPath, QFont, QTransform
from ..models.tag import Tag
from ..models.image_item import ImageItem


class ImageLabel(QLabel):
    """Custom QLabel for displaying images with scaling and drawing."""
    
    stroke_drawn = pyqtSignal(QPointF, QPointF)
    point_clicked = pyqtSignal(QPointF)
    hover_moved = pyqtSignal(QPointF)
    mouse_released = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self._base_image: Optional[QImage] = None
        self._overlay: Optional[QImage] = None
        self._overlay_opacity = 1.0
        self._drawing_enabled = False
        self._last_pos: Optional[QPointF] = None
        self._draw_rect = QRect()
        self._zoom = 1.0
        self._pan_offset = QPointF()
        self._is_panning = False
        self._last_mouse_pos = QPointF()
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #2a2a2a;")
    
    def set_image(self, image: Optional[QImage]) -> None:
        """Set the base image."""
        self._base_image = image
        if image:
            self._update_draw_rect()
        else:
            self._overlay = None
            self._draw_rect = QRect()
        self.update()
    
    def set_overlay(self, overlay: Optional[QImage], opacity: float = 1.0) -> None:
        """Set the overlay mask to display on top of image."""
        self._overlay = overlay
        self._overlay_opacity = opacity
        self.update()
    
    def set_drawing_enabled(self, enabled: bool) -> None:
        """Enable or disable drawing mode."""
        self._drawing_enabled = enabled
    
    def reset_view(self) -> None:
        """Reset zoom and pan."""
        self._zoom = 1.0
        self._pan_offset = QPointF()
        self._update_draw_rect()
        self.update()
    
    def set_cursor_for_mode(self, tool_mode: str, brush_size: int) -> None:
        """Update cursor based on current tool."""
        if tool_mode == "brush":
            size = max(6, brush_size)
            cursor_pixmap = QPixmap(size + 2, size + 2)
            cursor_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(cursor_pixmap)
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawEllipse(1, 1, size, size)
            painter.end()
            self.setCursor(QCursor(cursor_pixmap))
        elif tool_mode == "polygon":
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif tool_mode == "keypoint":
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.unsetCursor()
    
    def get_draw_rect(self) -> QRect:
        """Get the rectangle where the image is drawn within the label."""
        return self._draw_rect
    
    def get_image_size(self) -> Optional[QSize]:
        """Get the base image size."""
        if self._base_image:
            return self._base_image.size()
        return None
    
    def map_to_image(self, pos: QPointF) -> Optional[QPointF]:
        """Map a label position to image coordinates."""
        if self._draw_rect.isNull() or self._base_image is None:
            return None
        if not self._draw_rect.contains(pos.toPoint()):
            return None
        scale_x = self._base_image.width() / self._draw_rect.width()
        scale_y = self._base_image.height() / self._draw_rect.height()
        x = (pos.x() - self._draw_rect.x()) * scale_x
        y = (pos.y() - self._draw_rect.y()) * scale_y
        return QPointF(x, y)
    
    def map_from_image(self, pos: QPointF) -> Optional[QPointF]:
        """Map image coordinates to label coordinates."""
        if self._draw_rect.isNull() or self._base_image is None:
            return None
        scale_x = self._draw_rect.width() / self._base_image.width()
        scale_y = self._draw_rect.height() / self._base_image.height()
        x = self._draw_rect.x() + pos.x() * scale_x
        y = self._draw_rect.y() + pos.y() * scale_y
        return QPointF(x, y)
    
    def _update_draw_rect(self) -> None:
        """Update the rectangle where the image is drawn."""
        if not self._base_image:
            return
        scaled_width = self._base_image.width() * self._zoom
        scaled_height = self._base_image.height() * self._zoom
        x = (self.width() - scaled_width) / 2 + self._pan_offset.x()
        y = (self.height() - scaled_height) / 2 + self._pan_offset.y()
        self._draw_rect = QRect(int(x), int(y), int(scaled_width), int(scaled_height))
    
    def paintEvent(self, event) -> None:
        """Custom paint event for drawing image and overlay."""
        super().paintEvent(event)
        if not self._base_image:
            return
        self._update_draw_rect()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        target_rect = self._draw_rect
        painter.drawImage(target_rect, self._base_image)
        if self._overlay:
            painter.setOpacity(self._overlay_opacity)
            painter.drawImage(target_rect, self._overlay)
        painter.end()
    
    def resizeEvent(self, event) -> None:
        """Handle resize events to rescale the image."""
        super().resizeEvent(event)
        if self._base_image:
            self._update_draw_rect()
    
    def wheelEvent(self, event) -> None:
        """Handle zoom with mouse wheel."""
        if not self._base_image:
            return
        old_pos = self.map_to_image(event.position())
        if old_pos is None:
            return
        factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        new_zoom = max(0.2, min(5.0, self._zoom * factor))
        self._zoom = new_zoom
        self._update_draw_rect()
        new_pos = self.map_from_image(old_pos)
        if new_pos:
            delta = event.position() - new_pos
            self._pan_offset += delta
            self._update_draw_rect()
        self.update()
    
    def mousePressEvent(self, event) -> None:
        """Start drawing stroke or add polygon points."""
        if event.button() == Qt.MouseButton.RightButton:
            self._is_panning = True
            self._last_mouse_pos = event.position()
            return
        if self._drawing_enabled and event.button() == Qt.MouseButton.LeftButton:
            image_pos = self.map_to_image(event.position())
            if image_pos is None:
                return
            self._last_pos = image_pos
            self.point_clicked.emit(image_pos)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        """Draw while mouse moves or pan."""
        if self._is_panning:
            delta = event.position() - self._last_mouse_pos
            self._pan_offset += delta
            self._last_mouse_pos = event.position()
            self._update_draw_rect()
            self.update()
            return
        if self._drawing_enabled:
            image_pos = self.map_to_image(event.position())
            if image_pos:
                self.hover_moved.emit(image_pos)
            if self._last_pos and image_pos:
                self.stroke_drawn.emit(self._last_pos, image_pos)
                self._last_pos = image_pos
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """End drawing stroke or drag."""
        if event.button() == Qt.MouseButton.RightButton:
            self._is_panning = False
        if self._drawing_enabled and event.button() == Qt.MouseButton.LeftButton:
            self._last_pos = None
        self.mouse_released.emit()
        super().mouseReleaseEvent(event)


class TagBadge(QFrame):
    """A badge widget to display a tag on an image."""
    
    remove_requested = pyqtSignal(object)  # Emits the tag
    
    def __init__(self, tag: Tag, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tag = tag
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the tag badge UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Tag name label
        name_label = QLabel(self.tag.name)
        name_label.setStyleSheet(f"color: white;")
        layout.addWidget(name_label)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 8px;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.tag))
        layout.addWidget(remove_btn)
        
        # Set background color based on tag color
        color = self.tag.color
        self.setStyleSheet(f"""
            TagBadge {{
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 200);
                border-radius: 10px;
            }}
        """)
        
        self.setLayout(layout)


class ImageViewerPanel(QWidget):
    """Panel for viewing images and managing their tags."""
    
    # Signals
    tag_added = pyqtSignal(object)   # Emits Tag
    tag_removed = pyqtSignal(object)  # Emits Tag
    next_image_requested = pyqtSignal()
    previous_image_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_image: Optional[ImageItem] = None
        self._available_tags: List[Tag] = []
        self._active_tag: Optional[Tag] = None
        self._is_erase_mode = False
        self._brush_size = 10
        self._brush_opacity = 180
        self._brush_alpha = 180
        self._brightness = 0
        self._contrast = 0
        self._tool_mode = "brush"
        self._current_polygon: List[QPointF] = []
        self._hover_pos: Optional[QPointF] = None
        self._dragging_point: Optional[Tuple[int, int, int]] = None
        self._drag_offset = QPointF()
        self._setup_ui()
        self._connect_signals()
        self._update_cursor()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Image Viewer")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Image display area
        self.image_label = ImageLabel()
        self.image_label.setText("No Image Loaded")
        self.image_label.setMinimumSize(400, 300)
        layout.addWidget(self.image_label, 1)
        
        # View controls
        view_layout = QHBoxLayout()
        self.reset_view_btn = QPushButton("Reset View")
        view_layout.addWidget(self.reset_view_btn)
        view_layout.addStretch()
        layout.addLayout(view_layout)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)
        
        nav_layout.addStretch()
        
        self.image_info_label = QLabel("")
        self.image_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.image_info_label)
        
        nav_layout.addStretch()
        
        self.next_btn = QPushButton("Next →")
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Tag assignment section
        tag_section = QVBoxLayout()
        
        tag_header = QLabel("Assign Tags")
        tag_header.setStyleSheet("font-weight: bold;")
        tag_section.addWidget(tag_header)
        
        # Tag selector
        tag_selector_layout = QHBoxLayout()
        
        self.tag_combo = QComboBox()
        self.tag_combo.setPlaceholderText("Select a tag...")
        tag_selector_layout.addWidget(self.tag_combo, 1)
        
        self.add_tag_btn = QPushButton("Add Tag")
        self.add_tag_btn.setEnabled(False)
        tag_selector_layout.addWidget(self.add_tag_btn)
        
        tag_section.addLayout(tag_selector_layout)
        
        # Brush controls
        brush_layout = QHBoxLayout()
        
        self.tool_mode_btn = QPushButton("Brush")
        self.tool_mode_btn.setCheckable(True)
        self.tool_mode_btn.setChecked(True)
        brush_layout.addWidget(self.tool_mode_btn)
        
        self.keypoint_mode_btn = QPushButton("Keypoint")
        self.keypoint_mode_btn.setCheckable(True)
        brush_layout.addWidget(self.keypoint_mode_btn)
        
        self.brush_mode_btn = QPushButton("Draw")
        self.brush_mode_btn.setCheckable(True)
        self.brush_mode_btn.setChecked(True)
        brush_layout.addWidget(self.brush_mode_btn)
        
        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setRange(2, 60)
        self.brush_size_slider.setValue(self._brush_size)
        self.brush_size_slider.setToolTip("Brush size")
        brush_layout.addWidget(QLabel("Size"))
        brush_layout.addWidget(self.brush_size_slider, 1)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 255)
        self.opacity_slider.setValue(self._brush_opacity)
        self.opacity_slider.setToolTip("Brush opacity")
        brush_layout.addWidget(QLabel("Opacity"))
        brush_layout.addWidget(self.opacity_slider, 1)
        
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(10, 255)
        self.alpha_slider.setValue(self._brush_alpha)
        self.alpha_slider.setToolTip("Brush transparency")
        brush_layout.addWidget(QLabel("Alpha"))
        brush_layout.addWidget(self.alpha_slider, 1)
        
        tag_section.addLayout(brush_layout)
        
        # Image adjustments
        adjustment_layout = QHBoxLayout()
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        adjustment_layout.addWidget(QLabel("Brightness"))
        adjustment_layout.addWidget(self.brightness_slider, 1)
        
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        adjustment_layout.addWidget(QLabel("Contrast"))
        adjustment_layout.addWidget(self.contrast_slider, 1)
        
        tag_section.addLayout(adjustment_layout)
        
        # Applied tags container
        self.tags_scroll = QScrollArea()
        self.tags_scroll.setWidgetResizable(True)
        self.tags_scroll.setFixedHeight(80)
        self.tags_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(5, 5, 5, 5)
        self.tags_layout.addStretch()
        
        self.tags_scroll.setWidget(self.tags_container)
        tag_section.addWidget(self.tags_scroll)
        
        layout.addLayout(tag_section)
        
        self.setLayout(layout)
    
    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self.prev_btn.clicked.connect(self.previous_image_requested.emit)
        self.next_btn.clicked.connect(self.next_image_requested.emit)
        self.add_tag_btn.clicked.connect(self._on_add_tag)
        self.tag_combo.currentIndexChanged.connect(self._on_tag_selected)
        self.tool_mode_btn.toggled.connect(self._on_tool_mode_toggled)
        self.reset_view_btn.clicked.connect(self._on_reset_view)
        self.keypoint_mode_btn.toggled.connect(self._on_keypoint_mode_toggled)
        self.brush_mode_btn.toggled.connect(self._on_brush_mode_toggled)
        self.brush_size_slider.valueChanged.connect(self._on_brush_size_changed)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.alpha_slider.valueChanged.connect(self._on_alpha_changed)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)
        self.image_label.stroke_drawn.connect(self._on_stroke_drawn)
        self.image_label.point_clicked.connect(self._on_point_clicked)
        self.image_label.hover_moved.connect(self._on_hover_moved)
        self.image_label.mouse_released.connect(self._on_mouse_released)
    
    def load_image(self, image_item: Optional[ImageItem]) -> None:
        """Load an image item into the viewer."""
        self._current_image = image_item
        # self._active_tag = None  # Preserve active tag selection
        self._current_polygon = []
        self._hover_pos = None
        self._dragging_point = None
        
        if image_item and image_item.file_path.exists():
            # Load and adjust image from file path directly
            image = self._apply_image_adjustments(str(image_item.file_path))
            if not image.isNull():
                self.image_label.set_image(image)
                self.image_info_label.setText(
                    f"{image_item.filename}\n{image.width()} × {image.height()}"
                )
                self._initialize_masks_from_tags(image)
            else:
                self.image_label.set_image(None)
                self.image_label.setText("Failed to load image")
                self.image_info_label.setText("")
        else:
            self.image_label.set_image(None)
            self.image_label.setText("No Image")
            self.image_info_label.setText("")
        
        self._update_applied_tags()
        self._refresh_overlay()
        self._update_cursor()
    
    def set_available_tags(self, tags: List[Tag]) -> None:
        """Set the list of available tags for assignment."""
        self._available_tags = tags
        self._update_tag_combo()
        self.image_label.set_drawing_enabled(bool(tags))
        self._update_cursor()
    
    def _update_tag_combo(self) -> None:
        """Update the tag selection combo box."""
        self.tag_combo.clear()
        self.tag_combo.addItem("-- Select Tag --", None)
        
        for tag in self._available_tags:
            self.tag_combo.addItem(tag.name, tag)
    
    def _on_tag_selected(self, index: int) -> None:
        """Handle tag selection in combo box."""
        self.add_tag_btn.setEnabled(index > 0)
        if index > 0:
            self._active_tag = self.tag_combo.currentData()
            self._current_polygon = []
            self._hover_pos = None
            self._dragging_point = None
            self._refresh_overlay()
    
    def _on_add_tag(self) -> None:
        """Add the selected tag to the current image."""
        tag = self.tag_combo.currentData()
        if tag and self._current_image:
            self._current_image.add_tag(tag)
            if self._current_image.masks.get(tag.id) is None:
                self._initialize_mask(tag)
            if tag.id not in self._current_image.polygons:
                self._current_image.polygons[tag.id] = []
            if tag.id not in self._current_image.keypoints:
                self._current_image.keypoints[tag.id] = []
            self._update_applied_tags()
            self.tag_added.emit(tag)
            self._active_tag = tag
            self._refresh_overlay()
    
    def _on_remove_tag(self, tag: Tag) -> None:
        """Remove a tag from the current image."""
        if self._current_image:
            self._current_image.remove_tag(tag)
            self._current_image.masks.pop(tag.id, None)
            self._current_image.polygons.pop(tag.id, None)
            self._current_image.keypoints.pop(tag.id, None)
            if self._active_tag == tag:
                self._active_tag = None
            self._update_applied_tags()
            self.tag_removed.emit(tag)
            self._refresh_overlay()
    
    def _update_applied_tags(self) -> None:
        """Update the displayed applied tags."""
        # Clear existing tag badges
        while self.tags_layout.count() > 1:
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add current tags
        if self._current_image:
            for tag in self._current_image.tags:
                badge = TagBadge(tag)
                badge.remove_requested.connect(self._on_remove_tag)
                self.tags_layout.insertWidget(
                    self.tags_layout.count() - 1, badge
                )
        self._update_cursor()
    
    def _initialize_mask(self, tag: Tag) -> None:
        """Initialize a mask for the given tag."""
        if not self._current_image or not self.image_label.get_image_size():
            return
        image_size = self.image_label.get_image_size()
        if image_size is None:
            return
        mask = QImage(image_size, QImage.Format.Format_ARGB32)
        mask.fill(Qt.GlobalColor.transparent)
        self._current_image.masks[tag.id] = mask
    
    def _initialize_masks_from_tags(self, image: QImage) -> None:
        """Ensure masks exist for tags on current image."""
        if not self._current_image:
            return
        for tag in self._current_image.tags:
            if tag.id not in self._current_image.masks:
                mask = QImage(image.size(), QImage.Format.Format_ARGB32)
                mask.fill(Qt.GlobalColor.transparent)
                self._current_image.masks[tag.id] = mask
            if tag.id not in self._current_image.polygons:
                self._current_image.polygons[tag.id] = []
            if tag.id not in self._current_image.keypoints:
                self._current_image.keypoints[tag.id] = []
    
    def _refresh_overlay(self) -> None:
        """Refresh the overlay based on active tag."""
        if not self._current_image or not self._active_tag:
            self.image_label.set_overlay(None)
            return
        base_mask = self._current_image.masks.get(self._active_tag.id)
        if base_mask is None:
            return
        overlay = base_mask.copy()
        painter = QPainter(overlay)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        polygons = self._current_image.polygons.get(self._active_tag.id, [])
        keypoints = self._current_image.keypoints.get(self._active_tag.id, [])
        color = QColor(self._active_tag.color)
        color.setAlpha(self._brush_alpha)
        painter.setBrush(color)
        painter.setPen(QPen(color))
        for polygon in polygons:
            if len(polygon) >= 3:
                path = QPainterPath()
                path.moveTo(polygon[0])
                for point in polygon[1:]:
                    path.lineTo(point)
                path.closeSubpath()
                painter.drawPath(path)
                for point in polygon:
                    painter.drawEllipse(point, 4, 4)
        
        # Draw keypoints
        kp_color = QColor(self._active_tag.color)
        kp_color.setAlpha(255)
        painter.setBrush(kp_color)
        painter.setPen(QPen(Qt.GlobalColor.white))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        
        for kp_pos, kp_name in keypoints:
            painter.drawEllipse(kp_pos, 5, 5)
            painter.drawText(kp_pos + QPointF(8, 5), kp_name)
            
        # Reset painter for current polygon
        painter.setBrush(color)
        painter.setPen(QPen(color))
        
        if self._current_polygon:
            path = QPainterPath()
            path.moveTo(self._current_polygon[0])
            for point in self._current_polygon[1:]:
                path.lineTo(point)
            if self._hover_pos:
                path.lineTo(self._hover_pos)
            painter.setPen(QPen(color, 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            for point in self._current_polygon:
                painter.drawEllipse(point, 4, 4)
        painter.end()
        self.image_label.set_overlay(overlay, self._brush_opacity / 255.0)
    
    def _on_stroke_drawn(self, start_pos: QPointF, end_pos: QPointF) -> None:
        """Handle drawing strokes on the current mask."""
        if self._tool_mode != "brush" or not self._current_image or not self._active_tag:
            return
        mask = self._current_image.masks.get(self._active_tag.id)
        if mask is None:
            self._initialize_mask(self._active_tag)
            mask = self._current_image.masks.get(self._active_tag.id)
        if mask is None:
            return
        
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self._active_tag.color)
        color.setAlpha(self._brush_alpha)
        pen = QPen(color)
        pen.setWidth(self._brush_size)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        if self._is_erase_mode:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.drawLine(start_pos, end_pos)
        painter.end()
        self._refresh_overlay()
    
    def _on_brush_mode_toggled(self, checked: bool) -> None:
        """Toggle between draw and erase modes."""
        self._is_erase_mode = not checked
        self.brush_mode_btn.setText("Draw" if checked else "Erase")
        self.image_label.set_drawing_enabled(True)
    
    def _on_keypoint_mode_toggled(self, checked: bool) -> None:
        """Toggle keypoint tool mode."""
        if checked:
            self.tool_mode_btn.setChecked(False)
            self.brush_mode_btn.setChecked(False)
            self._tool_mode = "keypoint"
            self._update_cursor()
            self._refresh_overlay()
    
    def _on_tool_mode_toggled(self, checked: bool) -> None:
        """Toggle between brush and polygon tools."""
        if checked:
            self.keypoint_mode_btn.setChecked(False)
            self._tool_mode = "brush"
            self.tool_mode_btn.setText("Brush")
            self._update_cursor()
        else:
            self._tool_mode = "polygon"
            self.tool_mode_btn.setText("Polygon")
        self._current_polygon = []
        self._dragging_point = None
        self._hover_pos = None
        self._update_cursor()
        self._refresh_overlay()
    
    def _on_point_clicked(self, pos: QPointF) -> None:
        """Handle point placement for polygon or keypoint tool."""
        if not self._current_image or not self._active_tag:
            return
        
        if self._tool_mode == "keypoint":
            dragged = self._try_start_drag(pos)
            if not dragged:
                text, ok = QInputDialog.getText(
                    self, "Keypoint Name", "Enter keypoint name:"
                )
                if ok and text:
                    keypoints = self._current_image.keypoints.setdefault(
                        self._active_tag.id, []
                    )
                    keypoints.append((pos, text))
                    self._refresh_overlay()
            return
            
        if self._tool_mode == "polygon":
            dragged = self._try_start_drag(pos)
            if dragged:
                return
            self._current_polygon.append(pos)
            self._refresh_overlay()
    
    def _on_hover_moved(self, pos: QPointF) -> None:
        """Track hover position for polygon/keypoint preview or drag points."""
        if self._dragging_point and self._current_image and self._active_tag:
            self._update_drag_position(pos)
            return
            
        if self._tool_mode == "polygon":
            self._hover_pos = pos
            self._refresh_overlay()
    
    def _on_mouse_released(self) -> None:
        """Handle mouse release event."""
        if self._dragging_point:
            self._dragging_point = None
            self._drag_offset = QPointF()
    
    def _on_reset_view(self) -> None:
        """Reset zoom and pan view."""
        self.image_label.reset_view()
    
    def _on_brush_size_changed(self, value: int) -> None:
        """Update brush size."""
        self._brush_size = value
        self._update_cursor()
    
    def _on_opacity_changed(self, value: int) -> None:
        """Update brush opacity."""
        self._brush_opacity = value
        self._refresh_overlay()
    
    def _on_alpha_changed(self, value: int) -> None:
        """Update brush transparency (alpha)."""
        self._brush_alpha = value
        self._refresh_overlay()
    
    def _on_brightness_changed(self, value: int) -> None:
        """Update brightness."""
        self._brightness = value
        self._reload_current_image()
    
    def _on_contrast_changed(self, value: int) -> None:
        """Update contrast."""
        self._contrast = value
        self._reload_current_image()
    
    def _apply_image_adjustments(self, file_path: str) -> QImage:
        """Apply brightness and contrast adjustments using Pillow."""
        try:
            pil_image = PILImage.open(file_path)
            
            # Handle brightness
            if self._brightness != 0:
                # Map -100..100 to 0.0..2.0
                factor = (self._brightness + 100) / 100.0
                enhancer = ImageEnhance.Brightness(pil_image)
                pil_image = enhancer.enhance(factor)
            
            # Handle contrast
            if self._contrast != 0:
                # Map -100..100 to 0.0..2.0
                factor = (self._contrast + 100) / 100.0
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(factor)
            
            # Convert to QImage
            # Ensure image is in a mode compatible with QImage
            if pil_image.mode == "P":
                pil_image = pil_image.convert("RGBA")
            
            return ImageQt.ImageQt(pil_image).copy()
            
        except Exception as e:
            print(f"Error adjusting image: {e}")
            return QImage()
    
    def _reload_current_image(self) -> None:
        """Reload the current image with adjustments."""
        if not self._current_image:
            return
        image = self._apply_image_adjustments(str(self._current_image.file_path))
        if image.isNull():
            return
        self.image_label.set_image(image)
        self._refresh_overlay()
    
    def _update_cursor(self) -> None:
        """Update cursor based on tool mode."""
        self.image_label.set_cursor_for_mode(self._tool_mode, self._brush_size)
    
    def keyPressEvent(self, event) -> None:
        """Handle key presses for polygon completion."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finalize_polygon()
        else:
            super().keyPressEvent(event)
    
    def _finalize_polygon(self) -> None:
        """Finalize current polygon into the active tag."""
        if not self._current_image or not self._active_tag:
            return
        if len(self._current_polygon) < 3:
            return
        polygons = self._current_image.polygons.setdefault(self._active_tag.id, [])
        polygons.append(self._current_polygon.copy())
        self._current_polygon = []
        self._hover_pos = None
        self._refresh_overlay()
    
    def _try_start_drag(self, pos: QPointF) -> bool:
        """Start dragging a polygon point or keypoint if near one."""
        threshold = 6.0
        
        # Check keypoints first
        keypoints = self._current_image.keypoints.get(self._active_tag.id, [])
        for i, (kp_pos, _) in enumerate(keypoints):
            if (kp_pos - pos).manhattanLength() <= threshold:
                self._dragging_point = (-2, i, -1)  # -2 indicates keypoint
                self._drag_offset = kp_pos - pos
                return True
                
        # Check polygons
        polygons = self._current_image.polygons.get(self._active_tag.id, [])
        for poly_index, polygon in enumerate(polygons):
            for point_index, point in enumerate(polygon):
                if (point - pos).manhattanLength() <= threshold:
                    self._dragging_point = (poly_index, point_index, -1)
                    self._drag_offset = point - pos
                    return True
                    
        # Check current polygon being drawn
        for point_index, point in enumerate(self._current_polygon):
            if (point - pos).manhattanLength() <= threshold:
                self._dragging_point = (-1, point_index, -1)
                self._drag_offset = point - pos
                return True
                
        return False
    
    def _update_drag_position(self, pos: QPointF) -> None:
        """Update the currently dragged point position."""
        if not self._dragging_point or not self._current_image or not self._active_tag:
            return
            
        poly_index, point_index, _ = self._dragging_point
        new_pos = pos + self._drag_offset
        
        if poly_index == -2:  # Keypoint
            keypoints = self._current_image.keypoints.get(self._active_tag.id, [])
            if 0 <= point_index < len(keypoints):
                original_kp = keypoints[point_index]
                keypoints[point_index] = (new_pos, original_kp[1])
        elif poly_index == -1:  # Current polygon
            if 0 <= point_index < len(self._current_polygon):
                self._current_polygon[point_index] = new_pos
        else:  # Existing polygon
            polygons = self._current_image.polygons.get(self._active_tag.id, [])
            if 0 <= poly_index < len(polygons):
                polygon = polygons[poly_index]
                if 0 <= point_index < len(polygon):
                    polygon[point_index] = new_pos
                    
        self._refresh_overlay()
    
    def set_navigation_enabled(self, has_prev: bool, has_next: bool) -> None:
        """Enable or disable navigation buttons."""
        self.prev_btn.setEnabled(has_prev)
        self.next_btn.setEnabled(has_next)
    
    def get_current_image(self) -> Optional[ImageItem]:
        """Get the currently displayed image item."""
        return self._current_image
