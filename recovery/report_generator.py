# report_generator.py
import os
import time
import logging
import datetime
import platform
import psutil

logger = logging.getLogger("ImageRecovery.ReportGenerator")

class ReportGenerator:
    """Module for generating recovery reports"""
    
    def __init__(self):
        pass
    
    def generate_report(self, file_list, report_path, scan_type, target_path):
        """
        Generate a report of the recovery operation
        
        Args:
            file_list: List of file information dictionaries
            report_path: Path to save the report
            scan_type: Type of scan performed
            target_path: Path that was scanned
            
        Returns:
            Path to the generated report
        """
        logger.info(f"Generating report to {report_path}")
        
        try:
            # Count statistics
            total_files = len(file_list)
            ok_files = len([f for f in file_list if f['status'] == 'OK'])
            corrupted_files = len([f for f in file_list if 'Corrupted' in f['status']])
            copied_files = len([f for f in file_list if f['status'] == 'Copied'])
            
            # Get total recovered size
            total_size = sum(f['size'] for f in file_list if 'size' in f)
            
            # Generate HTML report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Recovery Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .status-ok {{
            color: green;
        }}
        .status-corrupted {{
            color: red;
        }}
        .status-copied {{
            color: blue;
        }}
    </style>
</head>
<body>
    <h1>Image Recovery Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Date/Time:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Scan Type:</strong> {scan_type}</p>
        <p><strong>Target Path:</strong> {target_path}</p>
        <p><strong>Total Files:</strong> {total_files}</p>
        <p><strong>Successfully Recovered:</strong> {ok_files}</p>
        <p><strong>Corrupted Files:</strong> {corrupted_files}</p>
        <p><strong>Existing Files Copied:</strong> {copied_files}</p>
        <p><strong>Total Data Size:</strong> {self._format_size(total_size)}</p>
    </div>
    
    <h2>System Information</h2>
    <table>
        <tr>
            <th>Item</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Operating System</td>
            <td>{platform.system()} {platform.release()}</td>
        </tr>
        <tr>
            <td>Machine</td>
            <td>{platform.machine()}</td>
        </tr>
        <tr>
            <td>Processor</td>
            <td>{platform.processor()}</td>
        </tr>
        <tr>
            <td>Total RAM</td>
            <td>{self._format_size(psutil.virtual_memory().total)}</td>
        </tr>
    </table>
    
    <h2>Recovered Files</h2>
    <table>
        <tr>
            <th>#</th>
            <th>File Name</th>
            <th>Type</th>
            <th>Size</th>
            <th>Status</th>
            <th>Hash</th>
        </tr>
""")

                # Add file entries
                for i, file_info in enumerate(file_list, 1):
                    status_class = ""
                    if file_info['status'] == 'OK':
                        status_class = "status-ok"
                    elif 'Corrupted' in file_info['status']:
                        status_class = "status-corrupted"
                    elif file_info['status'] == 'Copied':
                        status_class = "status-copied"
                        
                    f.write(f"""
        <tr>
            <td>{i}</td>
            <td>{os.path.basename(file_info['path'])}</td>
            <td>{file_info.get('type', 'Unknown')}</td>
            <td>{self._format_size(file_info.get('size', 0))}</td>
            <td class="{status_class}">{file_info['status']}</td>
            <td>{file_info.get('hash', 'N/A')}</td>
        </tr>""")

                # Close HTML document
                f.write("""
    </table>
    
    <p><em>Report generated by Image Recovery Tool</em></p>
</body>
</html>
""")

            logger.info(f"Report generated successfully: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            
            # Try to create a simple text report as fallback
            try:
                text_report_path = os.path.splitext(report_path)[0] + ".txt"
                with open(text_report_path, 'w') as f:
                    f.write(f"Image Recovery Report\n")
                    f.write(f"Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Scan Type: {scan_type}\n")
                    f.write(f"Target Path: {target_path}\n")
                    f.write(f"Total Files: {total_files}\n")
                    f.write(f"Successfully Recovered: {ok_files}\n")
                    f.write(f"Corrupted Files: {corrupted_files}\n")
                    f.write(f"Total Data Size: {self._format_size(total_size)}\n\n")
                    
                    f.write("File List:\n")
                    for i, file_info in enumerate(file_list, 1):
                        f.write(f"{i}. {os.path.basename(file_info['path'])} - "
                              f"{file_info.get('type', 'Unknown')} - "
                              f"{self._format_size(file_info.get('size', 0))} - "
                              f"{file_info['status']}\n")
                
                return text_report_path
                
            except Exception as fallback_error:
                logger.error(f"Failed to create fallback text report: {str(fallback_error)}")
                return None
    
    def _format_size(self, size_bytes):
        """Format size in bytes to a human-readable string"""
        if size_bytes == 0:
            return "0 B"
            
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
            
        return f"{size_bytes:.2f} {size_names[i]}"