# image_editor/gui/widgets.py

import tkinter as tk
from tkinter import ttk # ttk provides themed widgets, which look more modern
from tkinter import messagebox # For displaying messages

class SliderInput(tk.Frame):
    """
    A custom widget combining a label, a slider (ttk.Scale), and an entry field (ttk.Entry)
    for dynamic adjustment of numerical attributes.
    """
    def __init__(self, master, label_text, from_, to_, resolution, default_value, command_callback):
        """
        Initializes the SliderInput widget.

        Args:
            master (tk.Widget): The parent widget.
            label_text (str): Text for the label (e.g., "Blur Radius:").
            from_ (float): The minimum value for the slider.
            to_ (float): The maximum value for the slider.
            resolution (float): The step size for the DoubleVar (not directly for ttk.Scale).
            default_value (float): The initial value for the slider and entry.
            command_callback (callable): A function to call when the slider or entry value changes.
                                         It will receive the new float value as an argument.
        """
        # Corrected: Removed bg=master.cget('bg') as ttk widgets don't directly support it.
        # tk.Frame will default to a transparent background, inheriting from its parent.
        super().__init__(master) 
        self.pack(fill=tk.X, pady=2)

        self.command_callback = command_callback
        self.value_var = tk.DoubleVar(value=default_value) # Use DoubleVar for float values

        # Store default value for resetting
        self.default_value = default_value

        # Label
        ttk.Label(self, text=label_text).pack(side=tk.LEFT, padx=(0, 5))

        # Entry for numerical input
        self.entry = ttk.Entry(self, textvariable=self.value_var, width=8)
        self.entry.pack(side=tk.RIGHT, padx=(5, 0))
        # Bind <Return> key to update slider when user presses Enter in the entry field
        self.entry.bind("<Return>", self._on_entry_change)
        # Bind focus out to update slider when user clicks away from the entry field
        self.entry.bind("<FocusOut>", self._on_entry_change)

        # Slider
        # Corrected: Removed 'resolution=resolution' as ttk.Scale does not accept this option.
        # The DoubleVar handles the precision.
        self.slider = ttk.Scale(self, from_=from_, to=to_,
                                orient=tk.HORIZONTAL, variable=self.value_var,
                                command=self._on_slider_change)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _on_slider_change(self, value):
        """Callback when slider is dragged."""
        # The value is already updated in self.value_var by the slider's variable binding
        try:
            float_val = float(value)
            self.command_callback(float_val)
        except ValueError:
            # Handle cases where slider value might be malformed (shouldn't happen with ttk.Scale)
            pass

    def _on_entry_change(self, event=None):
        """Callback when entry field content changes (on Enter or FocusOut)."""
        try:
            # Attempt to get the value from the entry and convert to float
            new_value = float(self.entry.get())
            # Ensure the value is within the slider's defined range
            if new_value < self.slider.cget('from'):
                new_value = self.slider.cget('from')
                self.value_var.set(new_value) # Update variable and entry
            elif new_value > self.slider.cget('to'):
                new_value = self.slider.cget('to')
                self.value_var.set(new_value) # Update variable and entry
            
            self.command_callback(new_value)
        except ValueError:
            # If the entry content is not a valid number, revert to the last valid value
            messagebox.showerror("Invalid Input", "Please enter a valid number.")
            self.value_var.set(self.slider.get()) # Revert entry to current slider value

    def set_value(self, value):
        """Sets the value of the slider and entry programmatically."""
        self.value_var.set(value)


