#!/usr/bin/env python3
"""Main entry point for the Image Tagging Application."""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.main_window import ImageTaggingApp


def main():
    """Main function to run the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Image Tagger")
    app.setApplicationVersion("1.0.0")
    
    # Apply dark theme style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = ImageTaggingApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
