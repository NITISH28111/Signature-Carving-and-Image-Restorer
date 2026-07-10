# existing.py
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("ImageRecovery.Existing")

class ExistingImageExtractor:
    """Module for extracting existing image files"""
    
    def __init__(self):
        self.supported_extensions = ['.jpg', '.jpeg', '.png']
        self.file_count = 0
        
    def extract_images(self, source_path, output_path):
        """
        Extract existing image files from the source path to the output path
        
        Args:
            source_path: Path to scan for existing images
            output_path: Directory to copy the found images
            
        Returns:
            List of extracted file information
        """
        logger.info(f"Starting existing image extraction from {source_path}")
        self.file_count = 0
        extracted_files = []
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)
            
            # Walk through the source path
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_extension = os.path.splitext(file)[1].lower()
                    
                    # Check if it's a supported image file
                    if file_extension in self.supported_extensions:
                        try:
                            # Get file information
                            file_size = os.path.getsize(file_path)
                            
                            # Generate output filename
                            self.file_count += 1
                            output_filename = f"image_{self.file_count}{file_extension}"
                            output_file_path = os.path.join(output_path, output_filename)
                            
                            # Copy the file
                            shutil.copy2(file_path, output_file_path)
                            
                            # Add to extracted files list
                            extracted_files.append({
                                'path': output_file_path,
                                'original_path': file_path,
                                'size': file_size,
                                'type': file_extension[1:],  # Remove the dot
                                'status': 'Copied'
                            })
                            
                            logger.info(f"Copied existing file: {file_path} to {output_file_path}")
                            
                        except Exception as e:
                            logger.error(f"Error copying file {file_path}: {str(e)}")
            
            logger.info(f"Extraction complete. Extracted {len(extracted_files)} existing image files.")
            return extracted_files
            
        except Exception as e:
            logger.error(f"Error extracting existing images: {str(e)}", exc_info=True)
            return extracted_files
    
    def is_valid_image(self, file_path):
        """
        Check if a file is a valid image by attempting to open it
        
        Args:
            file_path: Path to the image file
            
        Returns:
            True if the file is a valid image, False otherwise
        """
        try:
            # Check file extension
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension not in self.supported_extensions:
                return False
                
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False
                
            # Open the file and read the first few bytes to check the signature
            with open(file_path, 'rb') as f:
                header = f.read(8)
                
                # Check for JPEG signature
                if file_extension in ['.jpg', '.jpeg']:
                    return header.startswith(b'\xFF\xD8\xFF')
                    
                # Check for PNG signature
                elif file_extension == '.png':
                    return header.startswith(b'\x89PNG\r\n\x1A\n')
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking image validity for {file_path}: {str(e)}")
            return False