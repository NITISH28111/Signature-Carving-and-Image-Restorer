import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFrame, QHBoxLayout, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor

class UnifiedLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Image Recovery Tool")
        self.resize(950, 750)  # Slightly increased window size
        self.setStyleSheet("background-color: white;")
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #eb49fc, stop:1 #00ccff); border-radius: 10px;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        header_label = QLabel("Advanced Image Recovery")
        header_label.setStyleSheet("color: white; font-size: 36px; font-weight: bold;")
        header_label.setAlignment(Qt.AlignCenter)
        
        # Add drop shadow effect programmatically
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(4)
        header_shadow.setColor(QColor(0, 0, 0, 80))
        header_shadow.setOffset(2, 2)
        header_label.setGraphicsEffect(header_shadow)
        
        header_layout.addWidget(header_label)
        main_layout.addWidget(header_frame)
        
        # Instructions
        instructions = QLabel("Select Operation Mode")
        instructions.setStyleSheet("font-size: 22px; color: #444444; font-weight: bold;")
        instructions.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(instructions)
        
        # Buttons frame (horizontal layout)
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(50)
        buttons_layout.setContentsMargins(50, 30, 50, 10)  # More margin to spread out
        
        # Button containers for vertical layout with description
        recover_container = QFrame()
        recover_layout = QVBoxLayout(recover_container)
        recover_layout.setSpacing(15)
        recover_layout.setContentsMargins(0, 0, 0, 0)
        
        ai_container = QFrame()
        ai_layout = QVBoxLayout(ai_container)
        ai_layout.setSpacing(15)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        
        # Buttons style - removed box-shadow properties
        button_style_green = """
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #5CCD60, stop:1 #4CAF50);
                color: white;
                border: none;
                padding: 40px 60px;
                border-radius: 12px;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #66DD6A, stop:1 #52B956);
                border: 2px solid white;
                color: white;
            }
            QPushButton:pressed {
                padding-top: 42px;
                padding-left: 62px;
            }
        """
        
        button_style_blue = """
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #2BA1FF, stop:1 #2196F3);
                color: white;
                border: none;
                padding: 40px 60px;
                border-radius: 12px;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #40AFFF, stop:1 #2EA7FF);
                border: 2px solid white;
                color: white;
            }
            QPushButton:pressed {
                padding-top: 42px;
                padding-left: 62px;
            }
        """
        
        # Recover Images button and description
        self.file_recovery_button = QPushButton("Recover Images")
        self.file_recovery_button.setStyleSheet(button_style_green)
        self.file_recovery_button.setMinimumHeight(120)
        self.file_recovery_button.clicked.connect(self.launch_file_recovery)
        
        # Add shadow effect programmatically
        button_shadow1 = QGraphicsDropShadowEffect()
        button_shadow1.setBlurRadius(15)
        button_shadow1.setColor(QColor(0, 0, 0, 80))
        button_shadow1.setOffset(0, 4)
        self.file_recovery_button.setGraphicsEffect(button_shadow1)
        
        recover_layout.addWidget(self.file_recovery_button)
        
        recover_desc = QLabel("Recover deleted or lost images from storage devices")
        recover_desc.setStyleSheet("color: #555555; font-size: 16px; font-weight: normal; text-align: center;")
        recover_desc.setAlignment(Qt.AlignCenter)
        recover_desc.setWordWrap(True)
        recover_layout.addWidget(recover_desc)
        
        # Feature points for recovery
        recovery_features = QLabel("• Scans for deleted image files\n• Existing Image file Retrieval\n• Scan Capabilities-USB/Disk Partition/Full Disk")
        recovery_features.setStyleSheet("color: #666666; font-size: 14px;")
        recovery_features.setAlignment(Qt.AlignCenter)
        recover_layout.addWidget(recovery_features)
        
        buttons_layout.addWidget(recover_container)
        
        # AI Image Enhancement button and description
        self.ai_repair_button = QPushButton("AI Image Enhancement")
        self.ai_repair_button.setStyleSheet(button_style_blue)
        self.ai_repair_button.setMinimumHeight(120)
        self.ai_repair_button.clicked.connect(self.launch_ai_repair)
        
        # Add shadow effect programmatically
        button_shadow2 = QGraphicsDropShadowEffect()
        button_shadow2.setBlurRadius(15)
        button_shadow2.setColor(QColor(0, 0, 0, 80))
        button_shadow2.setOffset(0, 4)
        self.ai_repair_button.setGraphicsEffect(button_shadow2)
        
        ai_layout.addWidget(self.ai_repair_button)
        
        ai_desc = QLabel("Enhance image quality using AI technology")
        ai_desc.setStyleSheet("color: #555555; font-size: 16px; font-weight: normal; text-align: center;")
        ai_desc.setAlignment(Qt.AlignCenter)
        ai_desc.setWordWrap(True)
        ai_layout.addWidget(ai_desc)
        
        # Feature points for AI enhancement
        ai_features = QLabel("• Classify Blurry, Noisy, Clear\n• Fix image Using MPRNet-Deblur\n• Fix image Using MPRNet-Denoise")
        ai_features.setStyleSheet("color: #666666; font-size: 14px;")
        ai_features.setAlignment(Qt.AlignCenter)
        ai_layout.addWidget(ai_features)
        
        buttons_layout.addWidget(ai_container)
        
        main_layout.addWidget(buttons_frame)
        
        # Information box
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; border: 1px solid #dddddd;")
        info_layout = QVBoxLayout(info_frame)
        
        info_text = QLabel("Select the operation mode based on your needs." "\n🔎For recovering lost images, use 'Recover Images'🔍. "
                         "\n⚙️To improve the quality of existing images, use 'AI Image Enhancement'⚙️.")
        info_text.setStyleSheet("color: #555555; font-size: 14px;")
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(info_text)
        
        main_layout.addWidget(info_frame)
        
        # Add some stretch
        main_layout.addStretch()
        
        # Footer
        footer = QLabel("© 2025 Image Recovery and Repair Tool | Version 1.0")
        footer.setStyleSheet("color: #888888; font-size: 13px;")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)
        
        # Store references to child windows
        self.ai_repair_window = None
        self.file_recovery_window = None
    
    def launch_ai_repair(self):
        """Launch the AI Image Repair application"""
        from ai_image_repair.gui.app import ImageRepairApp
        self.hide()
        self.ai_repair_window = ImageRepairApp()
        self.ai_repair_window.show()
        if hasattr(self.ai_repair_window, 'back_button'):
            self.ai_repair_window.back_button.clicked.connect(self.show_parent)
    
    def launch_file_recovery(self):
        """Launch the File Recovery application"""
        from recovery.gui import MainWindow
        from recovery.main import list_drives, RecoveryWorker
    
        self.hide()
        drives = list_drives()
        worker = RecoveryWorker()
        self.file_recovery_window = MainWindow(drives, worker.run_recovery)
        
        worker.progress_updated.connect(self.file_recovery_window.set_progress_value)
        worker.status_updated.connect(self.file_recovery_window.update_status)
        worker.recovery_complete.connect(self.file_recovery_window.on_recovery_complete)
        worker.error_occurred.connect(self.file_recovery_window.on_recovery_error)
        self.file_recovery_window.stop_button.clicked.connect(worker.stop)
        
        self.file_recovery_window.show()
        if hasattr(self.file_recovery_window, 'back_button'):
            self.file_recovery_window.back_button.clicked.connect(self.show_parent)
    
    def show_parent(self):
        """Show the main launcher window again"""
        if self.ai_repair_window:
            self.ai_repair_window.close()
            self.ai_repair_window = None
        if self.file_recovery_window:
            self.file_recovery_window.close()
            self.file_recovery_window = None
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyle("Fusion")
    
    launcher = UnifiedLauncher()
    launcher.show()
    sys.exit(app.exec_())