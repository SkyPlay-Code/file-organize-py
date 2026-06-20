#!/usr/bin/env python3
"""
Advanced Robust File Organizer
A resilient, safe, and feature-rich utility for automated file management.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ==============================================================================
# ANSI Color Codes for Rich Terminal Output
# ==============================================================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(text: str, color_code: str, bold: bool = False):
    """Prints text decorated with terminal ANSI escape codes safely."""
    # Check if the terminal supports color (standard check)
    has_colors = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    if has_colors:
        prefix = f"{Colors.BOLD}{color_code}" if bold else color_code
        print(f"{prefix}{text}{Colors.RESET}")
    else:
        print(text)


# ==============================================================================
# CONFIGURATION MANAGEMENT
# ==============================================================================
DEFAULT_FILE_TYPES = {
    "Images":       [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".svg", ".tiff", ".webp", ".heic"],
    "Documents":    [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".md"],
    "Archives":     [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Audio":        [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Video":        [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"],
    "Scripts":      [".py", ".js", ".html", ".css", ".sh", ".bat", ".ps1", ".json", ".xml", ".yaml", ".yml"],
    "Executables":  [".exe", ".msi", ".dmg", ".pkg", ".app", ".deb", ".rpm"]
}

CONFIG_FILE_NAME = ".organizer_config.json"
HISTORY_FILE_NAME = ".organizer_history.json"


def load_config(directory: Path) -> Dict:
    """Loads configuration from JSON or creates a default one if missing."""
    config_path = directory / CONFIG_FILE_NAME
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print_colored(f"Warning: Failed to load config file. Using defaults. Reason: {e}", Colors.YELLOW)
    
    # Default Config Structure
    default_config = {
        "file_types": DEFAULT_FILE_TYPES,
        "organize_by_date": False,
        "date_format": "%Y-%m",  # e.g., "2026-06"
        "ignored_files": [CONFIG_FILE_NAME, HISTORY_FILE_NAME, "organizer.log", ".DS_Store", "desktop.ini"],
        "ignored_folders": ["Other", "Duplicates"] + list(DEFAULT_FILE_TYPES.keys()),
        "detect_duplicates": True
    }
    
    # Save the default configuration for future user modification
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
    except Exception as e:
        print_colored(f"Note: Could not write config file: {e}", Colors.YELLOW)
        
    return default_config


# ==============================================================================
# DETAILED FILE HANDLING UTILITIES
# ==============================================================================
def get_safe_destination(target_path: Path) -> Path:
    """
    Prevents file overwriting. If 'file.txt' exists, returns 'file (1).txt', 
    then 'file (2).txt', and so on.
    """
    if not target_path.exists():
        return target_path
    
    parent = target_path.parent
    stem = target_path.stem
    suffix = target_path.suffix
    
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def calculate_file_hash(file_path: Path) -> Optional[str]:
    """Computes SHA-256 hash to reliably detect duplicate file contents."""
    sha256 = hashlib.sha256()
    try:
        # Read in binary chunks to protect memory footprint on large files
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None


# ==============================================================================
# MAIN ENGINE CLASS
# ==============================================================================
class FileOrganizer:
    def __init__(self, directory: Path, dry_run: bool = False, verbose: bool = True):
        self.directory = directory.resolve()
        self.dry_run = dry_run
        self.verbose = verbose
        
        # Load custom configuration
        self.config = load_config(self.directory)
        self.file_types = self.config.get("file_types", DEFAULT_FILE_TYPES)
        self.ignored_files = set(self.config.get("ignored_files", []))
        self.ignored_folders = set(self.config.get("ignored_folders", []))
        
        # Action history to support undo options
        self.history: List[Dict[str, str]] = []
        
        # Setup logging to a local file for post-crash postmortems
        logging.basicConfig(
            filename=self.directory / "organizer.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def _should_ignore(self, path: Path) -> bool:
        """Determines if a file or directory should be ignored based on settings."""
        if path.name in self.ignored_files:
            return True
        if path.is_dir() and path.name in self.ignored_folders:
            return True
        return False

    def get_destination_folder(self, file_path: Path) -> Tuple[str, Path]:
        """Calculates destination category and subfolder path based on file suffix."""
        suffix = file_path.suffix.lower()
        category = "Other"
        
        # Find matching rule
        for cat, extensions in self.file_types.items():
            if suffix in extensions:
                category = cat
                break
                
        destination_dir = self.directory / category
        
        # Append date directory if enabled
        if self.config.get("organize_by_date", False):
            try:
                mtime = file_path.stat().st_mtime
                date_str = datetime.fromtimestamp(mtime).strftime(self.config.get("date_format", "%Y-%m"))
                destination_dir = destination_dir / date_str
            except Exception as e:
                logging.warning(f"Failed to read file modification time for {file_path.name}: {e}")
                
        return category, destination_dir

    def run(self) -> bool:
        """Executes the file organization pipeline."""
        if not self.directory.is_dir():
            print_colored(f"Error: Path '{self.directory}' is not a valid directory.", Colors.RED, bold=True)
            return False

        print_colored(f"\n--- Organizing Directory: {self.directory} ---", Colors.CYAN, bold=True)
        if self.dry_run:
            print_colored("!!! DRY RUN SIMULATION - No changes will be written to disk !!!\n", Colors.YELLOW, bold=True)

        files_to_process = []
        try:
            for item in self.directory.iterdir():
                if item.is_dir() or self._should_ignore(item):
                    continue
                files_to_process.append(item)
        except Exception as e:
            print_colored(f"Error scanning directory: {e}", Colors.RED)
            return False

        if not files_to_process:
            print_colored("No eligible files found to organize.", Colors.GREEN)
            return True

        # Track unique files to detect matches
        processed_hashes: Dict[str, Path] = {}
        moved_count = 0
        error_count = 0

        # Step 1: Pre-scan files for duplicate detection
        if self.config.get("detect_duplicates", True):
            if self.verbose:
                print_colored("Scanning files for duplicate content...", Colors.BLUE)
            for file_path in files_to_process:
                file_hash = calculate_file_hash(file_path)
                if file_hash:
                    # Check if we already have this file in our base folder, or inside existing folders
                    processed_hashes[file_hash] = file_path

        # Step 2: Begin movement phase
        for file_path in files_to_process:
            if not file_path.exists():
                continue

            category = "Other"
            destination_dir = self.directory / "Other"

            # Check if current file is a duplicate of one we've already processed
            is_duplicate = False
            if self.config.get("detect_duplicates", True):
                file_hash = calculate_file_hash(file_path)
                if file_hash and file_hash in processed_hashes and processed_hashes[file_hash] != file_path:
                    category = "Duplicates"
                    destination_dir = self.directory / "Duplicates"
                    is_duplicate = True

            if not is_duplicate:
                category, destination_dir = self.get_destination_folder(file_path)

            final_destination = destination_dir / file_path.name
            
            # Resolve collisions
            final_destination = get_safe_destination(final_destination)

            if self.dry_run:
                # Simulation mode only prints intent
                dup_label = " (Duplicate)" if is_duplicate else ""
                print(f"[SIMULATED] Move: '{file_path.name}' -> '{category}/{final_destination.relative_to(destination_dir.parent)}'{dup_label}")
                continue

            # Ensure target folder exists (Lazy creation)
            try:
                destination_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print_colored(f"Error: Could not create folder {destination_dir.name}. Reason: {e}", Colors.RED)
                logging.error(f"Folder creation failure: {destination_dir} - {e}")
                error_count += 1
                continue

            # Move file safely
            try:
                # Record source and absolute destination for rollback
                self.history.append({
                    "src": str(file_path.resolve()),
                    "dst": str(final_destination.resolve())
                })
                
                # shutil.move is safer across devices/filesystems than os.rename
                shutil.move(str(file_path), str(final_destination))
                
                if self.verbose:
                    status_color = Colors.YELLOW if is_duplicate else Colors.GREEN
                    dup_tag = "[DUP] " if is_duplicate else ""
                    print_colored(f"✓ Moved: {dup_tag}{file_path.name} -> {category}/{final_destination.name}", status_color)
                
                logging.info(f"Successfully organized: {file_path.name} to {final_destination}")
                moved_count += 1
                
            except Exception as e:
                print_colored(f"✗ Error: Failed to move '{file_path.name}'. File may be locked or open. Reason: {e}", Colors.RED)
                logging.error(f"Failed moving {file_path.name} to {final_destination}: {e}")
                error_count += 1

        # Write execution footprint history
        if not self.dry_run and self.history:
            self._save_history()

        # Wrap-up summary output
        print_colored("\n--- Execution Summary ---", Colors.CYAN, bold=True)
        if self.dry_run:
            print_colored(f"Simulated checking {len(files_to_process)} files successfully.", Colors.GREEN)
        else:
            print_colored(f"Files successfully organized: {moved_count}", Colors.GREEN)
            if error_count > 0:
                print_colored(f"Encountered {error_count} process exceptions. Check 'organizer.log' details.", Colors.RED)
        return True

    def _save_history(self):
        """Saves current movement matrix to the local history file for future undo requests."""
        history_path = self.directory / HISTORY_FILE_NAME
        try:
            # Overwrites prior operations run to prevent invalid massive chains.
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            logging.error(f"Could not log rollback information: {e}")

    def undo(self) -> bool:
        """Reads local run logs to reverse the last categorization actions."""
        history_path = self.directory / HISTORY_FILE_NAME
        if not history_path.exists():
            print_colored("No history file found. Nothing to roll back.", Colors.YELLOW)
            return False

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                moves = json.load(f)
        except Exception as e:
            print_colored(f"Error reading history profile: {e}", Colors.RED)
            return False

        if not moves:
            print_colored("No movements recorded in history archive.", Colors.YELLOW)
            return False

        print_colored(f"\n--- Reversing Last Action ({len(moves)} steps) ---", Colors.CYAN, bold=True)
        reversed_count = 0
        failed_count = 0

        # Execute rollback in reverse order
        for move in reversed(moves):
            src = Path(move["src"])
            dst = Path(move["dst"])

            if not dst.exists():
                print_colored(f"Skipped: Target file '{dst.name}' was already removed or relocated since run.", Colors.YELLOW)
                failed_count += 1
                continue

            try:
                # Re-verify and resolve path names if necessary (though rollback typically is exact)
                actual_src = get_safe_destination(src)
                shutil.move(str(dst), str(actual_src))
                print_colored(f"✓ Restored: {dst.name} -> original home", Colors.GREEN)
                reversed_count += 1
            except Exception as e:
                print_colored(f"✗ Failed: Could not restore '{dst.name}' to '{src}': {e}", Colors.RED)
                failed_count += 1

        # Cleanup empty subdirectories left over during rollback
        self._cleanup_empty_dirs()

        # Safely remove local database track on complete rollback
        try:
            history_path.unlink()
        except Exception as e:
            logging.error(f"Failed to clear history database file: {e}")

        print_colored(f"\nRollback complete. Successfully restored: {reversed_count} files.", Colors.GREEN)
        if failed_count > 0:
            print_colored(f"Failed to restore {failed_count} files.", Colors.RED)
        return True

    def _cleanup_empty_dirs(self):
        """Cleans empty directory categories left behind by standard undo routines."""
        for name in list(self.file_types.keys()) + ["Other", "Duplicates"]:
            folder = self.directory / name
            if folder.is_dir():
                # Clean nested structures recursively
                for root, dirs, files in os.walk(folder, topdown=False):
                    for d in dirs:
                        dir_path = Path(root) / d
                        try:
                            if not os.listdir(dir_path):
                                dir_path.rmdir()
                        except OSError:
                            pass
                try:
                    if not os.listdir(folder):
                        folder.rmdir()
                        print_colored(f"Removed empty category folder: {folder.name}/", Colors.BLUE)
                except OSError:
                    pass


# ==============================================================================
# OPTIONAL BACKGROUND WATCHDOG MODE
# ==============================================================================
def start_watchdog_service(directory: Path):
    """Monitors directory for real-time adjustments if the watchdog package is present."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print_colored("Error: Dynamic monitoring requires the 'watchdog' Python library.", Colors.RED, bold=True)
        print("To install, run: pip install watchdog")
        return

    class FolderHandler(FileSystemEventHandler):
        def __init__(self, organizer: FileOrganizer):
            self.organizer = organizer
            self.cooldowns: Dict[str, float] = {}

        def on_created(self, event):
            if event.is_directory:
                return
            
            # Watchdog sometimes fires multiple events for one file during copy operations.
            # Debounce events to allow files to write to completion safely.
            file_path = Path(event.src_path)
            
            # Skip ignored resources immediately
            if self.organizer._should_ignore(file_path):
                return

            # Wait a brief moment to ensure write handle is fully released by OS
            time.sleep(1.0)
            print_colored(f"\n[Watchdog] New file detected: {file_path.name}", Colors.BLUE)
            self.organizer.run()

    organizer = FileOrganizer(directory, verbose=True)
    import time
    
    event_handler = FolderHandler(organizer)
    observer = Observer()
    observer.schedule(event_handler, path=str(directory), recursive=False)
    
    print_colored(f"Starting Background Service on {directory}", Colors.GREEN, bold=True)
    print_colored("Active Monitoring. Press Ctrl+C to terminate the daemon.", Colors.CYAN)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_colored("\nTerminating Background Watchdog Service safely.", Colors.YELLOW)
        observer.stop()
    observer.join()


# ==============================================================================
# CLI RUNTIME PARSER ENTRYPOINT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Automated Resilient File Organization Engine."
    )
    parser.add_argument(
        "directory", 
        type=str, 
        nargs="?", 
        default=str(Path.home() / "Downloads"),
        help="Target folder path to organize (defaults to user Downloads folder)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Simulate the actions without writing modification changes to disk"
    )
    parser.add_argument(
        "--undo", 
        action="store_true", 
        help="Revert the last organization actions executed on the target directory"
    )
    parser.add_argument(
        "--watch", 
        action="store_true", 
        help="Runs an active background loop watching for incoming files to organize"
    )
    parser.add_argument(
        "--silent", 
        action="store_true", 
        help="Suppress console action feedback"
    )

    args = parser.parse_args()
    target_dir = Path(args.directory)

    if not target_dir.exists():
        print_colored(f"Error: Specified path '{target_dir}' does not exist.", Colors.RED, bold=True)
        sys.exit(1)

    if args.watch:
        start_watchdog_service(target_dir)
    else:
        organizer = FileOrganizer(target_dir, dry_run=args.dry_run, verbose=not args.silent)
        if args.undo:
            organizer.undo()
        else:
            organizer.run()


if __name__ == "__main__":
    main()
