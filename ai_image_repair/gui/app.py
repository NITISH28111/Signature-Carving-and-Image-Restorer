import os
import shutil
import torch
import numpy as np
from PIL import Image
from torchvision.models import resnet50, ResNet50_Weights
from torchvision import transforms
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget, 
                            QTextBrowser, QFrame, QProgressBar, QHBoxLayout, QSplitter, 
                            QApplication, QMainWindow, QStatusBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
import subprocess

# Get current directory (where this script is located)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define paths relative to current directory
BASE_DIR = os.path.dirname(current_dir)  # Parent of current directory (your_project)
CLASSIFIER_DIR = os.path.join(BASE_DIR, "classifier")
MODEL_PATH = os.path.join(CLASSIFIER_DIR, "model_resnet50_multi_label.pth")

# Create data directories in current directory (gui folder)
DATA_DIR = os.path.join(current_dir, "data")
REPAIR_DIR_BLURRY = os.path.join(DATA_DIR, "images_to_deblur")
REPAIR_DIR_NOISY = os.path.join(DATA_DIR, "images_to_denoise")
OUTPUT_DEBLURRED_DIR = os.path.join(DATA_DIR, "output_deblurred")
OUTPUT_DENOISED_DIR = os.path.join(DATA_DIR, "output_denoised")
OUTPUT_HTML = os.path.join(DATA_DIR, "classification_report.html")

# MPRNet demo is in the same directory as this script
MPRNET_DEMO_PATH = os.path.join(current_dir, "demo.py")

# Debug path information
print(f"Current directory: {current_dir}")
print(f"Base directory: {BASE_DIR}")
print(f"MODEL_PATH: {MODEL_PATH}")
print(f"MPRNET_DEMO_PATH: {MPRNET_DEMO_PATH}")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPAIR_DIR_BLURRY, exist_ok=True)
os.makedirs(REPAIR_DIR_NOISY, exist_ok=True)
os.makedirs(OUTPUT_DEBLURRED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DENOISED_DIR, exist_ok=True)

CLASS_NAMES = ['blurry', 'noisy', 'none']
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

transform = ResNet50_Weights.DEFAULT.transforms()

# Load the classification model
def load_model():
    try:
        model = resnet50(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES))
        
        # Verify model path exists before loading
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
            
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        model.to(DEVICE)
        model.eval()
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        raise

model = load_model()

# Predict an image and return class probabilities
def predict_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logits = model(image)
        probs = torch.sigmoid(logits).cpu().numpy()[0]
    return probs

# Generate an HTML report from results
def generate_html_report(results, html_path):
    html = """
    <html><head><style>
    body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }
    h2 { color: #2c3e50; text-align: center; }
    table { border-collapse: collapse; width: 100%; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    th, td { border: 1px solid #ddd; padding: 12px; text-align: center; }
    th { background-color: #3498db; color: white; }
    tr:nth-child(even) { background-color: #f2f2f2; }
    tr:hover { background-color: #e9f7fe; }
    .high { color: #e74c3c; font-weight: bold; }
    </style></head><body>
    <h2>Image Classification Report</h2>
    <table><tr><th>Image</th><th>Blurry</th><th>Noisy</th><th>None</th><th>Top Class</th></tr>
    """
    for filename, probs in results:
        top_class = CLASS_NAMES[np.argmax(probs)]
        html += f"<tr><td>{filename}</td><td>{probs[0]:.2f}</td><td>{probs[1]:.2f}</td><td>{probs[2]:.2f}</td><td class='high'>{top_class}</td></tr>"
    html += "</table></body></html>"
    with open(html_path, 'w') as f:
        f.write(html)

class StyleHelper:
    @staticmethod
    def get_button_style(primary=True):
        if primary:
            return """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1c6ea4;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """

    @staticmethod
    def get_text_browser_style():
        return """
            QTextBrowser {
                background-color: #f8f9fa;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """

