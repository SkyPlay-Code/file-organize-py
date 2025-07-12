import os
from pathlib import Path

TARGET_DIRECTORY = Path.home() / "Downloads"

FILE_TYPES = {
    "Images":       [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".svg", ".tiff"],
    "Documents":    [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Archives":     [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Audio":        [".mp3", ".wav", ".aac", ".flac", ".ogg", ".acc"],
    "Video":        [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "Scripts":      [".py", ".js", ".html", ".css", ".sh", ".bat"],
    "Executables":  [".exe", ".msi", ".dmg"]
}

def organize_files(directory):
    """Scans a directory and organize its files into subdirectories based on their file types."""
    print(f"Organizing files in {directory}...")

    for folder_name in FILE_TYPES.keys():
        folder_path = directory / folder_name
        folder_path.mkdir(exist_ok=True)

    for file_path in directory.iterdir():
        if file_path.is_dir():
            continue
        if not file_path.exists():
            continue

        file_suffix = file_path.suffix.lower()

        moved = False

        for folder_name, extensions_list in FILE_TYPES.items():
            if file_suffix in extensions_list:
                destination_folder = directory / folder_name
                destiantion_path = destination_folder / file_path.name


                try:
                    file_path.rename(destination_folder)
                    print(f"MOVED: {file_path.name} -> {destiantion_path.name}/")
                    moved = True
                except (FileNotFoundError, PermissionError) as e:
                    print(f"ERROR: Could not move '{file_path.name}'. It might be in use. Reason: {e}")
                break

        if not moved:
            other_folder = directory / "Other"
            other_folder.mkdir(exist_ok=True)
            destination_path = other_folder / file_path.name

            try:
                file_path.rename(destination_path)
                print(f"MOVED: {file_path.name} -> Other/")
            except (FileNotFoundError, PermissionError) as e:
                print(f"ERROR: Could not move '{file_path.name}' to Other folder. Reason: {e}")
                
    print("---Orgranization Complete---")

if __name__ == "__main__":
    if not TARGET_DIRECTORY.is_dir():
        print(f"FATAL ERROR: The target directory does not exist.")
        print(f"Please check the path: '{TARGET_DIRECTORY}'")
    else:
        organize_files(TARGET_DIRECTORY)