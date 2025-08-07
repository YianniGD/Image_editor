# image_editor/core/file_manager.py

import os
import shutil
import hashlib

class FileManager:
    """
    Handles file system operations like sorting, duplicate removal,
    and empty folder cleanup. This class is independent of the GUI.
    """
    def __init__(self):
        pass

    def scan_extensions(self, source_dir: str) -> set:
        """
        Scans a directory and its subfolders for all unique file extensions.

        Args:
            source_dir (str): The path to the directory to scan.

        Returns:
            set: A set of unique file extensions found.
        """
        unique_extensions = set()
        for root, _, files in os.walk(source_dir):
            for file_name in files:
                _, file_extension = os.path.splitext(file_name)
                file_extension = file_extension.lstrip('.').lower()
                if not file_extension:
                    unique_extensions.add("no_extension")
                else:
                    unique_extensions.add(file_extension)
        return sorted(list(unique_extensions))

    def sort_files(self, source_dir: str, selected_ext: str, progress_callback=None) -> tuple:
        """
        Recursively sorts files of a selected extension into a new folder.

        Args:
            source_dir (str): The directory containing the files to sort.
            selected_ext (str): The file extension to sort (e.g., 'jpg', 'no_extension').
            progress_callback (callable, optional): A function to call with (current, total, filename).
        
        Returns:
            tuple: A tuple (moved_count, skipped_count).
        """
        if selected_ext == "no_extension":
            destination_folder_name = "no_extension"
        else:
            destination_folder_name = f"{selected_ext}_files"
        destination_folder = os.path.join(source_dir, destination_folder_name)

        os.makedirs(destination_folder, exist_ok=True)

        files_to_move_info = []
        for root, _, files in os.walk(source_dir):
            if os.path.abspath(root) == os.path.abspath(destination_folder):
                continue
            for file_name in files:
                full_original_path = os.path.join(root, file_name)
                _, file_extension = os.path.splitext(file_name)
                file_extension = file_extension.lstrip('.').lower()

                if (selected_ext == "no_extension" and not file_extension) or \
                   (selected_ext != "no_extension" and file_extension == selected_ext):
                    files_to_move_info.append((full_original_path, file_name))
        
        total_files = len(files_to_move_info)
        moved_count = 0
        skipped_count = 0
        
        for i, (original_full_path, file_name_only) in enumerate(files_to_move_info):
            if progress_callback:
                progress_callback(i + 1, total_files, file_name_only)
            
            try:
                unique_filename = self._get_unique_filename(destination_folder, file_name_only)
                destination_path = os.path.join(destination_folder, unique_filename)
                shutil.move(original_full_path, destination_path)
                moved_count += 1
            except Exception as e:
                print(f"Error moving '{file_name_only}': {e}")
                skipped_count += 1
        
        return moved_count, skipped_count

    def _get_unique_filename(self, destination_folder, original_filename):
        """
        Generates a unique filename by appending a recursive number if a duplicate exists.
        e.g., file.txt -> file(1).txt -> file(2).txt
        """
        base_name, extension = os.path.splitext(original_filename)
        counter = 0
        new_filename = original_filename
        while os.path.exists(os.path.join(destination_folder, new_filename)):
            counter += 1
            new_filename = f"{base_name}({counter}){extension}"
        return new_filename

    def find_duplicates(self, reference_dir: str, check_dir: str, dry_run: bool) -> tuple:
        """
        Finds and optionally deletes files in check_dir that are duplicates of files in reference_dir.
        Compares by filename and file hash for accuracy.

        Args:
            reference_dir (str): Directory containing the files to keep.
            check_dir (str): Directory to scan for duplicates.
            dry_run (bool): If True, only scans and logs. If False, deletes files.
        
        Returns:
            tuple: A tuple (found_count, deleted_count, log_messages).
        """
        log_messages = []
        def log(msg):
            log_messages.append(msg)

        log("Starting duplicate scan...")
        
        log(f"Indexing files in reference directory: '{reference_dir}'...")
        reference_hashes = {}
        for root, _, files in os.walk(reference_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        reference_hashes[file_hash] = filename
                except Exception as e:
                    log(f"Error reading file '{filepath}': {e}")

        log(f"Indexing complete. Found {len(reference_hashes)} unique files in reference.")
        log(f"\nChecking for exact file duplicates in directory: '{check_dir}'...")
        
        found_count = 0
        deleted_count = 0

        for root, _, files in os.walk(check_dir):
            for filename in files:
                filepath_to_check = os.path.join(root, filename)
                try:
                    with open(filepath_to_check, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        if file_hash in reference_hashes:
                            found_count += 1
                            log(f"Duplicate found: '{filepath_to_check}' (matches '{reference_hashes[file_hash]}')")
                            if not dry_run:
                                os.remove(filepath_to_check)
                                log(f"Deleted: '{filepath_to_check}'")
                                deleted_count += 1
                except Exception as e:
                    log(f"Error checking file '{filepath_to_check}': {e}")
        
        return found_count, deleted_count, log_messages

    def delete_empty_folders(self, target_dir: str, dry_run: bool) -> tuple:
        """
        Recursively deletes empty folders in a target directory.

        Args:
            target_dir (str): The directory to clean up.
            dry_run (bool): If True, only scans and logs. If False, deletes folders.

        Returns:
            tuple: A tuple (deleted_count, log_messages).
        """
        log_messages = []
        def log(msg):
            log_messages.append(msg)
            
        log("Starting empty folder cleanup...")
        
        deleted_count = 0
        for dirpath, dirnames, filenames in os.walk(target_dir, topdown=False):
            if dirpath == target_dir:
                continue

            try:
                if not os.listdir(dirpath):
                    if dry_run:
                        log(f"Found empty folder (will not delete in dry run): '{dirpath}'")
                    else:
                        os.rmdir(dirpath)
                        log(f"Deleted empty folder: '{dirpath}'")
                    deleted_count += 1
            except Exception as e:
                log(f"Error accessing or deleting folder '{dirpath}': {e}")
        
        return deleted_count, log_messages

