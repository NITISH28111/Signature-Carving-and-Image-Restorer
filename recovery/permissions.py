# permissions.py
import os
import sys
import ctypes
import logging

logger = logging.getLogger("ImageRecovery.Permissions")

def is_admin():
    """Check if the current process has admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        return False

def check_admin():
    """Check for admin rights and return status"""
    if is_admin():
        logger.info("Running with administrator privileges")
        return True
    else:
        logger.warning("Not running with administrator privileges")
        return False

def run_as_admin():
    """Re-run the current script with admin privileges"""
    try:
        if sys.argv[0].endswith('.py'):
            # Running as a Python script
            args = [sys.executable] + sys.argv
            # Set the param to indicate this process already tried to elevate
            if "--no-elevate" not in args:
                args.append("--no-elevate")
            
            # Request elevation via ShellExecute
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join('"' + arg + '"' for arg in sys.argv),
                None, 
                1
            )
        else:
            # Running as an executable
            if "--no-elevate" not in sys.argv:
                ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    " ".join('"' + arg + '"' for arg in sys.argv[1:]) + " --no-elevate",
                    None, 
                    1
                )
        return True
    except Exception as e:
        logger.error(f"Failed to run as admin: {str(e)}")
        return False

def has_disk_read_access(path):
    """
    Check if the current process has disk read access to the specified path
    Returns True if access is available, False otherwise
    """
    try:
        # For raw disk access check
        if path.startswith(r"\\\."):
            # Try to open the physical drive with read access
            try:
                handle = ctypes.windll.kernel32.CreateFileW(
                    path,  # Path to the drive
                    0x80000000,  # GENERIC_READ
                    1,  # FILE_SHARE_READ
                    None,  # Security attributes
                    3,  # OPEN_EXISTING
                    0,  # File attributes
                    None  # Template file
                )
                
                if handle == -1 or handle == 0xFFFFFFFFFFFFFFFF:  # INVALID_HANDLE_VALUE
                    logger.warning(f"Cannot access {path}: Permission denied")
                    return False
                    
                # Close the handle
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
                
            except Exception as e:
                logger.error(f"Error checking disk access: {str(e)}")
                return False
        
        # For regular file system access
        test_path = os.path.join(path, ".recovery_test")
        try:
            with open(test_path, "w") as f:
                f.write("test")
            os.remove(test_path)
            return True
        except PermissionError:
            logger.warning(f"Cannot write to {path}: Permission denied")
            
            # Still check if we can read
            try:
                files = os.listdir(path)
                return True
            except PermissionError:
                logger.warning(f"Cannot read from {path}: Permission denied")
                return False
                
    except Exception as e:
        logger.error(f"Error checking access to {path}: {str(e)}")
        return False