# Main application
class ImageRepairApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Repair Classifier")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #f0f5f9;")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #3498db; border-radius: 8px;")
        header_layout = QHBoxLayout(header_frame)
        
        header_label = QLabel("Image Repair Classifier")
        header_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        header_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header_label)
        
        main_layout.addWidget(header_frame)
        
        # Instructions label
        instructions = QLabel("Select a folder of images to classify and repair if needed")
        instructions.setStyleSheet("font-size: 14px; color: #34495e; margin: 10px;")
        instructions.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(instructions)
        
        # Split view
        splitter = QSplitter(Qt.Vertical)
        
        # Result box
        self.result_box = QTextBrowser()
        self.result_box.setStyleSheet(StyleHelper.get_text_browser_style())
        self.result_box.setFont(QFont("Consolas", 10))
        self.result_box.setMinimumHeight(300)
        splitter.addWidget(self.result_box)
        
        # Button frame
        button_frame = QFrame()
        button_frame.setStyleSheet("background-color: white; border-radius: 8px;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(20, 20, 20, 20)
        button_layout.setSpacing(15)
        
        # Buttons
        self.select_button = QPushButton("Select Image Folder")
        self.select_button.setStyleSheet(StyleHelper.get_button_style(primary=True))
        self.select_button.setMinimumHeight(50)
        self.select_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon))
        self.select_button.setIconSize(QSize(24, 24))
        self.select_button.clicked.connect(self.select_folder)
        button_layout.addWidget(self.select_button)
        
        self.repair_button = QPushButton("Repair Images with MPRNet")
        self.repair_button.setStyleSheet(StyleHelper.get_button_style(primary=False))
        self.repair_button.setMinimumHeight(50)
        self.repair_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        self.repair_button.setIconSize(QSize(24, 24))
        self.repair_button.clicked.connect(self.run_mprnet)
        self.repair_button.setEnabled(False)
        button_layout.addWidget(self.repair_button)

        # In the ImageRepairApp class __init__ method, add this after creating other buttons:
        self.back_button = QPushButton("Back to Launcher")
        self.back_button.setStyleSheet(StyleHelper.get_button_style(primary=False))
        self.back_button.setMinimumHeight(50)
        self.back_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowBack))
        self.back_button.setIconSize(QSize(24, 24))
        button_layout.addWidget(self.back_button)
        
        main_layout.addWidget(splitter)
        main_layout.addWidget(button_frame)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
                margin: 0.5px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #ecf0f1; color: #34495e;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to classify images")
        
        # Path info in status bar
        path_label = QLabel(f"Model: {os.path.basename(MODEL_PATH)}")
        path_label.setStyleSheet("color: #7f8c8d; margin-right: 15px;")
        self.status_bar.addPermanentWidget(path_label)
        
        # Initialize variables
        self.image_folder = ""
        self.repair_needed = False
        
        # Show paths in log
        self.result_box.append("<b>System Information:</b>")
        self.result_box.append(f"• Current Directory: {current_dir}")
        self.result_box.append(f"• Model Path: {MODEL_PATH}")
        self.result_box.append(f"• MPRNet Demo Path: {MPRNET_DEMO_PATH}")
        self.result_box.append(f"• Using Device: {DEVICE}")
        self.result_box.append("<hr>")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.image_folder = folder
            results = []
            
            # Clean repair directories
            for repair_dir in [REPAIR_DIR_BLURRY, REPAIR_DIR_NOISY]:
                if os.path.exists(repair_dir):
                    for file in os.listdir(repair_dir):
                        file_path = os.path.join(repair_dir, file)
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                else:
                    os.makedirs(repair_dir, exist_ok=True)

            self.result_box.clear()
            self.status_bar.showMessage(f"Processing images from: {folder}")
            self.result_box.append(f"<b>Processing folder:</b> {folder}")
            self.progress_bar.setVisible(True)
            
            image_files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            
            if not image_files:
                self.result_box.append("<div style='background-color: #f8d7da; padding: 10px; border-radius: 5px;'>No image files found in selected folder!</div>")
                self.status_bar.showMessage("No image files found")
                self.progress_bar.setVisible(False)
                return
                
            self.progress_bar.setMaximum(len(image_files))
            
            for i, filename in enumerate(image_files):
                path = os.path.join(folder, filename)
                probs = predict_image(path)
                results.append((filename, probs))
                top_class = CLASS_NAMES[np.argmax(probs)]
                
                # Color-code the classification results
                if top_class == 'blurry':
                    class_text = f"<span style='color: #e74c3c; font-weight: bold;'>BLURRY</span>"
                    shutil.copy(path, os.path.join(REPAIR_DIR_BLURRY, filename))
                elif top_class == 'noisy':
                    class_text = f"<span style='color: #e67e22; font-weight: bold;'>NOISY</span>"
                    shutil.copy(path, os.path.join(REPAIR_DIR_NOISY, filename))
                else:
                    class_text = f"<span style='color: #2ecc71; font-weight: bold;'>NONE</span>"
                
                self.result_box.append(f"<b>{filename}</b>: {class_text} (Blurry: {probs[0]:.2f}, Noisy: {probs[1]:.2f}, None: {probs[2]:.2f})")
                
                # Update progress bar
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()

            generate_html_report(results, OUTPUT_HTML)
            self.result_box.append(f"<hr><div style='background-color: #d4edda; padding: 10px; border-radius: 5px;'><b>HTML report generated:</b> {OUTPUT_HTML}</div>")

            # Check if any images need repair
            blurry_count = len(os.listdir(REPAIR_DIR_BLURRY)) if os.path.exists(REPAIR_DIR_BLURRY) else 0
            noisy_count = len(os.listdir(REPAIR_DIR_NOISY)) if os.path.exists(REPAIR_DIR_NOISY) else 0
            self.repair_needed = blurry_count > 0 or noisy_count > 0
            
            if self.repair_needed:
                self.result_box.append(f"<div style='background-color: #f8d7da; padding: 10px; border-radius: 5px; margin-top: 10px;'>"
                                     f"<b>Images requiring repair found:</b><br>"
                                     f"• Blurry images: {blurry_count}<br>"
                                     f"• Noisy images: {noisy_count}<br><br>"
                                     f"Click the repair button to proceed.</div>")
                self.repair_button.setEnabled(True)
                self.status_bar.showMessage(f"Found {blurry_count + noisy_count} images needing repair")
            else:
                self.result_box.append("<div style='background-color: #d4edda; padding: 10px; border-radius: 5px; margin-top: 10px;'><b>All images are clean. No repair needed.</b></div>")
                self.repair_button.setEnabled(False)
                self.status_bar.showMessage("All images are clean")
            
            self.progress_bar.setVisible(False)

    def run_mprnet(self):
        if not self.repair_needed:
            return
        
        self.status_bar.showMessage("Running MPRNet for image repair...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(2) # Two operations: deblurring and denoising
        
        self.result_box.append("<hr><div style='background-color: #cce5ff; padding: 10px; border-radius: 5px;'><b>Running MPRNet on images requiring repair...</b></div>")
        QApplication.processEvents()

        # Run Deblurring only if there are blurry images
        if os.path.exists(REPAIR_DIR_BLURRY) and len(os.listdir(REPAIR_DIR_BLURRY)) > 0:
            self.result_box.append("➤ Starting deblurring process...")
            QApplication.processEvents()
            try:
                subprocess.run([
                    "python", MPRNET_DEMO_PATH, 
                    "--task", "Deblurring", 
                    "--input_dir", REPAIR_DIR_BLURRY, 
                    "--result_dir", OUTPUT_DEBLURRED_DIR
                ], check=True)
                self.result_box.append("✓ Deblurring completed successfully!")
            except subprocess.CalledProcessError as e:
                self.result_box.append(f"⚠ Error during deblurring: {str(e)}")
            except Exception as e:
                self.result_box.append(f"⚠ Unexpected error during deblurring: {str(e)}")
        else:
            self.result_box.append("➤ No blurry images found - skipping deblurring")
            
        self.progress_bar.setValue(1)
        QApplication.processEvents()

        # Run Denoising only if there are noisy images
        if os.path.exists(REPAIR_DIR_NOISY) and len(os.listdir(REPAIR_DIR_NOISY)) > 0:
            self.result_box.append("➤ Starting denoising process...")
            QApplication.processEvents()
            try:
                subprocess.run([
                    "python", MPRNET_DEMO_PATH, 
                    "--task", "Denoising", 
                    "--input_dir", REPAIR_DIR_NOISY, 
                    "--result_dir", OUTPUT_DENOISED_DIR
                ], check=True)
                self.result_box.append("✓ Denoising completed successfully!")
            except subprocess.CalledProcessError as e:
                self.result_box.append(f"⚠ Error during denoising: {str(e)}")
            except Exception as e:
                self.result_box.append(f"⚠ Unexpected error during denoising: {str(e)}")
        else:
            self.result_box.append("➤ No noisy images found - skipping denoising")
            
        self.progress_bar.setValue(2)
        QApplication.processEvents()

        # Show results
        deblurred_count = len(os.listdir(OUTPUT_DEBLURRED_DIR)) if os.path.exists(OUTPUT_DEBLURRED_DIR) else 0
        denoised_count = len(os.listdir(OUTPUT_DENOISED_DIR)) if os.path.exists(OUTPUT_DENOISED_DIR) else 0
        
        self.result_box.append(f"<div style='background-color: #d4edda; padding: 10px; border-radius: 5px; margin-top: 10px;'><b>✓ Repair complete!</b><br>• Deblurred images: {deblurred_count}<br>• Denoised images: {denoised_count}<br><br>Check the following folders:<br>• {OUTPUT_DEBLURRED_DIR}<br>• {OUTPUT_DENOISED_DIR}</div>")
        self.status_bar.showMessage("Image repair completed successfully")
        self.progress_bar.setVisible(False)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    
    # Set application-wide font
    app.setFont(QFont("Segoe UI", 10))
    
    # Apply Material-style to the entire application
    app.setStyle("Fusion")
    
    window = ImageRepairApp()
    window.show()
    app.exec_()