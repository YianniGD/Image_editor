# image_editor/gui/batch_window.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading

from core.image_processor import ImageProcessor
from core.file_manager import FileManager # Import the new file manager

class BatchProcessorWindow(tk.Toplevel):
    """
    A separate Toplevel window for batch image processing and other file management tools.
    It now includes a Notebook with tabs for different functions.
    """
    def __init__(self, master, image_processor_instance):
        super().__init__(master)
        self.title("Batch Tools & File Management")
        self.geometry("600x700") # Increased size to fit new content
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)

        self.image_processor = image_processor_instance
        self.file_manager = FileManager() # Instantiate the new file manager

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabelFrame', background='#e0e0e0', foreground='darkblue', font=('Helvetica', 10, 'bold'))
        style.configure('TButton', font=('Helvetica', 10), padding=5)
        style.map('TButton', background=[('active', '!disabled', '#cceeff'), ('pressed', '#99ddff')])
        style.configure('TEntry', padding=3)
        style.configure('TScale', background='#e0e0e0', troughcolor='#c0c0c0')
        style.configure('TLabel', background='#e0e0e0')
        style.configure('TProgressbar', background='#4CAF50', troughcolor='#ddd')
        style.configure("Red.TCheckbutton", foreground="red", font=("Arial", 10, "bold"))
        style.configure("Green.TButton", foreground="darkgreen", font=("Arial", 10, "bold"))
        
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs for different functionalities
        self.batch_tab = ttk.Frame(self.notebook, padding=10)
        self.gif_tab = ttk.Frame(self.notebook, padding=10)
        self.file_sorter_tab = ttk.Frame(self.notebook, padding=10)
        self.duplicate_tab = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.batch_tab, text="Image Batching")
        self.notebook.add(self.gif_tab, text="GIF Extraction")
        self.notebook.add(self.file_sorter_tab, text="File Sorter")
        self.notebook.add(self.duplicate_tab, text="Duplicate Cleaner")

        self._setup_batch_tab(self.batch_tab)
        self._setup_gif_tab(self.gif_tab)
        self._setup_file_sorter_tab(self.file_sorter_tab)
        self._setup_duplicate_tab(self.duplicate_tab)

        # Centralized progress for the whole window
        self.progress_frame = ttk.Frame(self, padding=10)
        self.progress_frame.pack(fill=tk.X, pady=(0, 5))
        self.progress_label = ttk.Label(self.progress_frame, text="Ready.")
        self.progress_label.pack(fill=tk.X, pady=2)
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=2)

    # --- Setup Methods for each Tab ---

    def _setup_batch_tab(self, tab):
        # The content of the old batch processing section goes here
        batch_frame = ttk.LabelFrame(tab, text="Image Batching", padding=(10, 5))
        batch_frame.pack(fill=tk.X, pady=5)

        ttk.Label(batch_frame, text="Source Dir:").pack(anchor="w")
        self.batch_source_dir_entry = ttk.Entry(batch_frame)
        self.batch_source_dir_entry.pack(fill=tk.X, ipady=3)
        ttk.Button(batch_frame, text="Browse Source", command=self._browse_batch_source).pack(fill=tk.X, pady=2)

        ttk.Label(batch_frame, text="Destination Dir:").pack(anchor="w")
        self.batch_dest_dir_entry = ttk.Entry(batch_frame)
        self.batch_dest_dir_entry.pack(fill=tk.X, ipady=3)
        ttk.Button(batch_frame, text="Browse Destination", command=self._browse_batch_destination).pack(fill=tk.X, pady=2)

        scale_option_frame = ttk.Frame(batch_frame)
        scale_option_frame.pack(fill=tk.X, pady=2)
        ttk.Label(scale_option_frame, text="Scale (%):").pack(side=tk.LEFT)
        self.batch_percentage_entry = ttk.Entry(scale_option_frame, width=5)
        self.batch_percentage_entry.insert(0, "100")
        self.batch_percentage_entry.pack(side=tk.LEFT, padx=(0, 10))

        format_option_frame = ttk.Frame(batch_frame)
        format_option_frame.pack(fill=tk.X, pady=2)
        ttk.Label(format_option_frame, text="Format:").pack(side=tk.LEFT)
        self.batch_format_var = tk.StringVar(self)
        self.batch_format_var.set("JPEG")
        self.batch_format_menu = ttk.OptionMenu(format_option_frame, self.batch_format_var,
                                                "JPEG", "PNG", "WebP", "BMP", "GIF", "TIFF")
        self.batch_format_menu.pack(side=tk.LEFT, padx=(0, 10))

        quality_option_frame = ttk.Frame(batch_frame)
        quality_option_frame.pack(fill=tk.X, pady=2)
        ttk.Label(quality_option_frame, text="Quality:").pack(side=tk.LEFT)
        self.batch_quality_scale = ttk.Scale(quality_option_frame, from_=1, to=100, orient="horizontal", length=100)
        self.batch_quality_scale.set(85)
        self.batch_quality_scale.pack(side=tk.LEFT)
        self.batch_quality_label = ttk.Label(quality_option_frame, text=f"{int(self.batch_quality_scale.get())}")
        self.batch_quality_label.pack(side=tk.LEFT, padx=(5, 0))
        self.batch_quality_scale.bind("<Motion>", self._update_batch_quality_label)

        ttk.Button(batch_frame, text="Start Batch Process", command=self._start_batch_process).pack(fill=tk.X, pady=5)
    
    def _setup_gif_tab(self, tab):
        # The content of the old GIF extraction section goes here
        gif_extract_frame = ttk.LabelFrame(tab, text="GIF Frame Extraction", padding=(10, 5))
        gif_extract_frame.pack(fill=tk.X, pady=10)

        self.gif_mode_var = tk.StringVar(self)
        self.gif_mode_var.set("Directory") # Default to directory mode
        ttk.Radiobutton(gif_extract_frame, text="Single GIF File", variable=self.gif_mode_var, value="Single").pack(anchor="w")
        ttk.Radiobutton(gif_extract_frame, text="GIF Directory (Recursive)", variable=self.gif_mode_var, value="Directory").pack(anchor="w")

        ttk.Label(gif_extract_frame, text="Input Path:").pack(anchor="w", pady=(5,0))
        self.gif_input_path_entry = ttk.Entry(gif_extract_frame)
        self.gif_input_path_entry.pack(fill=tk.X, ipady=3)
        ttk.Button(gif_extract_frame, text="Browse Input", command=self._browse_gif_input).pack(fill=tk.X, pady=2)

        ttk.Label(gif_extract_frame, text="Output Directory:").pack(anchor="w", pady=(5,0))
        self.gif_output_dir_entry = ttk.Entry(gif_extract_frame)
        self.gif_output_dir_entry.pack(fill=tk.X, ipady=3)
        ttk.Button(gif_extract_frame, text="Browse Output", command=self._browse_gif_output).pack(fill=tk.X, pady=2)

        ttk.Button(gif_extract_frame, text="Start GIF Extraction", command=self._start_gif_extraction).pack(fill=tk.X, pady=5)

    def _setup_file_sorter_tab(self, tab):
        """Sets up the widgets for the File Sorter tab."""
        tab.columnconfigure(0, weight=0)
        tab.columnconfigure(1, weight=1)
        tab.columnconfigure(2, weight=0)
        tab.rowconfigure(7, weight=1)
        
        row_idx = 0
        tk.Label(tab, text="Source Directory:").grid(row=row_idx, column=0, sticky="w", padx=10, pady=5)
        self.sort_dir_path = tk.StringVar()
        ttk.Entry(tab, textvariable=self.sort_dir_path, width=50).grid(row=row_idx, column=1, sticky="ew", padx=10, pady=5)
        ttk.Button(tab, text="Browse", command=self._browse_sorting_directory).grid(row=row_idx, column=2, sticky="ew", padx=10, pady=5)

        row_idx += 1
        self.scan_button = ttk.Button(tab, text="Scan Extensions (Including Subfolders)", command=self._start_scan_thread)
        self.scan_button.grid(row=row_idx, column=0, columnspan=3, pady=10)

        row_idx += 1
        tk.Label(tab, text="Select File Type to Sort:").grid(row=row_idx, column=0, sticky="w", padx=10, pady=5)
        self.selected_extension = tk.StringVar()
        self.extension_options = []
        self.extension_menu = ttk.Combobox(tab, textvariable=self.selected_extension, values=self.extension_options, state="readonly")
        self.extension_menu.grid(row=row_idx, column=1, sticky="ew", padx=10, pady=5)
        self.extension_menu.set("Scan directory first...")
        self.extension_menu.config(state="disabled")

        row_idx += 1
        self.sort_button = ttk.Button(tab, text="Sort Selected Type", command=self._start_sorting_thread)
        self.sort_button.grid(row=row_idx, column=0, columnspan=3, pady=15)
        self.sort_button.config(state="disabled")

        row_idx += 1
        tk.Label(tab, text="Sorting Status:", anchor="w").grid(row=row_idx, column=0, sticky="nw", padx=10, pady=5)
        self.sort_status_text = tk.Text(tab, height=8, width=50, state="disabled", wrap=tk.WORD)
        self.sort_status_text.grid(row=row_idx, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
        self.sort_status_text_scrollbar = ttk.Scrollbar(tab, command=self.sort_status_text.yview)
        self.sort_status_text_scrollbar.grid(row=row_idx, column=3, sticky="ns", pady=5)
        self.sort_status_text.config(yscrollcommand=self.sort_status_text_scrollbar.set)
        
    def _setup_duplicate_tab(self, tab):
        """Sets up the widgets for the Duplicate Remover tab."""
        tab.columnconfigure(0, weight=0)
        tab.columnconfigure(1, weight=1)
        tab.columnconfigure(2, weight=0)
        tab.rowconfigure(7, weight=1)

        row_idx = 0
        tk.Label(tab, text="Reference Directory (Untouched):").grid(row=row_idx, column=0, sticky="w", padx=10, pady=5)
        self.ref_dir_path = tk.StringVar()
        ttk.Entry(tab, textvariable=self.ref_dir_path, width=50).grid(row=row_idx, column=1, sticky="ew", padx=10, pady=5)
        ttk.Button(tab, text="Browse", command=self._browse_reference_dir).grid(row=row_idx, column=2, sticky="ew", padx=10, pady=5)

        row_idx += 1
        tk.Label(tab, text="Check Directory (Target for Duplicates/Empty Folders):").grid(row=row_idx, column=0, sticky="w", padx=10, pady=5)
        self.check_dir_path = tk.StringVar()
        ttk.Entry(tab, textvariable=self.check_dir_path, width=50).grid(row=row_idx, column=1, sticky="ew", padx=10, pady=5)
        ttk.Button(tab, text="Browse", command=self._browse_check_dir).grid(row=row_idx, column=2, sticky="ew", padx=10, pady=5)

        row_idx += 1
        options_frame = ttk.Frame(tab)
        options_frame.grid(row=row_idx, column=0, columnspan=3, pady=5)
        self.delete_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Delete Duplicates (Files will be permanently removed)", variable=self.delete_mode,
                       style="Red.TCheckbutton").pack(anchor="w")
        ttk.Label(options_frame, text="*Uncheck for Scan Only").pack(anchor="w")

        row_idx += 1
        self.delete_empty_folders_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Delete Empty Subfolders in Check Directory (CAUTION!)", variable=self.delete_empty_folders_mode,
                       style="Red.TCheckbutton").pack(anchor="w", pady=(10, 0))
        ttk.Label(options_frame, text="*This will remove all empty folders within the 'Check Directory' selected above.").pack(anchor="w")

        row_idx += 1
        button_frame = ttk.Frame(tab)
        button_frame.grid(row=row_idx, column=0, columnspan=3, pady=10)
        self.dup_scan_button = ttk.Button(button_frame, text="Start Duplicate Scan", command=self._start_duplicate_scan_thread, width=20)
        self.dup_scan_button.pack(side=tk.LEFT, padx=10)
        self.empty_folder_button = ttk.Button(button_frame, text="Clean Empty Folders", command=self._start_empty_folder_cleanup_thread, width=20)
        self.empty_folder_button.pack(side=tk.LEFT, padx=10)
        self.clear_log_button = ttk.Button(button_frame, text="Clear Log", command=self._clear_duplicate_output, width=15)
        self.clear_log_button.pack(side=tk.LEFT, padx=10)

        row_idx += 1
        tk.Label(tab, text="Output Log:").grid(row=row_idx, column=0, sticky="w", padx=10, pady=5)
        self.duplicate_output_log = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=15, state='disabled')
        self.duplicate_output_log.grid(row=row_idx, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
        self.duplicate_output_log_scrollbar = ttk.Scrollbar(tab, command=self.duplicate_output_log.yview)
        self.duplicate_output_log_scrollbar.grid(row=row_idx, column=3, sticky="ns", pady=5)
        self.duplicate_output_log.config(yscrollcommand=self.duplicate_output_log_scrollbar.set)

    # --- Methods for Batch Image Processing Tab ---
    def _browse_batch_source(self):
        directory = filedialog.askdirectory(title="Select Source Directory for Batch Processing")
        if directory:
            self.batch_source_dir_entry.delete(0, tk.END)
            self.batch_source_dir_entry.insert(0, directory)

    def _browse_batch_destination(self):
        directory = filedialog.askdirectory(title="Select Destination Directory for Batch Processing")
        if directory:
            self.batch_dest_dir_entry.delete(0, tk.END)
            self.batch_dest_dir_entry.insert(0, directory)

    def _update_batch_quality_label(self, event):
        self.batch_quality_label.config(text=f"{int(self.batch_quality_scale.get())}")

    def _start_batch_process(self):
        source_dir = self.batch_source_dir_entry.get()
        dest_dir = self.batch_dest_dir_entry.get()
        
        if not source_dir or not dest_dir:
            messagebox.showerror("Error", "Please select both source and destination directories.")
            return
        
        try:
            percentage = float(self.batch_percentage_entry.get()) / 100
            if percentage <= 0:
                raise ValueError("Percentage must be positive.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive percentage.")
            return

        output_format = self.batch_format_var.get().lower()
        quality = int(self.batch_quality_scale.get())

        self.progress_label.config(text="Starting batch processing...")
        self.progress_bar["value"] = 0
        self.update_idletasks()

        threading.Thread(target=self._run_batch_process_threaded, args=(source_dir, dest_dir, percentage, output_format, quality), daemon=True).start()

    def _run_batch_process_threaded(self, source_dir, dest_dir, percentage, output_format, quality):
        try:
            processed_count = self.image_processor.batch_process_images(
                source_dir, dest_dir, percentage, output_format, quality,
                progress_callback=self._update_progress
            )
            self.master.after(0, lambda: messagebox.showinfo("Batch Complete", f"Successfully processed {processed_count} images."))
            self.master.after(0, lambda: self.progress_label.config(text=f"Batch processing complete. Processed {processed_count} files."))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Batch Error", f"An error occurred: {e}"))
            self.master.after(0, lambda: self.progress_label.config(text="Batch processing failed."))
        finally:
            self.master.after(0, lambda: self.progress_bar.config(value=0))

    def _update_progress(self, current: int, total: int, filename: str):
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = current
        self.progress_label.config(text=f"Processing {current}/{total}: {filename}")
        self.update_idletasks()

    # --- Methods for GIF Extraction Tab ---
    def _browse_gif_input(self):
        mode = self.gif_mode_var.get()
        if mode == "Single":
            file_path = filedialog.askopenfilename(title="Select GIF File", filetypes=[("GIF files", "*.gif")])
            if file_path:
                self.gif_input_path_entry.delete(0, tk.END)
                self.gif_input_path_entry.insert(0, file_path)
        else:
            directory = filedialog.askdirectory(title="Select GIF Source Directory")
            if directory:
                self.gif_input_path_entry.delete(0, tk.END)
                self.gif_input_path_entry.insert(0, directory)

    def _browse_gif_output(self):
        directory = filedialog.askdirectory(title="Select GIF Extraction Output Directory")
        if directory:
            self.gif_output_dir_entry.delete(0, tk.END)
            self.gif_output_dir_entry.insert(0, directory)

    def _start_gif_extraction(self):
        input_path = self.gif_input_path_entry.get()
        output_dir = self.gif_output_dir_entry.get()
        is_single_file = (self.gif_mode_var.get() == "Single")

        if not input_path or not output_dir:
            messagebox.showerror("Error", "Please select both input and output paths for GIF extraction.")
            return
        
        self.progress_label.config(text="Starting GIF extraction...")
        self.progress_bar["value"] = 0
        self.update_idletasks()
        
        threading.Thread(target=self._run_gif_extraction_threaded, args=(input_path, output_dir, is_single_file), daemon=True).start()

    def _run_gif_extraction_threaded(self, input_path, output_dir, is_single_file):
        try:
            extracted_frames_count = self.image_processor.extract_gif_frames(
                input_path, output_dir, is_single_file,
                progress_callback=self._update_gif_progress
            )
            self.master.after(0, lambda: messagebox.showinfo("GIF Extraction Complete", f"Successfully extracted {extracted_frames_count} frames."))
            self.master.after(0, lambda: self.progress_label.config(text=f"GIF extraction complete. Extracted {extracted_frames_count} frames."))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("GIF Extraction Error", f"An error occurred: {e}"))
            self.master.after(0, lambda: self.progress_label.config(text="GIF extraction failed."))
        finally:
            self.master.after(0, lambda: self.progress_bar.config(value=0))

    def _update_gif_progress(self, current_gif_idx, total_gifs, gif_filename, current_frame, total_frames_in_gif):
        self.progress_bar["maximum"] = total_gifs
        self.progress_bar["value"] = current_gif_idx
        self.progress_label.config(
            text=f"GIF {current_gif_idx}/{total_gifs}: {gif_filename} (Frame {current_frame}/{total_frames_in_gif})"
        )
        self.update_idletasks()

    # --- Methods for File Sorting Tab ---
    def _browse_sorting_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.sort_dir_path.set(directory)
            self._update_sorting_status(f"Selected directory for sorting: {directory}")
            self.extension_menu.set("Scanning...")
            self.extension_menu.config(state="disabled")
            self.sort_button.config(state="disabled")
            self.progress_bar['value'] = 0
            threading.Thread(target=self._scan_extensions_gui_threaded, daemon=True).start()

    def _update_sorting_status(self, message):
        self.sort_status_text.config(state="normal")
        self.sort_status_text.insert(tk.END, message + "\n")
        self.sort_status_text.see(tk.END)
        self.sort_status_text.config(state="disabled")
        self.update_idletasks()

    def _scan_extensions_gui_threaded(self):
        source_dir = self.sort_dir_path.get()
        try:
            unique_extensions = self.file_manager.scan_extensions(source_dir)
            self.master.after(0, self._post_scan_update_gui, unique_extensions, len(os.listdir(source_dir)))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Scan Error", f"An error occurred: {e}"))
            self.master.after(0, self._reset_sorting_buttons_on_error)

    def _post_scan_update_gui(self, unique_extensions, total_files_scanned):
        self.extension_options = unique_extensions
        if not self.extension_options:
            self.extension_menu.set("No file types found.")
            self._update_sorting_status("No files with extensions found.")
        else:
            self.extension_menu['values'] = self.extension_options
            self.extension_menu.set("Select an extension")
            self.extension_menu.config(state="readonly")
            self.sort_button.config(state="normal")
            self._update_sorting_status(f"Found {len(self.extension_options)} unique file types.")
        self.scan_button.config(state="normal")

    def _start_sorting_thread(self):
        source_dir = self.sort_dir_path.get()
        selected_ext = self.selected_extension.get()

        if not source_dir or not selected_ext or selected_ext in ["Select an extension", "No file types found."]:
            messagebox.showerror("Error", "Please select a directory and file type.")
            return

        self._update_sorting_status(f"Starting sorting for files with extension: .{selected_ext}")
        self.sort_button.config(state="disabled")
        self.scan_button.config(state="disabled")
        self.extension_menu.config(state="disabled")
        self.progress_bar['value'] = 0
        threading.Thread(target=self._sort_files_threaded, args=(source_dir, selected_ext), daemon=True).start()

    def _sort_files_threaded(self, source_dir, selected_ext):
        try:
            moved_count, skipped_count = self.file_manager.sort_files(source_dir, selected_ext, progress_callback=self._update_sorting_progress)
            self.master.after(0, lambda: messagebox.showinfo("Sorting Complete", f"Finished sorting files.\nMoved: {moved_count}\nSkipped: {skipped_count}"))
            self.master.after(0, lambda: self._update_sorting_status(f"File sorting process finished. Moved: {moved_count}, Skipped: {skipped_count}"))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Sorting Error", f"An error occurred: {e}"))
            self.master.after(0, lambda: self._update_sorting_status(f"Sorting failed: {e}"))
        finally:
            self.master.after(0, self._reset_sorting_buttons)
            self.master.after(0, lambda: self.progress_bar.config(value=0))

    def _update_sorting_progress(self, current, total, filename=None):
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar['value'] = percentage
            self.progress_label.config(text=f"Sorting {current}/{total}: {filename}")
            self.update_idletasks()

    def _reset_sorting_buttons(self):
        self.sort_button.config(state="normal")
        self.scan_button.config(state="normal")
        self.extension_menu.config(state="readonly")
        self.progress_label.config(text="Ready.")

    def _reset_sorting_buttons_on_error(self):
        self.sort_button.config(state="normal")
        self.scan_button.config(state="normal")
        if not self.extension_options:
            self.extension_menu.config(state="disabled")
            self.extension_menu.set("Scan directory first...")
        else:
            self.extension_menu.config(state="readonly")
        self.progress_label.config(text="Ready.")


    # --- Methods for Duplicate Removal Tab ---
    def _browse_reference_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.ref_dir_path.set(directory)

    def _browse_check_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.check_dir_path.set(directory)

    def _clear_duplicate_output(self):
        self.duplicate_output_log.config(state='normal')
        self.duplicate_output_log.delete(1.0, tk.END)
        self.duplicate_output_log.config(state='disabled')

    def _log_duplicate_status(self, message):
        self.duplicate_output_log.config(state="normal")
        self.duplicate_output_log.insert(tk.END, message + "\n")
        self.duplicate_output_log.see(tk.END)
        self.duplicate_output_log.config(state="disabled")
        self.update_idletasks()

    def _start_duplicate_scan_thread(self):
        ref_path = self.ref_dir_path.get()
        check_path = self.check_dir_path.get()

        if not ref_path or not check_path:
            messagebox.showerror("Input Error", "Please select both reference and check directories.")
            return
        
        is_delete_mode = self.delete_mode.get()
        self._log_duplicate_status(f"Starting duplicate scan...\nMode: {'Delete' if not is_delete_mode else 'Scan Only'}\n\n")
        self._set_duplicate_buttons_state("disabled")
        
        threading.Thread(target=self._find_duplicates_threaded, args=(ref_path, check_path, not is_delete_mode), daemon=True).start()

    def _find_duplicates_threaded(self, reference_dir, check_dir, dry_run):
        try:
            found_count, deleted_count, log_messages = self.file_manager.find_duplicates(reference_dir, check_dir, dry_run)
            self.master.after(0, lambda: self._post_duplicate_scan_update_gui(found_count, deleted_count, log_messages, dry_run))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
            self.master.after(0, self._set_duplicate_buttons_state, "normal")

    def _post_duplicate_scan_update_gui(self, found_count, deleted_count, log_messages, dry_run):
        for msg in log_messages:
            self._log_duplicate_status(msg)
        
        if dry_run:
            if found_count > 0:
                messagebox.showinfo("Scan Complete", f"Finished scanning. Found {found_count} potential duplicates. No files were deleted.")
            else:
                messagebox.showinfo("Scan Complete", "No duplicates found.")
        else:
            messagebox.showinfo("Operation Complete", f"Finished deleting duplicates.\nTotal files deleted: {deleted_count}")

        self._set_duplicate_buttons_state("normal")


    def _start_empty_folder_cleanup_thread(self):
        check_path = self.check_dir_path.get()

        if not check_path:
            messagebox.showerror("Input Error", "Please select a 'Check Directory' for empty folder cleanup.")
            return

        is_delete_mode = self.delete_empty_folders_mode.get()
        self._log_duplicate_status(f"Starting empty folder cleanup in: {check_path}\nMode: {'Delete' if not is_delete_mode else 'Scan Only'}\n\n")
        self._set_duplicate_buttons_state("disabled")

        threading.Thread(target=self._delete_empty_folders_threaded, args=(check_path, not is_delete_mode), daemon=True).start()
    
    def _delete_empty_folders_threaded(self, target_dir, dry_run):
        try:
            deleted_count, log_messages = self.file_manager.delete_empty_folders(target_dir, dry_run)
            self.master.after(0, lambda: self._post_empty_folder_cleanup_gui(deleted_count, log_messages, dry_run))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
            self.master.after(0, self._set_duplicate_buttons_state, "normal")

    def _post_empty_folder_cleanup_gui(self, deleted_count, log_messages, dry_run):
        for msg in log_messages:
            self._log_duplicate_status(msg)

        if dry_run:
            messagebox.showinfo("Scan Complete", f"Finished empty folder scan.\nFound {deleted_count} empty folders.")
        else:
            messagebox.showinfo("Operation Complete", f"Finished empty folder cleanup.\nTotal empty folders deleted: {deleted_count}")

        self._set_duplicate_buttons_state("normal")

    def _set_duplicate_buttons_state(self, state):
        for widget in [self.dup_scan_button, self.empty_folder_button, self.clear_log_button,
                       self.ref_dir_path, self.check_dir_path]:
            if isinstance(widget, (ttk.Button, ttk.Checkbutton)):
                widget.config(state=state)
            elif isinstance(widget, tk.StringVar):
                # The entries themselves need to be configured, not the StringVar
                # This is a placeholder for a more robust method of finding widgets
                pass
        
        # A more robust way to handle state is to use a master frame and configure its children
        for child in self.duplicate_tab.winfo_children():
            # Recursively find all widgets in the tab
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Checkbutton)):
                    widget.config(state=state)
