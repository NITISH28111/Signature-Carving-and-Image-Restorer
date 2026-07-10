# verifier.py
import os
import hashlib
import logging
import shutil
from PIL import Image

logger = logging.getLogger("ImageRecovery.Verifier")

class FileIntegrityVerifier:
    """Module for verifying the integrity of recovered image files"""
    
    def __init__(self):
        self.corrupted_count = 0
        
    def verify_files(self, file_list, corrupted_dir):
        """
        Verify the integrity of image files
        
        Args:
            file_list: List of file information dictionaries
            corrupted_dir: Directory to move corrupted files to
            
        Returns:
            Updated list of file information with integrity status
        """
        logger.info(f"Starting verification of {len(file_list)} files")
        self.corrupted_count = 0
        verified_files = []
        
        try:
            # Create corrupted files directory if it doesn't exist
            os.makedirs(corrupted_dir, exist_ok=True)
            
            for file_info in file_list:
                file_path = file_info['path']
                
                if not os.path.exists(file_path):
                    logger.warning(f"File does not exist: {file_path}")
                    file_info['status'] = 'Missing'
                    verified_files.append(file_info)
                    continue
                    
                # Calculate file hash
                file_hash = self._calculate_file_hash(file_path)
                file_info['hash'] = file_hash
                
                # Check if the file is a valid image
                is_valid = self._verify_image_integrity(file_path, file_info['type'])
                
                if is_valid:
                    file_info['status'] = 'OK'
                else:
                    # Move to corrupted files directory
                    self.corrupted_count += 1
                    corrupted_filename = f"corrupted_{self.corrupted_count}_{os.path.basename(file_path)}"
                    corrupted_path = os.path.join(corrupted_dir, corrupted_filename)
                    
                    try:
                        shutil.move(file_path, corrupted_path)
                        file_info['path'] = corrupted_path
                        file_info['status'] = 'Corrupted'
                        logger.warning(f"Moved corrupted file to: {corrupted_path}")
                    except Exception as e:
                        logger.error(f"Error moving corrupted file: {str(e)}")
                        file_info['status'] = 'Corrupted (not moved)'
                
                verified_files.append(file_info)
                
            logger.info(f"Verification complete. {len([f for f in verified_files if f['status'] == 'OK'])} OK, "
                      f"{len([f for f in verified_files if 'Corrupted' in f['status']])} corrupted")
            return verified_files
            
        except Exception as e:
            logger.error(f"Error verifying files: {str(e)}", exc_info=True)
            return file_list
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA-256 hash of a file"""
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                # Read the file in chunks
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
                    
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return "hash_error"
    
    def _verify_image_integrity(self, file_path, file_type):
        """
        Verify that a file is a valid image
        
        Args:
            file_path: Path to the image file
            file_type: Type of the image (jpg, png)
            
        Returns:
            True if the file is a valid image, False otherwise
        """
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.warning(f"Empty file: {file_path}")
                return False
                
            # Attempt to open and verify the image using PIL
            img = Image.open(file_path)
            img.verify()  # This will raise an exception if the file is not a valid image
            
            # Additional checks for corruption
            width, height = img.size
            if width <= 0 or height <= 0 or width > 10000 or height > 10000:
                logger.warning(f"Invalid image dimensions: {width}x{height} for {file_path}")
                return False
                
            # Check for expected format
            if file_type == 'jpg' and img.format not in ['JPEG', 'JPG']:
                logger.warning(f"File extension mismatch: {file_path} is not a JPEG")
                return False
                
            if file_type == 'png' and img.format != 'PNG':
                logger.warning(f"File extension mismatch: {file_path} is not a PNG")
                return False
                
            return True
            
        except Exception as e:
            logger.warning(f"Invalid image file {file_path}: {str(e)}")
            return False