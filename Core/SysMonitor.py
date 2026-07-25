# Libraries to handle I/O files, folders and Manage a system
import datetime
import time
import psutil
import platform
import os
try:
    from plyer import notification
except ImportError:
    # plyer is an optional dependency used only for desktop notifications.
    # The framework degrades gracefully when it is not installed.
    notification = None

# Other:
from Log import Logs
from Settings import Path_Settings
from DirectoryManager import Paths_Manager, ManageLogDir








class Sensor:
    
        
    def __init__(self):
        self.LogSys = Logs()
        self.LogSys.LogEngine("SysMonitor - Sensor", "LogCore_SysMonitor")


    def CPU_Checker(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            self.LogSys.print_and_log(f"[\u001b[35m*\u001b[0m] CPU Usage: {cpu_percent}%\n", "debug")
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error checking CPU usage: {e}", "error")

    def Uptime(self):
        try:
            uptime = round(time.time() - psutil.boot_time())
            self.LogSys.print_and_log(f"[\u001b[35m*\u001b[0m] System Uptime: {datetime.timedelta(seconds=uptime)}\n", "debug")
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error checking system uptime: {e}", "error")


    def Component_Temp_Checker(self):
        try:
            if not hasattr(psutil, "sensors_temperatures"):
                self.LogSys.print_and_log("[\u001b[31m!\u001b[0m]  Temperature sensor data not available on this system.", "error")
                return
            
            self.Component_details = psutil.sensors_temperatures()
    
            if not self.Component_details:
                self.LogSys.print_and_log("[\u001b[31m!\u001b[0m]  No temperature data detected.", "error")
                return
    
            self.LogSys.print_and_log("[\u001b[35m*\u001b[0m] Component Temperatures:", "debug")
            
            for i, (sensor, readings) in enumerate(self.Component_details.items()):
                self.LogSys.print_and_log(f"    [\u001b[36m{i+1}\u001b[0m] Sensor: {sensor}", "debug") 
                if readings:  # Ensure there is data
                    for check in readings:
                        label = check.label if check.label else "Unnamed"
                        self.LogSys.print_and_log(
                            f"        \u001b[36m├──\u001b[0m {label}: {check.current}°C (High: {check.high if check.high else 'N/A'}°C, Critical: {check.critical if check.critical else 'N/A'}°C)",
                            "debug"
                        )
                    self.LogSys.print_and_log("\n", "debug")
                else:
                    self.LogSys.print_and_log(f"        \u001b[36m├──\u001b[0m No data available for {sensor}.", "error")
            
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error checking component temperatures: {e}", "error")


    def Battery_Checker(self):
        try:
            self.LogSys.print_and_log("[\u001b[35m*\u001b[0m] Battery: ", "debug")
            
            if not hasattr(psutil, "sensors_battery"):
                self.LogSys.print_and_log("    Battery information not available on this system.", "debug")
                return
            
            battery_details = psutil.sensors_battery()
            if battery_details is None:
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m No battery detected or system does not support battery status", "debug")
                return
            
            power_plugged = getattr(battery_details, 'power_plugged', False)  # Default to False if None
            battery_percent = getattr(battery_details, 'percent', None)
            secsleft = getattr(battery_details, 'secsleft', psutil.POWER_TIME_UNLIMITED)
            
            if power_plugged:
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m Power Plugged ", "debug")
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m Status: %s" % ("Charging" if battery_percent is not None and battery_percent < 100 else "Fully charged"))
            else:
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m Power Unplugged ", "debug")
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m Status: Discharging", "debug")
            
            if battery_percent is not None:
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m Battery Percentage: %s%%" % round(battery_percent, 2))
            else:
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m Battery percentage could not be retrieved", "debug")
            
            if secsleft == psutil.POWER_TIME_UNLIMITED or secsleft == psutil.POWER_TIME_UNKNOWN:
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m Time Left: Not available", "debug")
            else:
                self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m Time Left: %s seconds" % secsleft)
            
            self.LogSys.print_and_log("\n", "debug")
            
        except Exception as e:
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Error retrieving battery information: {e}", "error")


    def Fan_Checker(self):
        try:
            if not hasattr(psutil, "sensors_fans"):
                self.LogSys.print_and_log("[\u001b[31m!\u001b[0m]  Fan sensor data not available on this system.", "error")
                return
    
            self.Fan_details = psutil.sensors_fans()
    
            if not self.Fan_details:
                self.LogSys.print_and_log("[\u001b[31m!\u001b[0m]  No fan data detected.", "error")
                return
    
            self.LogSys.print_and_log("[\u001b[35m*\u001b[0m] Fan Status:", "debug")
    
            for fan_name, readings in self.Fan_details.items():
                self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Fan Controller: {fan_name}", "debug")
                if readings:
                    for fan in readings:
                        self.LogSys.print_and_log(f"        \u001b[36m├──\u001b[0m {fan.label or 'Unnamed'}: {fan.current} RPM", "debug")
                else:
                    self.LogSys.print_and_log("        \u001b[36m├──\u001b[0m No data available.", "error")
    
            self.LogSys.print_and_log("\n", "debug")
    
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error checking fan status: {e}", "error")


    def Brigthness_checker(self):
        brightness = "N/A"
        
        if platform.system() == "Linux":
            backlight_path = "/sys/class/backlight/"
            
            try:
                if not os.path.exists(backlight_path):
                    raise FileNotFoundError("Backlight path not found")
                
                # Get all available backlight directories
                backlight_dirs = [d for d in os.listdir(backlight_path) if os.path.isdir(os.path.join(backlight_path, d))]
                
                if not backlight_dirs:
                    raise FileNotFoundError("No backlight devices found")
                
                for device in backlight_dirs:
                    brightness_file = os.path.join(backlight_path, device, "brightness")
                    max_brightness_file = os.path.join(backlight_path, device, "max_brightness")
                    
                    if os.path.exists(brightness_file) and os.path.exists(max_brightness_file):
                        try:
                            with open(brightness_file, 'r') as bf, open(max_brightness_file, 'r') as mbf:
                                brightness_value = bf.read().strip()
                                max_brightness_value = mbf.read().strip()
                                
                                if not brightness_value.isdigit() or not max_brightness_value.isdigit():
                                    raise ValueError("Brightness values are not valid integers")
                                
                                brightness = int(brightness_value) / int(max_brightness_value) * 100  # Percentage
                        except ValueError as ve:
                            brightness = f"Error parsing brightness values: {ve}"
                        except Exception as e:
                            brightness = f"Error reading brightness files: {e}"
                        break  
            except FileNotFoundError as fnf:
                brightness = str(fnf)
            except Exception as e:
                brightness = f"Unexpected error: {e}"
        
        self.LogSys.print_and_log("\n[\u001b[35m*\u001b[0m] Brightness: %s" % brightness)


    def Memory_Checker(self):
        try:
            memory_info = psutil.virtual_memory()
            total_memory_gb = memory_info.total / (1024 ** 3)
            used_memory_gb = memory_info.used / (1024 ** 3)
            free_memory_gb = memory_info.available / (1024 ** 3)
        
            self.LogSys.print_and_log("\n[\u001b[35m*\u001b[0m] Memory Usage:", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Total Memory: {total_memory_gb:.2f} GB", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Used Memory: {used_memory_gb:.2f} GB", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Free Memory: {free_memory_gb:.2f} GB", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Memory Usage: {memory_info.percent}%\n", "debug")
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error retrieving memory information: {e}", "error")
    
    
    def Disk_Checker(self, directory='/'):
        try:
            disk_info = psutil.disk_usage(directory)
            total_disk_gb = disk_info.total / (1024 ** 3)
            used_disk_gb = disk_info.used / (1024 ** 3)
            free_disk_gb = disk_info.free / (1024 ** 3)
        
            self.LogSys.print_and_log("\n[\u001b[35m*\u001b[0m] Disk Usage:", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Total Disk: {total_disk_gb:.2f} GB", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Used Disk: {used_disk_gb:.2f} GB", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Free Disk: {free_disk_gb:.2f} GB", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Disk Usage: {disk_info.percent}%\n", "debug")
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error retrieving disk usage: {e}", "error")
    
    
    def Network_Checker(self):
        try:
            network_info = psutil.net_io_counters()
            bytes_sent_mb = network_info.bytes_sent / (1024 ** 2)
            bytes_recv_mb = network_info.bytes_recv / (1024 ** 2)
        
            self.LogSys.print_and_log("\n[\u001b[35m*\u001b[0m] Network Usage:", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Data Sent: {bytes_sent_mb:.2f} MB", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Data Received: {bytes_recv_mb:.2f} MB", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Packets Sent: {network_info.packets_sent}", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Packets Received: {network_info.packets_recv}\n", "debug")
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error retrieving network information: {e}", "error")
    
    
    def OS_Info(self):
        try:
            self.LogSys.print_and_log("\n[\u001b[35m*\u001b[0m] Operating System Information:", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m System: {platform.system()}", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Release: {platform.release()}", "debug")
            self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m Version: {platform.version()}\n", "debug")
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error retrieving OS information: {e}", "error")


    def Logged_Users(self):
        try:
            users = psutil.users()
            if not users:
                self.LogSys.print_and_log("[\u001b[35m*\u001b[0m] No users are currently logged in.", "debug")
                return
            
            self.LogSys.print_and_log("\n[\u001b[35m*\u001b[0m] Logged-in Users:", "debug")
            for index, user in enumerate(users):
                start_time = datetime.datetime.fromtimestamp(user.started).strftime("%Y-%m-%d %H:%M:%S")
                
                self.LogSys.print_and_log(f"    \u001b[36m├──\u001b[0m User {index+1}: {user.name}", "debug")
                self.LogSys.print_and_log(f"    \u001b[36m│   ├──\u001b[0m Terminal: {user.terminal or 'N/A'}", "debug")
                self.LogSys.print_and_log(f"    \u001b[36m│   ├──\u001b[0m Host: {user.host if user.host.strip() else 'Local'}", "debug")
                self.LogSys.print_and_log(f"    \u001b[36m│   ├──\u001b[0m Login Time: {start_time}", "debug")
    
            self.LogSys.print_and_log("", "debug") 
            
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error retrieving logged-in users: {e}", "error")
            
            
    def Start_Sensor(self):
        self.Uptime()
        self.CPU_Checker()
        self.Component_Temp_Checker()
        self.Battery_Checker()
        self.Fan_Checker()
        self.Brigthness_checker()
        self.Memory_Checker()
        self.Disk_Checker()
        self.Network_Checker()
        self.OS_Info()
        self.Logged_Users()













    
    
class RealTime_Dir:
    def __init__(self):
        self.LogSys = Logs()
        self.LogSys.LogEngine("SysMonitor - RealTime_Dir", "LogCore_SysMonitor")
        self.monitorFile = Path_Settings()
        
        # Robustly determine MainPath
        try:
            self.MainPath = self.monitorFile.checkpath("Server-FrameworkPath")
            if not self.MainPath or not os.path.isdir(self.MainPath):
                raise ValueError("Main path not found or invalid")
            self.LogSys.LogsMessages(f"MainPath set to: {self.MainPath}", "INFO")
        except Exception as e:
            self.LogSys.LogsMessages(f"[\u001b[31m!\u001b[0m]  Failed to get Server-FrameworkPath: {e}", "CRITICAL")
            # Fallback: Walk up from current file to find project root
            current_dir = os.path.dirname(__file__)
            while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
                if os.path.basename(current_dir) == "Server-Framework":
                    self.MainPath = current_dir
                    self.LogSys.LogsMessages(f"Fallback: MainPath resolved to {self.MainPath}", "INFO")
                    break
                current_dir = os.path.dirname(current_dir)
            else:
                self.MainPath = os.path.dirname(__file__)  # Last resort
                self.LogSys.LogsMessages(f"Last resort: MainPath set to {self.MainPath}", "WARNING")
        
        # Ensure MainPath is valid before proceeding
        if not os.path.isdir(self.MainPath):
            self.LogSys.LogsMessages(f"[\u001b[31m!\u001b[0m]  MainPath {self.MainPath} is not a directory, cannot monitor", "CRITICAL")
            raise ValueError(f"Invalid MainPath: {self.MainPath}")

        # Set LogPath with a fallback
        self.LogPath = self.monitorFile.checkpath("Server-FrameworkLogs")
        if not self.LogPath or not os.path.isdir(self.LogPath):
            self.LogPath = os.path.join(self.MainPath, "Logs")
            self.LogSys.LogsMessages(f"LogPath not found, defaulting to: {self.LogPath}", "WARNING")
            os.makedirs(self.LogPath, exist_ok=True)

        self.snapshot = {}
        self.snapshot_log = {}
        self.monitorPath = Paths_Manager()
        self.monitorLog = ManageLogDir()


    def take_snapshot(self):

        try:
            self.LogSys.LogsMessages("[+] Taking a snapshot")
            self.snapshot.clear()
            for root, dirs, files in os.walk(self.MainPath):          
                for folder in dirs:
                    folder_path = os.path.join(root, folder)
                    relative_path = os.path.relpath(folder_path, self.MainPath)
                    self.snapshot[relative_path] = os.path.getmtime(folder_path)
    
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.MainPath)
                    if relative_path == 'Logs/SysMonitor.log' or relative_path == 'Logs\\SysMonitor.log':
                        continue 
                    self.snapshot[relative_path] = os.path.getmtime(file_path)
        
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error taking snapshot: {e}", "error")
 
 
    def monitor_changes(self):
        try:
            current_state = {}
    
            for root, dirs, files in os.walk(self.MainPath):
                    
                for folder in dirs:
                    folder_path = os.path.join(root, folder)
                    relative_path = os.path.relpath(folder_path, self.MainPath)
                    current_state[relative_path] = os.path.getmtime(folder_path)
    
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.MainPath)
                    if relative_path == 'Logs/SysMonitor.log' or relative_path == 'Logs\\SysMonitor.log':
                        continue 
                    current_state[relative_path] = os.path.getmtime(file_path)
    
            added_items = set(current_state.keys()) - set(self.snapshot.keys())
            removed_items = set(self.snapshot.keys()) - set(current_state.keys())
            modified_items = {item for item in set(self.snapshot.keys()) & set(current_state.keys()) if (self.snapshot[item] != current_state[item])} 
    
            if added_items or removed_items or modified_items:
                self.alert_user(added_items, removed_items, modified_items)
    
            self.snapshot = current_state
        except Exception as e:
            self.LogSys.print_and_log(f"[\u001b[31m!\u001b[0m]  Error monitoring changes: {e}", "error")


    def alert_user(self, added_items, removed_items, modified_items):
        self.LogSys.LogsMessages("Change detected:", "debug")
        if added_items:
            self.LogSys.LogsMessages(f"[#] Added items: {added_items}", "debug")
            file_path = added_items.pop()
            SecFile = os.path.split(file_path)
            self.Take_Action(add=True, Folder=SecFile[0], File=SecFile[-1])

        if removed_items:
            self.LogSys.LogsMessages(f"[#] Removed items: {removed_items}", "debug")
            file_path = removed_items.pop()
            SecFile = os.path.split(file_path)
            self.Take_Action(remove=True, Folder=SecFile[0], File=SecFile[-1])

        if modified_items:
            self.LogSys.LogsMessages(f"[#] Modified items: {modified_items}", "debug")
            file_path = modified_items.pop()
            SecFile = os.path.split(file_path)

        self.LogSys.LogsMessages("\n", "debug")


    def Take_Action(self, add=False, remove=False, modified=False, Folder=None, File=None):
        if add:
            self.monitorPath.SectionPath(Folder)  # Create section if it doesn’t exist
            self.monitorPath.add_path(Folder, File, os.path.join(self.MainPath, Folder, File))  # Add the new path
            self.monitorLog.MainLog()  # Update log directory
        
        elif remove:
            if Folder == "Logs":
                self.monitorLog.MainLog()  # Handle log directory changes
            else:
                self.monitorPath.remove_path(section=Folder, pathname=File)  # Remove specific path
                self.monitorPath.GeneralPaths()  # Ensure general paths are intact
        
        elif modified:
            self.monitorPath.GeneralPaths()  # Refresh general paths
            # Optionally update the modified path if needed
            if Folder and File:
                self.monitorPath.add_path(Folder, File, os.path.join(self.MainPath, Folder, File))


    def Start_Monitor(self):
        self.take_snapshot()
        while True:
            time.sleep(1)
            self.monitor_changes()











