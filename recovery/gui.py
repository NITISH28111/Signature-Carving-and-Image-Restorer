# recovery/gui.py (updated theme)
import os
import sys
import webbrowser
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QComboBox, QFileDialog, 
                            QProgressBar, QTextEdit, QGroupBox, QRadioButton,
                            QButtonGroup, QApplication, QMessageBox, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QTextCursor

class RecoveryThread(QThread):
    """Thread to handle the recovery process"""
    update_progress = pyqtSignal(int)
    update_status = pyqtSignal(str)
    recovery_complete = pyqtSignal(list, str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, scan_type, target_path, output_dir, recovery_callback):
        super().__init__()
        self.scan_type = scan_type
        self.target_path = target_path
        self.output_dir = output_dir
        self.recovery_callback = recovery_callback
        self.running = True

    def run(self):
        try:
            self.update_status.emit(f"Starting {self.scan_type} on {self.target_path}...")
            self.recovery_callback(
                self.scan_type,
                self.target_path,
                self.output_dir
            )
        except Exception as e:
            self.error_occurred.emit(f"Error during recovery: {str(e)}")

    def stop(self):
        self.running = False
        self.terminate()

class MainWindow(QMainWindow):
    """Main GUI window for the Image Recovery Application"""
    
    def __init__(self, drives, recovery_callback):
        super().__init__()
        self.drives = drives
        self.recovery_callback = recovery_callback
        self.report_path = None
        self.recovery_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Image Recovery Tool")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: #f0f5f9;")
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Add header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #3498db; border-radius: 8px;")
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("Image Recovery Tool")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        main_layout.addWidget(header_frame)
        
        # Add scan mode selection
        scan_group = QGroupBox("Scan Mode")
        scan_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        scan_layout = QVBoxLayout()
        scan_group.setLayout(scan_layout)
        
        self.scan_mode_group = QButtonGroup()
        
        # Radio buttons for scan modes
        self.usb_scan_radio = QRadioButton("USB Scan")
        self.partition_scan_radio = QRadioButton("Disk Partition Scan")
        self.full_disk_scan_radio = QRadioButton("Full Disk Scan")
        self.existing_scan_radio = QRadioButton("Existing Images (No Recovery)")
        
        # Style radio buttons
        radio_style = """
            QRadioButton {
                font-weight: normal;
                padding: 5px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """
        self.usb_scan_radio.setStyleSheet(radio_style)
        self.partition_scan_radio.setStyleSheet(radio_style)
        self.full_disk_scan_radio.setStyleSheet(radio_style)
        self.existing_scan_radio.setStyleSheet(radio_style)
        
        self.scan_mode_group.addButton(self.usb_scan_radio, 1)
        self.scan_mode_group.addButton(self.partition_scan_radio, 2)
        self.scan_mode_group.addButton(self.full_disk_scan_radio, 3)
        self.scan_mode_group.addButton(self.existing_scan_radio, 4)
        
        self.usb_scan_radio.setChecked(True)
        
        scan_layout.addWidget(self.usb_scan_radio)
        scan_layout.addWidget(self.partition_scan_radio)
        scan_layout.addWidget(self.full_disk_scan_radio)
        scan_layout.addWidget(self.existing_scan_radio)


        main_layout.addWidget(scan_group)
        
        # Add target selection
        target_group = QGroupBox("Target Selection")
        target_group.setStyleSheet(scan_group.styleSheet())
        target_layout = QVBoxLayout()
        target_group.setLayout(target_layout)
        
        # Drive selection combo box
        drive_layout = QHBoxLayout()
        drive_label = QLabel("Select Drive/Partition:")
        drive_label.setStyleSheet("font-weight: normal;")
        drive_layout.addWidget(drive_label)
        
        self.drive_combo = QComboBox()
        self.drive_combo.setStyleSheet("""
            QComboBox {
                font-weight: normal;
                padding: 5px;
                border: 1px solid #dcdcdc;
                border-radius: 3px;
            }
        """)
        
        # Populate with available drives
        for drive in self.drives:
            label = f"{drive['path']} - {drive['label']} ({drive['filesystem']}, {drive['size_formatted']} - {drive['free_space_formatted']} free)"
            self.drive_combo.addItem(label, drive['path'])
            
        drive_layout.addWidget(self.drive_combo, 1)
        target_layout.addLayout(drive_layout)
        
        # Output directory selection
        output_layout = QHBoxLayout()
        output_label = QLabel("Output Directory:")
        output_label.setStyleSheet("font-weight: normal;")
        output_layout.addWidget(output_label)
        
        self.output_edit = QTextEdit()
        self.output_edit.setMaximumHeight(30)
        self.output_edit.setStyleSheet("""
            QTextEdit {
                font-weight: normal;
                border: 1px solid #dcdcdc;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.output_edit.setText(os.path.join(os.path.expanduser("~"), "RecoveredImages"))
        output_layout.addWidget(self.output_edit, 1)
        
        self.output_button = QPushButton("Browse...")
        self.output_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.output_button.clicked.connect(self.browse_output)
        output_layout.addWidget(self.output_button)
        target_layout.addLayout(output_layout)
        
        main_layout.addWidget(target_group)
        
        # Add action buttons
        button_frame = QFrame()
        button_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(10)
        
        self.start_button = QPushButton("Start Scan")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_button.clicked.connect(self.start_scan)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Scan")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_button.clicked.connect(self.stop_scan)
        button_layout.addWidget(self.stop_button)
        
        self.report_button = QPushButton("Open Report")
        self.report_button.setEnabled(False)
        self.report_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.report_button.clicked.connect(self.open_report)
        button_layout.addWidget(self.report_button)

        # In the MainWindow class init_ui method, add this after creating other buttons:
        self.back_button = QPushButton("Back to Launcher")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        button_layout.addWidget(self.back_button)
        
        main_layout.addWidget(button_frame)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                width: 10px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Add status log
        log_group = QGroupBox("Status Log")
        log_group.setStyleSheet(scan_group.styleSheet())
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dcdcdc;
                font-family: monospace;
                border-radius: 5px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
        # Set some spacing and margins
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Initialize with a welcome message
        self.update_status("Ready to scan. Please select a scan mode and target.")
            
    def browse_output(self):
        """Open file dialog to select output directory"""
        selected_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if selected_path:
            self.output_edit.setText(selected_path)
            
    def start_scan(self):
        """Start the scan process"""
        # Get the scan type
        scan_type = "USB Scan"
        if self.partition_scan_radio.isChecked():
            scan_type = "Partition Scan"
        elif self.full_disk_scan_radio.isChecked():
            scan_type = "Full Disk Scan"
        elif self.existing_scan_radio.isChecked():
            scan_type = "Existing Images"
            
        # Get the target path
        selected_index = self.drive_combo.currentIndex()
        if selected_index >= 0:
            target_path = self.drive_combo.itemData(selected_index)
        else:
            QMessageBox.warning(self, "Invalid Selection", "Please select a target drive.")
            return
            
        # Get output directory
        output_dir = self.output_edit.toPlainText().strip()
        if not output_dir:
            output_dir = os.path.join(os.path.expanduser("~"), "RecoveredImages")
            
        # Update UI state
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.report_button.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Create and start recovery thread
        self.recovery_thread = RecoveryThread(
            scan_type, 
            target_path, 
            output_dir,
            self.recovery_callback
        )
        
        # Connect signals
        self.recovery_thread.update_progress.connect(self.set_progress_value)
        self.recovery_thread.update_status.connect(self.update_status)
        self.recovery_thread.recovery_complete.connect(self.on_recovery_complete)
        self.recovery_thread.error_occurred.connect(self.on_recovery_error)
        
        self.recovery_thread.start()
        
    def stop_scan(self):
        """Stop the current scan"""
        if self.recovery_thread and self.recovery_thread.isRunning():
            self.recovery_thread.stop()
            self.update_status("Scan stopped by user")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setValue(0)
            
    def on_recovery_complete(self, recovered_files, output_dir, report_path):
        """Handle completion of recovery process"""
        self.update_status(f"Recovery complete! Found {len(recovered_files)} files.")
        self.update_status(f"Files saved to: {output_dir}")
        self.update_status(f"Report generated at: {report_path}")
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.report_button.setEnabled(True)
        self.progress_bar.setValue(100)
        
        self.report_path = report_path
        
        # Show completion message
        QMessageBox.information(
            self,
            "Recovery Complete",
            f"Recovery process completed successfully!\n\n"
            f"Recovered {len(recovered_files)} files to:\n{output_dir}\n\n"
            f"Report saved to:\n{report_path}"
        )
        
    def on_recovery_error(self, error_message):
        """Handle errors during recovery"""
        self.update_status(f"Error: {error_message}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        QMessageBox.critical(
            self,
            "Recovery Error",
            f"An error occurred during recovery:\n\n{error_message}"
        )
            
    def update_status(self, message):
        """Update the status log with a new message"""
        self.log_text.append(message)
        # Scroll to the bottom
        self.log_text.moveCursor(QTextCursor.End)
        
    def set_progress_value(self, value):
        """Set the progress bar value"""
        self.progress_bar.setValue(value)
        
    def open_report(self):
        """Open the generated report in the default browser"""
        if self.report_path and os.path.exists(self.report_path):
            webbrowser.open(f"file://{self.report_path}")
        else:
            QMessageBox.warning(self, "Report Not Found", 
                              "The report file was not found or has not been generated yet.")