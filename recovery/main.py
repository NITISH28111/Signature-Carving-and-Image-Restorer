# main.py

import os
import sys
import logging
import tempfile
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject

from .enumerator import list_drives
from .gui import MainWindow
from .permissions import check_admin, run_as_admin
from .existing import ExistingImageExtractor
from .verifier import FileIntegrityVerifier
from .report_generator import ReportGenerator

# === Logging Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImageRecovery.Main")

class RecoveryWorker(QObject):
    """Worker class for handling recovery operations with progress signals"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    recovery_complete = pyqtSignal(list, str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True

    def run_recovery(self, scan_type, target_path, output_dir):
        """Main recovery method to be run in a separate thread"""
        try:
            self.status_updated.emit(f"Initializing {scan_type} on {target_path}...")
            
            # Normalize raw access path
            if target_path.startswith("\\\\.\\"):
                raw_path = target_path
            else:
                drive_letter = target_path.strip("\\")[:2]
                raw_path = f"\\\\.\\{drive_letter}"

            all_files = []
            
            # Initial setup
            self.progress_updated.emit(0)

            if scan_type == "Existing Images":
                self.status_updated.emit("Scanning for existing images...")
                extractor = ExistingImageExtractor()
                all_files = extractor.extract_images(target_path, output_dir) or []
            else:
                self.status_updated.emit("Performing raw recovery...")
                all_files = self.raw_recovery(raw_path, output_dir)
                
                self.status_updated.emit("Verifying recovered files...")
                verifier = FileIntegrityVerifier()
                corrupted_dir = os.path.join(output_dir, "corrupted")
                all_files = verifier.verify_files(all_files, corrupted_dir) or []

            self.status_updated.emit("Generating recovery report...")
            report_path = os.path.join(output_dir, "recovery_report.html")
            report_gen = ReportGenerator()
            report_gen.generate_report(all_files, report_path, scan_type, target_path)
            
            # Complete
            self.progress_updated.emit(100)

            if self._is_running:
                self.recovery_complete.emit(all_files, output_dir, report_path)

        except Exception as e:
            self.error_occurred.emit(f"Error during recovery: {str(e)}")

    def raw_recovery(self, drive_path, output_dir):
        """Raw recovery implementation with improved progress updates"""
        size = 512
        rcvd = 0
        recovered_files = []
        
        # Define signatures for JPG and PNG
        jpg_signatures = [
            b'\xff\xd8\xff\xe0\x00\x10\x4a\x46',  # JPEG SOI + APP0 JFIF
            b'\xff\xd8\xff\xe1',                   # JPEG SOI + APP1 Exif
            b'\xff\xd8\xff\xdb',                   # JPEG SOI + DQT
            b'\xff\xd8\xff\xe0',                   # JPEG SOI + APP0
            b'\xff\xd8\xff\xee',                   # JPEG SOI + APP14
            b'\xff\xd8\xff\xc0',                   # JPEG SOI + SOF0
            b'\xff\xd8\xff\xc4'                    # JPEG SOI + DHT
        ]
        png_signature = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'  # PNG signature
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            self.status_updated.emit(f"Scanning drive sectors for image files...")

            if not os.path.exists(drive_path):
                raise FileNotFoundError(f"Drive path not found: {drive_path}")

            # Try to get total size for progress calculation
            try:
                drive_size = os.path.getsize(drive_path)
                total_sectors = drive_size // size
                if total_sectors <= 0:
                    total_sectors = 1000000  # Fallback value
            except:
                total_sectors = 1000000  # Default estimate

            processed_sectors = 0
            prev_progress = 0
            
            # Reserve part of the progress bar for verification and post-processing
            # Only use 90% for scanning, reserve 10% for post-processing
            scan_progress_weight = 0.90
            
            with open(drive_path, "rb") as fileD:
                byte = fileD.read(size)
                drec = False
                offs = 0
                
                while byte and self._is_running:
                    # Check for signatures
                    file_type = None
                    found_pos = -1
                    
                    # Check for JPG signatures
                    for sig in jpg_signatures:
                        found = byte.find(sig)
                        if found >= 0:
                            file_type = "jpg"
                            found_pos = found
                            break
                    
                    # Check for PNG signature if no JPG found
                    if found_pos < 0:
                        found = byte.find(png_signature)
                        if found >= 0:
                            file_type = "png"
                            found_pos = found
                    
                    # If we found a signature
                    if found_pos >= 0:
                        drec = True
                        logger.info(f'Found {file_type.upper()} at location: {hex(found_pos+(size*offs))}')
                        
                        file_path = os.path.join(output_dir, f"recovered_{rcvd}.{file_type}")
                        
                        # Save current position to calculate per-file progress
                        file_start_pos = processed_sectors
                        estimated_file_size = 1000  # Estimate in sectors, will adjust during recovery
                        
                        with open(file_path, "wb") as fileN:
                            fileN.write(byte[found_pos:])
                            
                            # For JPG, we look for the end marker
                            if file_type == "jpg":
                                end_signature = b'\xff\xd9'
                            # For PNG, we look for IEND chunk
                            else:  # file_type == "png"
                                end_signature = b'\x49\x45\x4e\x44\xae\x42\x60\x82'
                            
                            file_sectors = 0
                            
                            while drec and self._is_running:
                                byte = fileD.read(size)
                                offs += 1
                                processed_sectors += 1
                                file_sectors += 1
                                
                                # Calculate two components of progress:
                                # 1. Overall drive scanning progress (weighted at 90%)
                                scan_progress = min(100, int((processed_sectors / total_sectors) * 100))
                                
                                # 2. Current file recovery progress (provide micro-updates)
                                # Dynamically adjust file size estimation based on seen data
                                if file_sectors > estimated_file_size / 2:
                                    estimated_file_size = file_sectors * 2
                                    
                                file_progress = min(100, int((file_sectors / estimated_file_size) * 100))
                                
                                # Show progress as combination, weighted toward scan progress
                                # but ensuring visible movement during file processing
                                combined_progress = int(scan_progress * scan_progress_weight)
                                
                                # Ensure progress never goes backward and shows movement
                                current_progress = max(prev_progress, combined_progress)
                                
                                # Always limit to 95% max until complete
                                current_progress = min(95, current_progress)
                                
                                if current_progress > prev_progress:
                                    self.progress_updated.emit(current_progress)
                                    self.status_updated.emit(f"Recovering {file_type.upper()} file ({file_progress}% complete)")
                                    prev_progress = current_progress
                                
                                if not byte:
                                    drec = False
                                    break
                                
                                bfind = byte.find(end_signature)
                                if bfind >= 0:
                                    # For JPG, end marker is 2 bytes
                                    if file_type == "jpg":
                                        fileN.write(byte[:bfind+2])
                                    # For PNG, IEND chunk is 12 bytes total (including the length field and CRC)
                                    else:  # file_type == "png"
                                        fileN.write(byte[:bfind+12])
                                    
                                    drec = False
                                else:
                                    fileN.write(byte)
                        
                        rcvd += 1
                        self.status_updated.emit(f"Recovered file {rcvd}: {os.path.basename(file_path)}")
                        
                        recovered_files.append({
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'type': file_type,
                            'status': 'Recovered'
                        })
                    
                    byte = fileD.read(size)
                    offs += 1
                    processed_sectors += 1
                    
                    # Update overall scanning progress periodically
                    if processed_sectors % 1000 == 0:
                        current_progress = min(95, int((processed_sectors / total_sectors) * scan_progress_weight * 100))
                        if current_progress > prev_progress:
                            self.progress_updated.emit(current_progress)
                            prev_progress = current_progress

            # Move to 98% after scanning is complete
            self.progress_updated.emit(98)
            self.status_updated.emit(f"Scan complete. Found {rcvd} files.")

        except Exception as e:
            self.error_occurred.emit(f"Error during raw recovery: {str(e)}")
            return []

        return recovered_files

    def stop(self):
        self._is_running = False
        self.status_updated.emit("Recovery process stopping...")

# === Application Entry Point ===
def main():
    if not check_admin():
        run_as_admin()
        return

    drives = list_drives()
    app = QApplication(sys.argv)

    worker = RecoveryWorker()
    window = MainWindow(drives, worker.run_recovery)

    # Connect signals
    worker.progress_updated.connect(window.set_progress_value)
    worker.status_updated.connect(window.update_status)
    worker.recovery_complete.connect(window.on_recovery_complete)
    worker.error_occurred.connect(window.on_recovery_error)
    window.stop_button.clicked.connect(worker.stop)

    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()