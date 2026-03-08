# Image Tagger

A desktop image tagging application built with PyQt6.

## Features

- **Left Panel**: Browse and upload folders/files containing images
- **Middle Panel**: View images and assign/remove tags
- **Right Panel**: Create and manage custom tags with colors and classifications
- Support for PNG and JPG file formats
- Resizable panels with splitter layout
- Dark-themed interface

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
cd /testbed/zed-base
python -m src.main
```

## Project Structure

```
src/
├── main.py              # Application entry point
├── main_window.py       # Main application window
├── models/
│   ├── tag.py           # Tag data model
│   └── image_item.py    # Image item model
├── panels/
│   ├── left_panel.py    # File browser panel
│   ├── middle_panel.py  # Image viewer panel
│   └── right_panel.py   # Tag manager panel
└── utils/
    └── file_utils.py    # File utility functions
```

## Keyboard Shortcuts

- `Ctrl+O`: Open folder
- `Left Arrow`: Previous image
- `Right Arrow`: Next image
- `Ctrl+Q`: Exit application