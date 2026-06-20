# Advanced Robust File Organizer

An automated, safe, and customizable command-line interface (CLI) utility designed to organize cluttered folders into neatly structured categories. It sorts files based on extensions, handles file collisions securely, isolates identical duplicates, supports instant undo, and offers real-time folder monitoring.

## Key Features

- **Extension-Based Categorization**: Groups files into intuitive default directories (e.g., Documents, Images, Audio, Video, Archives, Scripts, Executables) or custom classifications.
- **Collision Avoidance**: Automatically appends indices (e.g., `file (1).txt`) to filenames if a conflict occurs, avoiding accidental overwriting.
- **Duplicate Detection**: Computes SHA-256 hashes of files to safely recognize exact content duplicates and isolate them in a dedicated `Duplicates` folder.
- **Flexible Configuration**: Automatically generates a local `.organizer_config.json` inside the targeted directory, allowing customization of file extensions, custom-ignored folders/files, and optional date-based sorting.
- **Rollback System (Undo)**: Logs movements in a local `.organizer_history.json` footprint to facilitate a clean reversal of the last organization cycle.
- **Optional Real-Time Monitoring**: Integrates with the Python `watchdog` library to actively listen for filesystem changes and categorize files immediately upon creation.
- **Detailed Log Records**: Records execution footprints inside a local `organizer.log` file to help identify and troubleshoot issues.

## Prerequisites

This utility operates using Python's standard library. However, if you wish to use the **active background monitoring** feature, you will need to install the optional `watchdog` package.

```bash
pip install watchdog
```

## Usage

Save the script as `organizer.py` and run it from your terminal.

### Basic Organization
By default, the script targets your home `Downloads` folder:
```bash
python3 organizer.py
```

To target a specific folder, pass the path as an argument:
```bash
python3 organizer.py /path/to/your/target/folder
```

### Dry Run (Simulation Mode)
Verify what changes the tool would make without actually moving files on your drive:
```bash
python3 organizer.py /path/to/folder --dry-run
```

### Reversing the Last Run
If you are unsatisfied with how the files were organized, you can revert the action and restore them to their original locations:
```bash
python3 organizer.py /path/to/folder --undo
```

### Active Background Watchdog
To run a persistent daemon that automatically monitors the folder and organizes incoming files in real-time:
```bash
python3 organizer.py /path/to/folder --watch
```

### Silent Mode
Minimize terminal output during automated tasks (useful for cron jobs or scheduled tasks):
```bash
python3 organizer.py /path/to/folder --silent
```

## Custom Configuration

Upon running the organizer in a target directory for the first time, a hidden configuration file named `.organizer_config.json` is generated. You can modify this JSON file to fine-tune how the tool works.

### Default Configuration Structure:
```json
{
    "file_types": {
        "Images": [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".svg", ".tiff", ".webp", ".heic"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".md"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
        "Video": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"],
        "Scripts": [".py", ".js", ".html", ".css", ".sh", ".bat", ".ps1", ".json", ".xml", ".yaml", ".yml"],
        "Executables": [".exe", ".msi", ".dmg", ".pkg", ".app", ".deb", ".rpm"]
    },
    "organize_by_date": false,
    "date_format": "%Y-%m",
    "ignored_files": [".organizer_config.json", ".organizer_history.json", "organizer.log", ".DS_Store", "desktop.ini"],
    "ignored_folders": ["Other", "Duplicates", "Images", "Documents", "Archives", "Audio", "Video", "Scripts", "Executables"],
    "detect_duplicates": true
}
```

- **`organize_by_date`**: If changed to `true`, files will be categorized and placed inside monthly subfolders (e.g., `Documents/2026-06/proposal.pdf`).
- **`ignored_files` / `ignored_folders`**: Prevents the script from moving or recursing into specific system files, logs, or predefined outputs.

## Logging & Auditing

For transparency, the tool creates a local `organizer.log` inside the execution folder. It documents all move actions and errors. If an error is encountered, check this file for details.