class RealTime_Process:
    def __init__(self):
        self.LogSys = Logs()
        self.LogSys.LogEngine("SysMonitor - RealTime_Process", "LogCore_SysMonitor")
        self.monitorFile = Path_Settings()
        self.MainPath = self.monitorFile.checkpath("Server-FrameworkPath")
    
    def ProcessAlert(self, script_name_alert):
        notification_title = "Information"
        notification_message = f"Script started: {script_name_alert}"
        self.send_notification(notification_title, notification_message)


    def send_notification(self, title, message):
        try:
            if notification is None:
                self.LogSys.LogsMessages("Desktop notifications unavailable (plyer not installed).")
            elif platform.system() == "Linux":
                notification.notify(
                    title=title,
                    message=message,
                    timeout=10,
                )
            else:
                self.LogSys.LogsMessages("Unsupported operating system for notifications.")
        except Exception as e:
            self.LogSys.LogsMessages(f"[\u001b[31m!\u001b[0m]  Error sending notification: {e}", "error")
    
        notification_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.LogSys.LogsMessages(f"Notification sent at: {notification_timestamp}")




if __name__ == "__main__":
    Sensor().Start_Sensor()
    #RealTime_Dir().Start_Monitor()
    #RealTime_Process().ProcessInfo("simple_socketTCP_server.py", 34113)
    
    


