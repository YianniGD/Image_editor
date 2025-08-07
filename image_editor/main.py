# image_editor/main.py

import tkinter as tk
from gui.main_window import ImageEditor

def main():
    """
    Main function to initialize and run the image editor application.
    This is the entry point of the entire program.
    """
    # Create the main Tkinter window (root window)
    root = tk.Tk()
    
    # Create an instance of the ImageEditor application
    # The ImageEditor class will handle all GUI elements and logic.
    app = ImageEditor(root)
    
    # Start the Tkinter event loop.
    # This keeps the application running, listening for user interactions
    # (like button clicks, window resizing, etc.) until the window is closed.
    root.mainloop()

if __name__ == "__main__":
    # This ensures that the main() function is called only when the script
    # is executed directly (not when imported as a module).
    main()

