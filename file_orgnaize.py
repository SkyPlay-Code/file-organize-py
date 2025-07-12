# ==============================================================================
# SECTION 1: IMPORTS - Getting our tools
# ==============================================================================
import os
from pathlib import Path

# ==============================================================================
# SECTION 2: CONFIGURATION - The settings you can easily change
# ==============================================================================
# Tell the script WHICH FOLDER to organize.
# Path.home() finds your main user folder (e.g., C:\Users\padma) automatically.
# The / operator is a smart way to join paths together.
TARGET_DIRECTORY = Path.home() / "Downloads"

# This is our "Rulebook". It maps folder names to the file extensions that go inside.
# We use a dictionary: the "key" is the folder name (a string), 
# and the "value" is a list of file extensions (strings).
FILE_TYPES = {
    "Images":       [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".svg", ".tiff"],
    "Documents":    [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Archives":     [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Audio":        [".mp3", ".wav", ".aac", ".flac", ".ogg", ".acc"],
    "Video":        [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "Scripts":      [".py", ".js", ".html", ".css", ".sh", ".bat"],
    "Executables":  [".exe", ".msi", ".dmg"]
}

# ==============================================================================
# SECTION 3: THE ENGINE - The main function that does all the work
# ==============================================================================
def organize_files(directory):
    """
    Scans a directory and organizes its files into subfolders based on FILE_TYPES.
    """
    print(f"--- Starting organization of: {directory} ---")

    # STEP 1: Create the category folders if they don't already exist.
    for folder_name in FILE_TYPES.keys():
        folder_path = directory / folder_name
        folder_path.mkdir(exist_ok=True) # exist_ok=True prevents an error if the folder is already there.

    # STEP 2: Loop through every single item in the target directory.
    for file_path in directory.iterdir():

        # First, we check if the item is a directory (a folder). If so, we skip it.
        # We only want to move files, not other folders.
        if file_path.is_dir():
            continue

        # This is a critical safety check. The file might be deleted by another program
        # (like a browser finishing a download) while our script is running.
        # This line ensures we don't try to move a file that no longer exists.
        if not file_path.exists():
            continue

        # We found a file! Let's get its extension (e.g., ".pdf")
        # .suffix gets the extension, and .lower() makes it lowercase (so ".JPG" and ".jpg" are treated the same).
        file_suffix = file_path.suffix.lower()

        # A flag to remember if we successfully moved the file.
        moved = False

        # STEP 3: Find a matching folder for the current file.
        # Loop through our FILE_TYPES rulebook.
        for folder_name, extensions_list in FILE_TYPES.items():
            if file_suffix in extensions_list:
                # We found a match!
                destination_folder = directory / folder_name
                destination_path = destination_folder / file_path.name

                # Now, attempt to move the file.
                # We use a `try...except` block because moving a file can fail
                # if it's open, locked by another program, or if it vanishes.
                try:
                    file_path.rename(destination_path)
                    print(f"MOVED: {file_path.name} -> {destination_folder.name}/")
                    moved = True
                except (FileNotFoundError, PermissionError) as e:
                    print(f"ERROR: Could not move '{file_path.name}'. It might be in use. Reason: {e}")
                
                # Since we found a home for it, we can stop checking other folders.
                break
        
        # STEP 4: Handle files that didn't match any category.
        if not moved:
            # Create the "Other" folder if it doesn't exist.
            other_folder = directory / "Other"
            other_folder.mkdir(exist_ok=True)
            destination_path = other_folder / file_path.name
            
            # Attempt to move the file to the "Other" folder.
            try:
                file_path.rename(destination_path)
                print(f"MOVED: {file_path.name} -> Other/")
            except (FileNotFoundError, PermissionError) as e:
                print(f"ERROR: Could not move '{file_path.name}' to Other folder. Reason: {e}")

    print("--- Organization complete! ---")


# ==============================================================================
# SECTION 4: THE START BUTTON - This makes the script run
# ==============================================================================
if __name__ == "__main__":
    # This is a safety check to make sure the folder you want to organize actually exists.
    if not TARGET_DIRECTORY.is_dir():
        print(f"FATAL ERROR: The target directory does not exist.")
        print(f"Please check the path: '{TARGET_DIRECTORY}'")
    else:
        # If the folder exists, call our main function to start the work.
        organize_files(TARGET_DIRECTORY)
