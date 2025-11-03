import os
import re

# Path to your folder (change this to your actual path)
folder_path = "copom_texts"

# Loop through all files in the folder
for filename in os.listdir(folder_path):
    # Check for files with exactly 8 digits followed by .txt (e.g. 01092010.txt)
    match = re.match(r"(\d{2})(\d{2})(\d{4})\.txt$", filename)
    if match:
        day, month, year = match.groups()
        new_name = f"{year}{month}{day}.txt"

        # Build full paths
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_name)

        # Rename the file
        os.rename(old_path, new_path)
        print(f"Renamed: {filename} -> {new_name}")
