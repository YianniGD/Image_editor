# image_editor/gui/main_window.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk # Import ttk for Notebook widget and styling
from PIL import Image, ImageTk
import os # Import os for basename

from core.image_processor import ImageProcessor
from gui.widgets import ControlPanel
from gui.batch_window import BatchProcessorWindow # Import the new batch window

class ImageEditor:
    """
    The main application class for the image editor.
    Manages the overall GUI layout, image display, and orchestrates
    calls to the image processing core.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Modular Image Editor")
        self.root.geometry("1300x800") # Increased initial size for tabs and wider sidebar
        self.root.minsize(800, 600)

        # Apply a ttk theme for a modern look
        style = ttk.Style()
        style.theme_use('clam') # You can try 'alt', 'default', 'vista', 'xpnative', 'winnative'
        # Customize some common widget styles for a cleaner look
        style.configure('TLabelFrame', background='#e0e0e0', foreground='darkblue', font=('Helvetica', 10, 'bold'))
        style.configure('TButton', font=('Helvetica', 10), padding=5)
        style.map('TButton', background=[('active', '!disabled', '#cceeff'), ('pressed', '#99ddff')]) # Lighter blue on active/pressed
        style.configure('TEntry', padding=3)
        style.configure('TScale', background='#e0e0e0', troughcolor='#c0c0c0') # Background of the scale trough
        style.configure('TLabel', background='#e0e0e0') # Background for labels in control panel frames
        style.configure('TProgressbar', background='#4CAF50', troughcolor='#ddd') # Green progress bar

        # Set a background for the main root window
        self.root.configure(bg="#d0d0d0")


        # Initialize ImageProcessor
        self.image_processor = ImageProcessor()

        # --- GUI Layout ---
        self.control_frame = tk.Frame(self.root, width=300, bg="#e0e0e0", bd=2, relief=tk.RAISED)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.control_frame.pack_propagate(False) # Prevent frame from resizing to fit contents

        self.image_display_frame = tk.Frame(self.root, bg="#e0e0e0", bd=2, relief=tk.SUNKEN)
        self.image_display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Use a ttk.Notebook for tabbed interface
        self.notebook = ttk.Notebook(self.image_display_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        # Bind right-click to the notebook for tab context menu
        self.notebook.bind("<Button-3>", self._on_notebook_right_click)

        # List to store data for each open image/tab
        # Each item will be a dictionary:
        # {'original_img': PIL.Image, 'current_img': PIL.Image, 'canvas': tk.Canvas,
        #  'image_tk': ImageTk.PhotoImage, 'zoom': float, 'pan_x': int, 'pan_y': int,
        #  'last_pan_x': int, 'last_pan_y': int, 'crop_active': bool, 'crop_rect_id': int,
        #  'crop_start_x': int, 'crop_start_y': int, 'rendered_size': (w, h),
        #  'blur_radius': float, 'sharpen_factor': float, 'brightness_factor': float, 'contrast_factor': float}
        self.image_tabs_data = []
        self.active_tab_index = -1 # Index of the currently selected tab

        # Create the control panel
        self.control_panel = ControlPanel(self.control_frame, self)

        # Context menu for tabs
        self.tab_context_menu = tk.Menu(self.root, tearoff=0)
        self.tab_context_menu.add_command(label="Close Tab", command=self.close_active_tab)
        self.tab_context_menu.add_command(label="Close Other Tabs", command=self.close_other_tabs)

        # --- Menu Bar ---
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Image...", command=self.open_image)
        self.file_menu.add_command(label="Save Image", command=self.save_image, state=tk.DISABLED)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit Menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Reset All Adjustments", command=self.reset_image, state=tk.DISABLED)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Apply Grayscale", command=lambda: self.apply_filter("grayscale"), state=tk.DISABLED)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Rotate 90° CW", command=lambda: self.rotate_image(90), state=tk.DISABLED)
        self.edit_menu.add_command(label="Flip Horizontal", command=lambda: self.flip_image("horizontal"), state=tk.DISABLED)
        self.edit_menu.add_command(label="Flip Vertical", command=lambda: self.flip_image("vertical"), state=tk.DISABLED)
        self.edit_menu.add_command(label="Start Crop Tool", command=self.start_crop_tool, state=tk.DISABLED)

        # Tools Menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Batch Processing & GIF Extraction...", command=self.open_batch_window)

        # Initial state update for menu items
        self._update_menu_states()

    def _update_menu_states(self):
        """Enables/disables menu items based on whether an image is active."""
        is_image_active = self._get_active_tab_data() is not None

        # File Menu
        self.menu_bar.entryconfig("File", state=tk.NORMAL)
        self.file_menu.entryconfig("Save Image", state=tk.NORMAL if is_image_active else tk.DISABLED)

        # Edit Menu
        self.edit_menu.entryconfig("Reset All Adjustments", state=tk.NORMAL if is_image_active else tk.DISABLED)
        self.edit_menu.entryconfig("Apply Grayscale", state=tk.NORMAL if is_image_active else tk.DISABLED)
        self.edit_menu.entryconfig("Rotate 90° CW", state=tk.NORMAL if is_image_active else tk.DISABLED)
        self.edit_menu.entryconfig("Flip Horizontal", state=tk.NORMAL if is_image_active else tk.DISABLED)
        self.edit_menu.entryconfig("Flip Vertical", state=tk.NORMAL if is_image_active else tk.DISABLED)
        self.edit_menu.entryconfig("Start Crop Tool", state=tk.NORMAL if is_image_active else tk.DISABLED)

        # Control Panel sliders and buttons are handled by their own logic based on active_data
        if not is_image_active:
            self.control_panel.update_sliders_to_defaults(0.0, 1.0, 1.0, 1.0)
            self.control_panel.set_controls_state(tk.DISABLED)
        else:
            self.control_panel.set_controls_state(tk.NORMAL)


    def _get_active_tab_data(self):
        """Helper to get the data dictionary for the currently active tab."""
        if self.active_tab_index >= 0 and self.active_tab_index < len(self.image_tabs_data):
            return self.image_tabs_data[self.active_tab_index]
        return None

    def _on_tab_change(self, event):
        """Callback when the selected tab changes."""
        old_index = self.active_tab_index
        new_index = self.notebook.index(self.notebook.select())
        self.active_tab_index = new_index

        if new_index != old_index:
            active_data = self._get_active_tab_data()
            if active_data:
                # Update main app's current_image/original_image to match the new tab
                # These are used by the control panel methods directly
                self.current_image = active_data['current_img']
                self.original_image = active_data['original_img'] 
                self.display_image_tk = active_data['image_tk'] 

                # Update control panel sliders to reflect the new tab's values
                self.control_panel.update_sliders_to_defaults(
                    active_data['blur_radius'],
                    active_data['sharpen_factor'],
                    active_data['brightness_factor'],
                    active_data['contrast_factor']
                )
                # Ensure the image is displayed correctly on tab switch (e.g., if canvas size changed)
                self.display_image()
            else:
                # No image in the new tab (shouldn't happen if tabs are managed correctly)
                self.current_image = None
                self.original_image = None
                self.display_image_tk = None
                self.control_panel.update_sliders_to_defaults(0.0, 1.0, 1.0, 1.0) # Reset sliders
            
            self._update_menu_states() # Update menu states on tab change

    def _on_notebook_right_click(self, event):
        """Displays a context menu when a tab is right-clicked."""
        try:
            # Identify the tab that was right-clicked
            tab_id = self.notebook.identify(event.x, event.y)
            if tab_id:
                # Select the right-clicked tab (optional, but good UX)
                self.notebook.select(tab_id)
                # Post the context menu
                self.tab_context_menu.post(event.x_root, event.y_root)
        except tk.TclError:
            # This can happen if right-click is outside a tab area
            pass


    def open_image(self):
        """
        Opens a file dialog, loads the selected image, creates a new tab for it,
        and displays it.
        """
        # Expanded file types for opening
        filetypes = [
            ("Common Raster Images", "*.jpg *.jpeg *.png *.gif *.webp *.bmp *.ico *.jpe *.jfif *.jfi *.jif"),
            ("Advanced Raster Images", "*.avif *.heic *.heif"), # Pillow may need plugins or specific builds
            ("Professional/Large Documents", "*.psd *.hdr *.tiff *.tif *.psb *.tga *.xcf *.miff *.dcm *.xpm *.pcx *.fits *.ppm *.pgm *.pfm *.mng *.dds *.otb"),
            ("Vector/PDF (Rasterized)", "*.svg *.pdf"), # Will be rasterized by Pillow
            ("Camera RAW Formats", "*.cr2 *.rw2 *.nef *.arw *.sr2 *.orf *.pef *.raf *.srw *.mrw *.dcr *.dng *.erf *.3fr *.ari *.srf *.bay *.crw *.cap *.iiq *.eip *.dcs *.drf *.k25 *.kdc *.fff *.mef *.mos *.nrw *.ptx *.pxn *.r3d *.rwl *.rwz *.x3f *.mdc"),
            ("All Files", "*.*") # Catch-all for other types
        ]
        file_path = filedialog.askopenfilename(
            title="Open Image File",
            filetypes=filetypes
        )
        if file_path:
            try:
                pil_image = Image.open(file_path)
                file_name = os.path.basename(file_path)

                # Create a new frame for the tab content
                tab_frame = tk.Frame(self.notebook, bg="gray") # Changed to gray to match canvas
                tab_frame.pack(fill=tk.BOTH, expand=True)

                # Create a canvas within the new tab frame
                new_canvas = tk.Canvas(tab_frame, bg="gray", bd=0, highlightthickness=0)
                new_canvas.pack(fill=tk.BOTH, expand=True)

                # Store all relevant data for this new tab
                tab_data = {
                    'original_img': pil_image.copy(),
                    'current_img': pil_image.copy(),
                    'canvas': new_canvas,
                    'image_tk': None, # Will be set by display_image
                    'zoom': 1.0,
                    'pan_x': 0,
                    'pan_y': 0,
                    'last_pan_x': None, 
                    'last_pan_y': None, 
                    'crop_active': False,
                    'crop_rect_id': None,
                    'crop_start_x': None,
                    'crop_start_y': None,
                    'rendered_size': (0, 0),
                    'blur_radius': 0.0,
                    'sharpen_factor': 1.0,
                    'brightness_factor': 1.0,
                    'contrast_factor': 1.0
                }
                self.image_tabs_data.append(tab_data)

                # Add the new tab to the notebook

                self.notebook.add(tab_frame, text=file_name)
                new_tab_index = len(self.image_tabs_data) - 1
                self.notebook.select(new_tab_index) # Switch to the new tab
                self.active_tab_index = new_tab_index  # Ensure active_tab_index is set

                # Bind canvas events for zoom/pan/crop to this new canvas
                # Use lambda to pass the specific tab_data to the event handlers
                new_canvas.bind("<Configure>", lambda e, data=tab_data: self._on_canvas_resize(e, data))
                new_canvas.bind("<Control-MouseWheel>", lambda e, data=tab_data: self._on_mouse_scroll(e, data))
                new_canvas.bind("<ButtonPress-1>", lambda e, data=tab_data: self._on_pan_start(e, data))
                new_canvas.bind("<B1-Motion>", lambda e, data=tab_data: self._on_pan_drag(e, data))
                new_canvas.bind("<ButtonRelease-1>", lambda e, data=tab_data: self._on_pan_end(e, data))
                # Double-click to reset zoom/pan
                new_canvas.bind("<Double-Button-1>", lambda e, data=tab_data: self._on_double_click_reset_view(e, data))

                # Initial display for the new image
                self.display_image() # This will operate on the newly active tab
                self._update_menu_states() # Update menu states after opening image

            except Exception as e:
                messagebox.showerror("Error", f"Failed to open image: {e}\n\nNote: Some formats like Camera RAW (CR2, NEF) or advanced vectors (SVG) are not directly supported by Pillow and require specialized external libraries (e.g., rawpy for RAW, Cairo for SVG).")
                print(f"Error opening image: {e}")

    def display_image(self):
        """
        Resizes the current image of the active tab to fit its canvas,
        applies zoom/pan, converts to PhotoImage, and displays it.
        """
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['current_img']:
            return

        canvas = active_data['canvas']
        current_img = active_data['current_img']
        zoom_level = active_data['zoom']
        pan_x = active_data['pan_x']
        pan_y = active_data['pan_y']

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        if canvas_width == 0 or canvas_height == 0:
            return

        img_width, img_height = current_img.size

        # Calculate base ratio to fit image within canvas at zoom 1.0
        base_ratio = min(canvas_width / img_width, canvas_height / img_height)

        # Apply zoom to the base ratio
        display_ratio = base_ratio * zoom_level

        new_width = int(img_width * display_ratio)
        new_height = int(img_height * display_ratio)

        # Store the size of the image as it's rendered on the canvas
        active_data['rendered_size'] = (new_width, new_height)

        # Resize the image for display
        # Use LANCZOS for general photos for high quality scaling
        resized_img = current_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to Tkinter PhotoImage
        active_data['image_tk'] = ImageTk.PhotoImage(resized_img)
        
        # Clear canvas and draw the image
        canvas.delete("all")
        
        # Calculate image position with pan
        # Image is centered, then offset by pan
        img_x = (canvas_width / 2) + pan_x
        img_y = (canvas_height / 2) + pan_y

        canvas.create_image(img_x, img_y, anchor=tk.CENTER, image=active_data['image_tk'])
        # Keep a reference to prevent garbage collection
        canvas.image = active_data['image_tk']

    def _on_canvas_resize(self, event, tab_data):
        """Callback for canvas resize, specific to a tab."""
        # Update the rendered size for the specific tab
        # The display_image will be called by _on_tab_change or directly if needed
        # This ensures the image scales correctly when the window is resized.
        self.display_image()

    # --- Zoom and Pan Logic ---
    def _on_mouse_scroll(self, event, tab_data):
        """Handles Ctrl + MouseWheel for zooming."""
        if not tab_data or not tab_data['current_img']: return

        # Determine zoom direction
        if event.delta > 0: # Scroll up (zoom in)
            tab_data['zoom'] *= 1.1 # Increase zoom by 10%
        else: # Scroll down (zoom out)
            tab_data['zoom'] /= 1.1 # Decrease zoom by 10%

        # Clamp zoom level to reasonable bounds
        tab_data['zoom'] = max(0.1, min(tab_data['zoom'], 10.0)) # 0.1x to 10x zoom

        # Recalculate pan to keep the center of zoom roughly stable
        # This is a simplified approach; a more advanced one would zoom towards mouse cursor
        # For now, just reset pan to center if zoom changes
        # Keep pan relative to the image center, not absolute canvas position
        # If you want to zoom towards cursor, this logic needs to be more complex
        # For now, we'll keep the current pan offset and let the image scale around it.
        # The display_image function will handle recentering if pan_x/y are 0.

        self.display_image()

    def _on_pan_start(self, event, tab_data):
        """Records starting mouse position for panning."""
        if not tab_data or not tab_data['current_img']: return
        # Only pan if zoomed in, or if explicitly in pan mode
        if tab_data['zoom'] > 1.0: # Only pan when zoomed in
            tab_data['last_pan_x'] = event.x
            tab_data['last_pan_y'] = event.y
            tab_data['canvas'].config(cursor="fleur") # Change cursor to move icon

    def _on_pan_drag(self, event, tab_data):
        """Updates pan offset as mouse is dragged."""
        if not tab_data or not tab_data['current_img'] or tab_data['last_pan_x'] is None: return

        if tab_data['zoom'] > 1.0:
            dx = event.x - tab_data['last_pan_x']
            dy = event.y - tab_data['last_pan_y']
            
            tab_data['pan_x'] += dx
            tab_data['pan_y'] += dy

            tab_data['last_pan_x'] = event.x
            tab_data['last_pan_y'] = event.y
            
            self.display_image()

    def _on_pan_end(self, event, tab_data):
        """Resets pan state after mouse release."""
        if not tab_data: return
        tab_data['last_pan_x'] = None
        tab_data['last_pan_y'] = None
        tab_data['canvas'].config(cursor="") # Reset cursor

    def _on_double_click_reset_view(self, event, tab_data):
        """Resets zoom and pan on double-click."""
        if not tab_data or not tab_data['current_img']: return
        tab_data['zoom'] = 1.0
        tab_data['pan_x'] = 0
        tab_data['pan_y'] = 0
        self.display_image()
        messagebox.showinfo("View Reset", "Zoom and pan reset to default.")


    # --- Tab Closing Logic ---
    def close_active_tab(self):
        """Closes the currently active tab."""
        if self.active_tab_index >= 0:
            self._close_tab(self.active_tab_index)
        else:
            messagebox.showinfo("Info", "No tab is currently open to close.")

    def close_other_tabs(self):
        """Closes all tabs except the currently active one."""
        if self.active_tab_index == -1:
            messagebox.showinfo("Info", "No tabs are open.")
            return
        
        tabs_to_close = [i for i in range(len(self.image_tabs_data)) if i != self.active_tab_index]
        # Close tabs from highest index to lowest to avoid index shifting issues
        for index in sorted(tabs_to_close, reverse=True):
            self._close_tab(index)

    def _close_tab(self, index_to_close):
        """
        Internal method to close a tab by its index.
        Removes the tab from the notebook and its data from the list.
        """
        if 0 <= index_to_close < len(self.image_tabs_data):
            # Get the widget (frame) associated with the tab
            tab_widget = self.notebook.winfo_children()[index_to_close]
            
            # Remove the tab from the notebook
            self.notebook.forget(index_to_close)
            # Destroy the tab's widget to free resources
            tab_widget.destroy()
            
            # Remove the data from our list
            del self.image_tabs_data[index_to_close]

            # Adjust active_tab_index if necessary
            if len(self.image_tabs_data) == 0:
                self.active_tab_index = -1
                # Clear control panel when no tabs are open
                self.current_image = None
                self.original_image = None
                self.display_image_tk = None
                self.control_panel.update_sliders_to_defaults(0.0, 1.0, 1.0, 1.0)
            elif index_to_close <= self.active_tab_index and self.active_tab_index > 0:
                self.active_tab_index -= 1
                self.notebook.select(self.active_tab_index) # Select the new active tab
            elif len(self.image_tabs_data) > 0: # If the last tab was closed, select the new last tab
                self.notebook.select(len(self.image_tabs_data) - 1)
            
            # Manually trigger tab change to update UI if needed (notebook.select usually does this)
            self._on_tab_change(None) # Pass None for event as it's a manual trigger
            self._update_menu_states() # Update menu states after closing tab


    # --- Filter and Adjustment Methods (now operate on active tab's image) ---

    def apply_filter(self, filter_type: str):
        """
        Applies a non-dynamic filter (like grayscale) to the current image of the active tab.
        """
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['original_img']:
            messagebox.showinfo("Info", "No image loaded to apply filter.")
            return

        # Apply to a copy of the original image of the active tab
        temp_image = active_data['original_img'].copy()

        if filter_type == "grayscale":
            temp_image = self.image_processor.apply_grayscale(temp_image)
        # Add more non-dynamic filters here

        active_data['current_img'] = temp_image
        self.display_image()

    def on_blur_change(self, radius: float):
        """Callback for blur slider/input change."""
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['original_img']: return
        active_data['blur_radius'] = radius
        self._apply_all_dynamic_adjustments(active_data)

    def on_sharpen_change(self, factor: float):
        """Callback for sharpen slider/input change."""
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['original_img']: return
        active_data['sharpen_factor'] = factor
        self._apply_all_dynamic_adjustments(active_data)

    def on_brightness_change(self, factor: float):
        """Callback for brightness slider/input change."""
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['original_img']: return
        active_data['brightness_factor'] = factor
        self._apply_all_dynamic_adjustments(active_data)

    def on_contrast_change(self, factor: float):
        """Callback for contrast slider/input change."""
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['original_img']: return
        active_data['contrast_factor'] = factor
        self._apply_all_dynamic_adjustments(active_data)

    def _apply_all_dynamic_adjustments(self, tab_data):
        """
        Applies all dynamic adjustments (blur, sharpen, brightness, contrast)
        to the original image of the given tab data.
        """
        if not tab_data or not tab_data['original_img']: return

        temp_image = tab_data['original_img'].copy()
        
        temp_image = self.image_processor.apply_blur(temp_image, tab_data['blur_radius'])
        temp_image = self.image_processor.apply_sharpen(temp_image, tab_data['sharpen_factor'])
        temp_image = self.image_processor.adjust_brightness(temp_image, tab_data['brightness_factor'])
        temp_image = self.image_processor.adjust_contrast(temp_image, tab_data['contrast_factor'])
        
        tab_data['current_img'] = temp_image
        self.display_image()

    # --- Transformation Methods (now operate on active tab's image) ---

    def rotate_image(self, angle: int):
        """Rotates the current image of the active tab by the given angle."""
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['current_img']:
            messagebox.showinfo("Info", "No image loaded to rotate.")
            return
        
        active_data['current_img'] = self.image_processor.rotate_image(active_data['current_img'], angle)
        active_data['original_img'] = active_data['current_img'].copy() # Update original for sequential transforms
        self.display_image()

    def flip_image(self, direction: str):
        """Flips the current image of the active tab horizontally or vertically."""
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['current_img']:
            messagebox.showinfo("Info", "No image loaded to flip.")
            return
        
        active_data['current_img'] = self.image_processor.flip_image(active_data['current_img'], direction)
        active_data['original_img'] = active_data['current_img'].copy() # Update original for sequential transforms
        self.display_image()

    def resize_image(self, new_size: tuple):
        """Resizes the current image of the active tab to the new dimensions."""
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['current_img']:
            messagebox.showinfo("Info", "No image loaded to resize.")
            return
        try:
            if not (isinstance(new_size, tuple) and len(new_size) == 2 and
                    isinstance(new_size[0], int) and isinstance(new_size[1], int) and
                    new_size[0] > 0 and new_size[1] > 0):
                raise ValueError("New size must be a tuple of two positive integers (width, height).")

            active_data['current_img'] = self.image_processor.resize_image(active_data['current_img'], new_size)
            active_data['original_img'] = active_data['current_img'].copy() # Update original for sequential transforms
            self.display_image()
        except ValueError as e:
            messagebox.showerror("Resize Error", str(e))
        except Exception as e:
            messagebox.showerror("Resize Error", f"An unexpected error occurred during resize: {e}")

    def reset_image(self):
        """
        Resets the current image of the active tab to its original loaded state.
        Also resets all dynamic adjustment sliders to their default values.
        """
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['original_img']:
            messagebox.showinfo("Info", "No image loaded to reset.")
            return

        active_data['current_img'] = active_data['original_img'].copy()
        # Reset dynamic adjustment values for this tab
        active_data['blur_radius'] = 0.0
        active_data['sharpen_factor'] = 1.0
        active_data['brightness_factor'] = 1.0
        active_data['contrast_factor'] = 1.0
        active_data['zoom'] = 1.0
        active_data['pan_x'] = 0
        active_data['pan_y'] = 0

        # Update the UI sliders to reflect these default values
        self.control_panel.update_sliders_to_defaults(
            active_data['blur_radius'],
            active_data['sharpen_factor'],
            active_data['brightness_factor'],
            active_data['contrast_factor']
        )
        self.display_image()

    def save_image(self):
        """
        Saves the current image of the active tab to a file.
        """
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['current_img']:
            messagebox.showinfo("Info", "No image to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"),
                       ("JPEG files", "*.jpg"),
                       ("BMP files", "*.bmp"),
                       ("GIF files", "*.gif"),
                       ("TIFF files", "*.tif *.tiff"),
                       ("WebP files", "*.webp"),
                       ("All files", "*.*")],
            title="Save Image As"
        )
        if file_path:
            try:
                active_data['current_img'].save(file_path)
                messagebox.showinfo("Success", f"Image saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")
                print(f"Error saving image: {e}")

    # --- Cropping Tool Logic (now operates on active tab's image) ---
    def start_crop_tool(self):
        """Activates the cropping tool for the active tab."""
        active_data = self._get_active_tab_data()
        if not active_data or not active_data['current_img']:
            messagebox.showinfo("Info", "No image loaded to crop.")
            return
        
        messagebox.showinfo("Crop Tool", "Click and drag on the image to select a crop area. Release the mouse to apply.")
        active_data['crop_active'] = True
        active_data['canvas'].config(cursor="crosshair")
        # Ensure these are bound to the specific canvas of the active tab
        active_data['canvas'].bind("<ButtonPress-1>", lambda e: self._on_crop_press(e, active_data))
        active_data['canvas'].bind("<B1-Motion>", lambda e: self._on_crop_drag(e, active_data))
        active_data['canvas'].bind("<ButtonRelease-1>", lambda e: self._on_crop_release(e, active_data))
        
        if active_data['crop_rect_id']:
            active_data['canvas'].delete(active_data['crop_rect_id'])
            active_data['crop_rect_id'] = None

    def _on_crop_press(self, event, tab_data):
        """Records the starting point of the crop selection."""
        if tab_data['crop_active']:
            tab_data['crop_start_x'] = tab_data['canvas'].canvasx(event.x)
            tab_data['crop_start_y'] = tab_data['canvas'].canvasy(event.y)
            if tab_data['crop_rect_id']:
                tab_data['canvas'].delete(tab_data['crop_rect_id'])
            tab_data['crop_rect_id'] = None

    def _on_crop_drag(self, event, tab_data):
        """Draws or updates the crop selection rectangle."""
        if tab_data['crop_active'] and tab_data['crop_start_x'] is not None:
            cur_x = tab_data['canvas'].canvasx(event.x)
            cur_y = tab_data['canvas'].canvasy(event.y)

            if tab_data['crop_rect_id']:
                tab_data['canvas'].coords(tab_data['crop_rect_id'], tab_data['crop_start_x'], tab_data['crop_start_y'], cur_x, cur_y)
            else:
                tab_data['crop_rect_id'] = tab_data['canvas'].create_rectangle(
                    tab_data['crop_start_x'], tab_data['crop_start_y'], cur_x, cur_y,
                    outline="blue", width=2, dash=(5, 2)
                )

    def _on_crop_release(self, event, tab_data):
        """Performs the crop operation based on the selected rectangle."""
        if tab_data['crop_active'] and tab_data['crop_start_x'] is not None:
            end_x = tab_data['canvas'].canvasx(event.x)
            end_y = tab_data['canvas'].canvasy(event.y)

            canvas_center_x = tab_data['canvas'].winfo_width() / 2
            canvas_center_y = tab_data['canvas'].winfo_height() / 2
            rendered_img_width, rendered_img_height = tab_data['rendered_size']
            
            img_canvas_x1 = canvas_center_x - (rendered_img_width / 2)
            img_canvas_y1 = canvas_center_y - (rendered_img_height / 2)

            original_img_width, original_img_height = tab_data['original_img'].size
            scale_x = original_img_width / rendered_img_width if rendered_img_width > 0 else 1
            scale_y = original_img_height / rendered_img_height if rendered_img_height > 0 else 1

            x1_crop_canvas = min(tab_data['crop_start_x'], end_x)
            y1_crop_canvas = min(tab_data['crop_start_y'], end_y)
            x2_crop_canvas = max(tab_data['crop_start_x'], end_x)
            y2_crop_canvas = max(tab_data['crop_start_y'], end_y)

            crop_left = int((x1_crop_canvas - img_canvas_x1) * scale_x)
            crop_upper = int((y1_crop_canvas - img_canvas_y1) * scale_y)
            crop_right = int((x2_crop_canvas - img_canvas_x1) * scale_x)
            crop_lower = int((y2_crop_canvas - img_canvas_y1) * scale_y)
            
            crop_left = max(0, crop_left)
            crop_upper = max(0, crop_upper)
            crop_right = min(original_img_width, crop_right)
            crop_lower = min(original_img_height, crop_lower)

            if crop_right > crop_left and crop_lower > crop_upper:
                tab_data['current_img'] = self.image_processor.crop_image(tab_data['original_img'].copy(), 
                                                                    (crop_left, crop_upper, crop_right, crop_lower))
                tab_data['original_img'] = tab_data['current_img'].copy()
                self.display_image()
            else:
                messagebox.showinfo("Crop Info", "Invalid crop area selected or no area selected.")

            tab_data['canvas'].delete(tab_data['crop_rect_id'])
            tab_data['crop_rect_id'] = None
            tab_data['crop_start_x'] = None
            tab_data['crop_start_y'] = None
            tab_data['crop_active'] = False
            tab_data['canvas'].config(cursor="")
            # Unbind mouse events specific to this canvas to prevent conflicts
            tab_data['canvas'].unbind("<ButtonPress-1>")
            tab_data['canvas'].unbind("<B1-Motion>")
            tab_data['canvas'].unbind("<ButtonRelease-1>")

    # --- Batch Processing ---
    def start_batch_processing(self, source_dir: str, dest_dir: str, percentage: float, output_format: str, quality: int):
        """
        Initiates batch processing, updating the UI with progress.
        """
        # This method is now called by BatchProcessorWindow, so it needs to update that window's progress.
        # It no longer directly accesses self.control_panel for progress.
        # Instead, it relies on the progress_callback passed from BatchProcessorWindow.
        
        # We need a reference to the batch window's progress widgets.
        # A simpler way is to pass the update function from BatchProcessorWindow directly to image_processor.
        # For now, we'll assume the calls from BatchProcessorWindow will handle their own UI updates.
        # This method's logic is primarily for the core operation.
        try:
            processed_count = self.image_processor.batch_process_images(
                source_dir, dest_dir, percentage, output_format, quality,
                progress_callback=None # Progress is handled by BatchProcessorWindow directly
            )
            return processed_count # Return count for BatchProcessorWindow to display
        except Exception as e:
            raise e # Re-raise for BatchProcessorWindow to catch and display error

    # --- GIF Extraction ---
    def start_gif_extraction(self, input_path: str, output_dir: str, is_single_file: bool):
        """
        Initiates GIF frame extraction, updating the UI with progress.
        """
        # Similar to batch_processing, this is called by BatchProcessorWindow.
        # Progress is handled by BatchProcessorWindow directly.
        try:
            extracted_frames_count = self.image_processor.extract_gif_frames(
                input_path, output_dir, is_single_file,
                progress_callback=None # Progress is handled by BatchProcessorWindow directly
            )
            return extracted_frames_count # Return count for BatchProcessorWindow to display
        except Exception as e:
            raise e # Re-raise for BatchProcessorWindow to catch and display error

    def open_batch_window(self):
        """Opens the separate batch processing window."""
        # Check if a batch window is already open
        if hasattr(self, '_batch_window') and self._batch_window.winfo_exists():
            self._batch_window.lift() # Bring it to front
            return
        
        self._batch_window = BatchProcessorWindow(self.root, self.image_processor)
        # When the batch window closes, ensure it's unreferenced
        self.root.wait_window(self._batch_window)
        # After the window closes, you might want to refresh something in the main app
        # For now, no specific action is needed here