class ControlPanel(tk.Frame):
    """
    A custom widget class for the control panel, containing buttons
    and sliders for various image editing operations.
    """
    def __init__(self, master, app_instance):
        """
        Initializes the ControlPanel.

        Args:
            master (tk.Widget): The parent widget (e.g., a tk.Frame).
            app_instance (ImageEditor): The main ImageEditor application instance,
                                        used to call its methods.
        """
        # Corrected: Removed bg=master.cget('bg') from here.
        # tk.Frame will now correctly inherit its background from its ttk.LabelFrame parent.
        super().__init__(master) 
        self.pack(fill=tk.BOTH, expand=True) # Pack itself into the master frame

        self.app = app_instance # Store reference to the main app instance
        self.slider_inputs = {} # Dictionary to store references to SliderInput widgets

        # --- File Operations ---
        file_frame = ttk.LabelFrame(self, text="File Operations", padding=(10, 5))
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Button(file_frame, text="Open Image", command=self.app.open_image).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Save Image", command=self.app.save_image).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Reset All", command=self.app.reset_image).pack(fill=tk.X, pady=2)
        # Added a button to close the active tab
        ttk.Button(file_frame, text="Close Active Tab", command=self.app.close_active_tab).pack(fill=tk.X, pady=2)


        # --- Filters with Sliders ---
        filter_frame = ttk.LabelFrame(self, text="Filters & Adjustments", padding=(10, 5))
        filter_frame.pack(fill=tk.X, pady=5)

        # Blur Slider
        self.slider_inputs["blur"] = SliderInput(filter_frame, "Blur Radius:", 0.0, 10.0, 0.1, 0.0, self.app.on_blur_change)
        # Sharpen Slider
        self.slider_inputs["sharpen"] = SliderInput(filter_frame, "Sharpen Factor:", 0.0, 5.0, 0.1, 1.0, self.app.on_sharpen_change)
        # Brightness Slider
        self.slider_inputs["brightness"] = SliderInput(filter_frame, "Brightness Factor:", 0.0, 3.0, 0.01, 1.0, self.app.on_brightness_change)
        # Contrast Slider
        self.slider_inputs["contrast"] = SliderInput(filter_frame, "Contrast Factor:", 0.0, 3.0, 0.01, 1.0, self.app.on_contrast_change)
        
        # Grayscale button (no slider needed)
        ttk.Button(filter_frame, text="Apply Grayscale", command=lambda: self.app.apply_filter("grayscale")).pack(fill=tk.X, pady=2)

        # --- Transformations ---
        transform_frame = ttk.LabelFrame(self, text="Transformations", padding=(10, 5))
        transform_frame.pack(fill=tk.X, pady=5)

        ttk.Button(transform_frame, text="Rotate 90° CW", command=lambda: self.app.rotate_image(90)).pack(fill=tk.X, pady=2)
        ttk.Button(transform_frame, text="Flip Horizontal", command=lambda: self.app.flip_image("horizontal")).pack(fill=tk.X, pady=2)
        ttk.Button(transform_frame, text="Flip Vertical", command=lambda: self.app.flip_image("vertical")).pack(fill=tk.X, pady=2)

        # Resize Inputs
        resize_frame = ttk.Frame(transform_frame)
        resize_frame.pack(fill=tk.X, pady=2)
        ttk.Label(resize_frame, text="New Width:").pack(side=tk.LEFT)
        self.new_width_entry = ttk.Entry(resize_frame, width=8)
        self.new_width_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(resize_frame, text="New Height:").pack(side=tk.LEFT)
        self.new_height_entry = ttk.Entry(resize_frame, width=8)
        self.new_height_entry.pack(side=tk.LEFT)
        ttk.Button(transform_frame, text="Apply Resize", command=self._apply_resize).pack(fill=tk.X, pady=2)

        # Cropping Tool Button
        ttk.Button(transform_frame, text="Start Crop", command=self.app.start_crop_tool).pack(fill=tk.X, pady=2)

        # --- Batch Tools Button (moved from its own section) ---
        tools_frame = ttk.LabelFrame(self, text="Tools", padding=(10, 5))
        tools_frame.pack(fill=tk.X, pady=5)
        ttk.Button(tools_frame, text="Open Batch Tools", command=self.app.open_batch_window).pack(fill=tk.X, pady=2)

    def _apply_resize(self):
        """
        Retrieves values from resize entry fields and calls the app's resize method.
        """
        try:
            new_width = int(self.new_width_entry.get())
            new_height = int(self.new_height_entry.get())
            if new_width > 0 and new_height > 0:
                self.app.resize_image((new_width, new_height))
            else:
                messagebox.showerror("Invalid Input", "Width and Height must be positive integers.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integer values for width and height.")

    def update_sliders_to_defaults(self, blur_val, sharpen_val, brightness_val, contrast_val):
        """
        Updates the values of the dynamic adjustment sliders to specified defaults.
        This is called by the main app when an image is loaded or reset.
        """
        self.slider_inputs["blur"].set_value(blur_val)
        self.slider_inputs["sharpen"].set_value(sharpen_val)
        self.slider_inputs["brightness"].set_value(brightness_val)
        self.slider_inputs["contrast"].set_value(contrast_val)

    def set_controls_state(self, state):
        """
        Sets the state (NORMAL or DISABLED) of all controls in the ControlPanel.
        """
        for slider_input in self.slider_inputs.values():
            slider_input.slider.config(state=state)
            slider_input.entry.config(state=state)
        
        # Disable/Enable other buttons and entries in the control panel
        # File operations are typically always enabled, except Save/Reset
        # which are handled by the main_window's _update_menu_states.
        # Here we focus on the transformation and filter buttons/entries.
        
        # Transformation buttons
        for child in self.winfo_children(): # Iterate through top-level frames in ControlPanel
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Transformations":
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Button):
                        widget.config(state=state)
                    elif isinstance(widget, ttk.Frame): # Resize inputs frame
                        for entry_widget in widget.winfo_children():
                            if isinstance(entry_widget, ttk.Entry):
                                entry_widget.config(state=state)
                break # Found the transformations frame, exit loop

        # Grayscale button
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "Filters & Adjustments":
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Button) and widget.cget("text") == "Apply Grayscale":
                        widget.config(state=state)
                        break
                break
        
        # Batch tools button is always active to open the window
        # No need to disable it here.
