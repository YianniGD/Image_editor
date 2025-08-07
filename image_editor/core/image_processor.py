# image_editor/core/image_processor.py

import os
from PIL import Image, ImageFilter, ImageEnhance # Import Image, ImageFilter, and ImageEnhance from Pillow

class ImageProcessor:
    """
    Handles all core image manipulation logic.
    This class is completely independent of the GUI.
    It takes Pillow Image objects as input and returns Pillow Image objects.
    """
    def __init__(self):
        """
        Initializes the ImageProcessor.
        (Currently, no specific initialization needed, but can be extended).
        """
        pass

    def apply_blur(self, image: Image.Image, radius: float) -> Image.Image:
        """
        Applies a blur filter to the given image with a specified radius.

        Args:
            image (PIL.Image.Image): The input Pillow image.
            radius (float): The blur radius. A value of 0 means no blur.

        Returns:
            PIL.Image.Image: The blurred image.
        """
        if image and radius >= 0:
            return image.filter(ImageFilter.GaussianBlur(radius))
        return image

    def apply_sharpen(self, image: Image.Image, factor: float) -> Image.Image:
        """
        Applies a sharpen filter to the given image with a specified factor.
        Factor 1.0 is original, less than 1.0 is blurred, greater than 1.0 is sharpened.

        Args:
            image (PIL.Image.Image): The input Pillow image.
            factor (float): The sharpening factor.

        Returns:
            PIL.Image.Image: The sharpened image.
        """
        if image:
            enhancer = ImageEnhance.Sharpness(image)
            return enhancer.enhance(factor)
        return image

    def apply_grayscale(self, image: Image.Image) -> Image.Image:
        """
        Converts the given image to grayscale.

        Args:
            image (PIL.Image.Image): The input Pillow image.

        Returns:
            PIL.Image.Image: The grayscale image.
        """
        if image:
            # 'L' mode is for grayscale (luminance)
            return image.convert('L') 
        return image

    def adjust_brightness(self, image: Image.Image, factor: float) -> Image.Image:
        """
        Adjusts the brightness of the given image.
        Factor 1.0 is original, 0.0 is black, greater than 1.0 is brighter.

        Args:
            image (PIL.Image.Image): The input Pillow image.
            factor (float): The brightness factor.

        Returns:
            PIL.Image.Image: The brightness-adjusted image.
        """
        if image:
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)
        return image

    def adjust_contrast(self, image: Image.Image, factor: float) -> Image.Image:
        """
        Adjusts the contrast of the given image.
        Factor 1.0 is original, 0.0 is solid gray, greater than 1.0 is higher contrast.

        Args:
            image (PIL.Image.Image): The input Pillow image.
            factor (float): The contrast factor.

        Returns:
            PIL.Image.Image: The contrast-adjusted image.
        """
        if image:
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)
        return image

    def rotate_image(self, image: Image.Image, angle: int) -> Image.Image:
        """
        Rotates the given image by a specified angle.

        Args:
            image (PIL.Image.Image): The input Pillow image.
            angle (int): The angle in degrees to rotate counter-clockwise.

        Returns:
            PIL.Image.Image: The rotated image. `expand=True` ensures the entire
                             rotated image is visible, expanding the canvas if needed.
        """
        if image:
            return image.rotate(angle, expand=True)
        return image

    def flip_image(self, image: Image.Image, direction: str) -> Image.Image:
        """
        Flips the image horizontally or vertically.

        Args:
            image (PIL.Image.Image): The input Pillow image.
            direction (str): "horizontal" or "vertical".

        Returns:
            PIL.Image.Image: The flipped image.
        """
        if image:
            if direction == "horizontal":
                return image.transpose(Image.FLIP_LEFT_RIGHT)
            elif direction == "vertical":
                return image.transpose(Image.FLIP_TOP_BOTTOM)
        return image

    def crop_image(self, image: Image.Image, box: tuple) -> Image.Image:
        """
        Crops the image to a specified rectangular region.

        Args:
            image (PIL.Image.Image): The input Pillow image.
            box (tuple): A 4-tuple defining the left, upper, right, and lower
                         pixel coordinate.

        Returns:
            PIL.Image.Image: The cropped image.
        """
        if image and box and len(box) == 4:
            # Ensure box coordinates are within image bounds
            img_width, img_height = image.size
            left, upper, right, lower = box
            
            left = max(0, left)
            upper = max(0, upper)
            right = min(img_width, right)
            lower = min(img_height, lower)

            # Ensure valid box (right > left, lower > upper)
            if right > left and lower > upper:
                return image.crop((left, upper, right, lower))
        return image

    def resize_image(self, image: Image.Image, new_size: tuple) -> Image.Image:
        """
        Resizes the image to the specified new dimensions.

        Args:
            image (PIL.Image.Image): The input Pillow image.
            new_size (tuple): A 2-tuple (width, height) for the new size.

        Returns:
            PIL.Image.Image: The resized image.
        """
        if image and new_size and len(new_size) == 2 and new_size[0] > 0 and new_size[1] > 0:
            return image.resize(new_size, Image.LANCZOS) # LANCZOS for high quality resizing
        return image

    def batch_process_images(self, source_dir: str, dest_dir: str, percentage: float, 
                             output_format: str, quality: int, progress_callback=None) -> int:
        """
        Processes images in a source directory: resizes by percentage and converts format.

        Args:
            source_dir (str): Path to the directory containing source images.
            dest_dir (str): Path to the directory where processed images will be saved.
            percentage (float): Scale factor (e.g., 0.5 for 50%).
            output_format (str): Desired output format (e.g., "jpeg", "png", "webp").
            quality (int): Quality for lossy formats (1-100).
            progress_callback (callable, optional): A function to call with (current_file_index, total_files, filename)
                                                   for progress updates. Defaults to None.

        Returns:
            int: The number of images successfully processed.
        """
        if not os.path.isdir(source_dir) or not os.path.isdir(dest_dir):
            raise ValueError("Source or destination directory is not valid.")

        os.makedirs(dest_dir, exist_ok=True)
        # Expanded supported formats for batch input
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', # Common
                             '.psd', '.hdr', '.tga', '.xcf', '.miff', '.dcm', '.xpm', '.pcx', # Professional/Large
                             '.fits', '.ppm', '.pgm', '.pfm', '.mng', '.dds', '.otb', '.pdf', # More specialized
                             '.avif', '.heic', '.heif', # Modern (Pillow might need plugins)
                             # RAW formats are generally not directly handled by Pillow for batch processing
                             # and would require external libraries like rawpy.
                             # Listing them here means Pillow might attempt to open, but could fail or flatten.
                             '.cr2', '.rw2', '.nef', '.arw', '.sr2', '.orf', '.pef', '.raf', '.srw', '.mrw', 
                             '.dcr', '.dng', '.erf', '.3fr', '.ari', '.srf', '.bay', '.crw', '.cap', '.iiq', 
                             '.eip', '.dcs', '.drf', '.k25', '.kdc', '.fff', '.mef', '.mos', '.nrw', '.ptx', 
                             '.pxn', '.r3d', '.rwl', '.rwz', '.x3f', '.mdc'
                            )
        
        image_files = []
        for filename in os.listdir(source_dir):
            if filename.lower().endswith(supported_formats):
                image_files.append(filename)

        if not image_files:
            return 0

        total_files = len(image_files)
        processed_count = 0

        for i, filename in enumerate(image_files):
            filepath = os.path.join(source_dir, filename)
            try:
                if progress_callback:
                    progress_callback(i + 1, total_files, filename)

                with Image.open(filepath) as img:
                    # Calculate new size while maintaining aspect ratio
                    original_width, original_height = img.size
                    new_width = int(original_width * percentage)
                    new_height = int(original_height * percentage)
                    
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Prepare output filename and save
                    base_name, _ = os.path.splitext(filename)
                    output_filepath = os.path.join(dest_dir, f"{base_name}.{output_format.lower()}")
                    
                    # Handle format-specific saving
                    if output_format.lower() in ("jpeg", "webp"):
                        if resized_img.mode in ('RGBA', 'P'):
                            # Convert to RGB for formats that don't support alpha (like JPEG, WebP)
                            resized_img = resized_img.convert('RGB') 
                        resized_img.save(output_filepath, quality=quality, optimize=True)
                    else: # For PNG, BMP, GIF, TIFF, etc.
                        resized_img.save(output_filepath, optimize=True)
                processed_count += 1
            except Exception as e:
                print(f"Could not process {filename} in batch: {e}")
                # Continue to next file even if one fails
        return processed_count

    def extract_gif_frames(self, input_path: str, output_base_directory: str, 
                           is_single_file: bool = False, progress_callback=None) -> int:
        """
        Extracts all frames from GIF files (either a single file or recursively from a directory)
        and saves them as PNG images in a subfolder named after the GIF.

        Args:
            input_path (str): Path to a single GIF file or a directory containing GIF files.
            output_base_directory (str): The base path to the directory where extracted frames
                                         will be saved. A subfolder will be created for each GIF.
            is_single_file (bool): True if input_path is a single GIF file, False if it's a directory.
            progress_callback (callable, optional): A function to call with (current_gif_index, total_gifs, gif_filename, current_frame, total_frames_in_gif)
                                                   for progress updates. Defaults to None.

        Returns:
            int: The total number of frames successfully extracted.
        """
        if is_single_file:
            gif_files = [input_path]
            if not os.path.isfile(input_path) or not input_path.lower().endswith('.gif'):
                raise ValueError(f"Invalid single GIF file path: '{input_path}'")
        else:
            if not os.path.isdir(input_path):
                raise FileNotFoundError(f"Input directory '{input_path}' not found.")
            gif_files = []
            for root, _, files in os.walk(input_directory):
                for filename in files:
                    if filename.lower().endswith('.gif'):
                        gif_files.append(os.path.join(root, filename))
        
        if not gif_files:
            return 0

        os.makedirs(output_base_directory, exist_ok=True)
        total_gifs = len(gif_files)
        total_frames_extracted = 0

        for gif_idx, gif_path in enumerate(gif_files):
            try:
                gif_filename = os.path.basename(gif_path)
                gif_name_without_ext = os.path.splitext(gif_filename)[0]

                # Create a subfolder for each GIF's frames
                if is_single_file:
                    # If single file, save directly to output_base_directory
                    # or a subfolder if desired, but for now, keep it simple for single.
                    # For consistency with batch, we'll still create a subfolder.
                    output_gif_folder = os.path.join(output_base_directory, gif_name_without_ext)
                else:
                    # Mirror the directory structure for batch processing
                    relative_path = os.path.relpath(os.path.dirname(gif_path), input_path)
                    output_gif_folder = os.path.join(output_base_directory, relative_path, gif_name_without_ext)
                
                os.makedirs(output_gif_folder, exist_ok=True)

                with Image.open(gif_path) as img:
                    frame_count = 0
                    try:
                        while True:
                            img.seek(frame_count) # Go to the current frame
                            frame = img.copy() # Get a copy of the frame
                            
                            # Convert to RGBA to ensure transparency is handled correctly when saving as PNG
                            if frame.mode != 'RGBA':
                                frame = frame.convert('RGBA')

                            frame_output_path = os.path.join(output_gif_folder, f"{gif_name_without_ext}_frame_{frame_count:04d}.png")
                            frame.save(frame_output_path, "PNG")
                            
                            frame_count += 1
                            total_frames_extracted += 1
                            if progress_callback:
                                progress_callback(gif_idx + 1, total_gifs, gif_filename, frame_count, img.n_frames if hasattr(img, 'n_frames') else 'N/A')
                    except EOFError:
                        # Reached the end of frames
                        pass
            except Exception as e:
                print(f"Error processing GIF '{gif_path}': {e}")
                # Continue to next GIF even if one fails
        return total_frames_extracted

