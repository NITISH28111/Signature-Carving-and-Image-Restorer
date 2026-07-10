# enumerator.py
import os
import string
import ctypes
import logging
import platform
import win32api
import win32file
import wmi

logger = logging.getLogger("ImageRecovery.Enumerator")

def get_size_formatted(size_bytes):
    """Convert bytes to a human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def list_drives():
    """List all available drives, partitions, and mount points"""
    drives = []
    
    try:
        # Get physical drives
        c = wmi.WMI()
        
        # Get logical drives (mounted partitions)
        for drive_letter in string.ascii_uppercase:
            drive_path = f"{drive_letter}:\\"
            
            try:
                if not os.path.exists(drive_path):
                    continue
                    
                drive_type = win32file.GetDriveType(drive_path)
                
                # Skip CD-ROM drives
                if drive_type == win32file.DRIVE_CDROM:
                    continue
                    
                # Get drive information
                drive_info = {
                    'path': drive_path,
                    'device_id': None,
                    'label': '',
                    'filesystem': '',
                    'size_bytes': 0,
                    'size_formatted': '',
                    'free_space_bytes': 0,
                    'free_space_formatted': '',
                    'type': 'unknown'
                }
                
                # Get volume information
                try:
                    volume_info = win32api.GetVolumeInformation(drive_path)
                    drive_info['label'] = volume_info[0] if volume_info[0] else 'No Label'
                    drive_info['filesystem'] = volume_info[4]
                except Exception as e:
                    logger.warning(f"Error getting volume info for {drive_path}: {str(e)}")
                    drive_info['label'] = 'Unknown'
                    drive_info['filesystem'] = 'Unknown'
                
                # Get disk space information
                try:
                    free_bytes, total_bytes, total_free_bytes = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p(drive_path),
                        ctypes.byref(free_bytes),
                        ctypes.byref(total_bytes),
                        ctypes.byref(total_free_bytes)
                    )
                    
                    drive_info['size_bytes'] = total_bytes.value
                    drive_info['size_formatted'] = get_size_formatted(total_bytes.value)
                    drive_info['free_space_bytes'] = free_bytes.value
                    drive_info['free_space_formatted'] = get_size_formatted(free_bytes.value)
                except Exception as e:
                    logger.warning(f"Error getting disk space for {drive_path}: {str(e)}")
                
                # Set drive type
                drive_types = {
                    win32file.DRIVE_REMOVABLE: 'Removable',
                    win32file.DRIVE_FIXED: 'Fixed',
                    win32file.DRIVE_REMOTE: 'Network',
                    win32file.DRIVE_RAMDISK: 'RAM Disk',
                    win32file.DRIVE_CDROM: 'CD-ROM',
                    win32file.DRIVE_UNKNOWN: 'Unknown'
                }
                drive_info['type'] = drive_types.get(drive_type, 'Unknown')
                
                # Get physical device ID
                for physical_disk in c.Win32_DiskDrive():
                    for partition in physical_disk.associators("Win32_DiskDriveToDiskPartition"):
                        for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                            if logical_disk.DeviceID == f"{drive_letter}:":
                                drive_info['device_id'] = physical_disk.DeviceID
                
                drives.append(drive_info)
                
            except Exception as e:
                logger.error(f"Error processing drive {drive_path}: {str(e)}")
        
        # Add physical drives as well (for direct access)
        physical_drives = []
        for i in range(10):  # Check up to 10 physical drives
            device_path = f"\\\\.\\PhysicalDrive{i}"
            try:
                # Try to open the drive to see if it exists
                handle = win32file.CreateFile(
                    device_path,
                    win32file.GENERIC_READ,
                    win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None
                )
                
                if handle != win32file.INVALID_HANDLE_VALUE:
                    # Get drive information from WMI
                    for disk in c.Win32_DiskDrive():
                        if disk.DeviceID.endswith(f"PhysicalDrive{i}"):
                            drive_info = {
                                'path': device_path,
                                'device_id': disk.DeviceID,
                                'label': f"Physical Disk {i}",
                                'filesystem': 'Raw Disk',
                                'size_bytes': int(disk.Size) if disk.Size else 0,
                                'size_formatted': get_size_formatted(int(disk.Size) if disk.Size else 0),
                                'free_space_bytes': 0,
                                'free_space_formatted': 'N/A',
                                'type': 'Physical Drive',
                                'model': disk.Model if hasattr(disk, 'Model') else 'Unknown Model'
                            }
                            physical_drives.append(drive_info)
                            break
                    
                    # Close the handle
                    win32file.CloseHandle(handle)
                    
            except Exception as e:
                # This physical drive probably doesn't exist
                pass
                
        # Add physical drives to the list
        drives.extend(physical_drives)
        
    except Exception as e:
        logger.error(f"Error listing drives: {str(e)}")
        
    return drives

def get_drive_by_path(path):
    """Get drive information for a specific path"""
    drives = list_drives()
    
    # Direct match
    for drive in drives:
        if drive['path'] == path:
            return drive
            
    # Match drive letter for a path
    if os.path.isabs(path) and len(path) >= 2 and path[1] == ':':
        drive_letter = path[0].upper()
        for drive in drives:
            if drive['path'].startswith(f"{drive_letter}:"):
                return drive
                
    return None