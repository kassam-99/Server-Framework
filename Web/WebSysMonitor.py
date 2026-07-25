import datetime
import time
import psutil
import platform
import os


import socket
import uuid
import requests


class Sensor:
    def __init__(self):
        self.output = []

    def CPU_Checker(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            self.output.append(f"CPU Usage: {cpu_percent}%")
        except Exception as e:
            self.output.append(f"Error checking CPU usage: {e}")

    def Uptime(self):
        try:
            uptime = round(time.time() - psutil.boot_time())
            self.output.append(f"System Uptime: {datetime.timedelta(seconds=uptime)}")
        except Exception as e:
            self.output.append(f"Error checking system uptime: {e}")

    def Component_Temp_Checker(self):
        try:
            if not hasattr(psutil, "sensors_temperatures"):
                self.output.append("Temperature sensor data not available on this system.")
                return

            component_details = psutil.sensors_temperatures()
            if not component_details:
                self.output.append("No temperature data detected.")
                return

            self.output.append("Component Temperatures:")
            for sensor, readings in component_details.items():
                self.output.append(f"  Sensor: {sensor}")
                if readings:
                    for check in readings:
                        label = check.label if check.label else "Unnamed"
                        self.output.append(
                            f"    {label}: {check.current}°C (High: {check.high if check.high else 'N/A'}°C, "
                            f"Critical: {check.critical if check.critical else 'N/A'}°C)"
                        )
                else:
                    self.output.append(f"    No data available for {sensor}")
                self.output.append("")
        except Exception as e:
            self.output.append(f"Error checking component temperatures: {e}")

    def Battery_Checker(self):
        try:
            self.output.append("Battery:")
            if not hasattr(psutil, "sensors_battery"):
                self.output.append("  Battery information not available on this system.")
                return

            battery_details = psutil.sensors_battery()
            if battery_details is None:
                self.output.append("  No battery detected or system does not support battery status.")
                return

            power_plugged = battery_details.power_plugged
            battery_percent = battery_details.percent
            secsleft = battery_details.secsleft

            if power_plugged:
                self.output.append("  Power Plugged")
                status = "Charging" if battery_percent is not None and battery_percent < 100 else "Fully charged"
                self.output.append(f"  Status: {status}")
            else:
                self.output.append("  Power Unplugged")
                self.output.append("  Status: Discharging")

            if battery_percent is not None:
                self.output.append(f"  Battery Percentage: {round(battery_percent, 2)}%")
            else:
                self.output.append("  Battery percentage could not be retrieved.")

            if secsleft in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN):
                self.output.append("  Time Left: Not available")
            else:
                self.output.append(f"  Time Left: {datetime.timedelta(seconds=secsleft)}")

            self.output.append("")
        except Exception as e:
            self.output.append(f"Error retrieving battery information: {e}")

    def Fan_Checker(self):
        try:
            if not hasattr(psutil, "sensors_fans"):
                self.output.append("Fan sensor data not available on this system.")
                return

            fan_details = psutil.sensors_fans()
            if not fan_details:
                self.output.append("No fan data detected.")
                return

            self.output.append("Fan Status:")
            for fan_name, readings in fan_details.items():
                self.output.append(f"  Fan Controller: {fan_name}")
                if readings:
                    for fan in readings:
                        self.output.append(f"    {fan.label or 'Unnamed'}: {fan.current} RPM")
                else:
                    self.output.append("    No data available.")
                self.output.append("")
        except Exception as e:
            self.output.append(f"Error checking fan status: {e}")

    def Brightness_Checker(self):
        brightness = "N/A"
        system = platform.system()

        if system == "Linux":
            backlight_path = "/sys/class/backlight/"
            try:
                if not os.path.exists(backlight_path):
                    raise FileNotFoundError("Backlight path not found")

                backlight_dirs = [d for d in os.listdir(backlight_path) if os.path.isdir(os.path.join(backlight_path, d))]
                if not backlight_dirs:
                    raise FileNotFoundError("No backlight devices found")

                for device in backlight_dirs:
                    brightness_file = os.path.join(backlight_path, device, "brightness")
                    max_brightness_file = os.path.join(backlight_path, device, "max_brightness")

                    if os.path.exists(brightness_file) and os.path.exists(max_brightness_file):
                        with open(brightness_file, "r") as bf, open(max_brightness_file, "r") as mbf:
                            brightness_value = bf.read().strip()
                            max_brightness_value = mbf.read().strip()

                            if not brightness_value.isdigit() or not max_brightness_value.isdigit():
                                raise ValueError("Brightness values are not valid integers")

                            brightness = int(brightness_value) / int(max_brightness_value) * 100
                            brightness = f"{round(brightness, 2)}%"
                            break
            except FileNotFoundError as fnf:
                brightness = f"Error: {fnf}"
            except ValueError as ve:
                brightness = f"Error parsing brightness values: {ve}"
            except Exception as e:
                brightness = f"Unexpected error: {e}"
        else:
            brightness = "Brightness checking not supported on this platform."

        self.output.append(f"Brightness: {brightness}")

    def Memory_Checker(self):
        try:
            memory_info = psutil.virtual_memory()
            total_memory_gb = memory_info.total / (1024 ** 3)
            used_memory_gb = memory_info.used / (1024 ** 3)
            free_memory_gb = memory_info.available / (1024 ** 3)

            self.output.append("Memory Usage:")
            self.output.append(f"  Total Memory: {total_memory_gb:.2f} GB")
            self.output.append(f"  Used Memory: {used_memory_gb:.2f} GB")
            self.output.append(f"  Free Memory: {free_memory_gb:.2f} GB")
            self.output.append(f"  Memory Usage: {memory_info.percent}%")
            self.output.append("")
        except Exception as e:
            self.output.append(f"Error retrieving memory information: {e}")

    def Disk_Checker(self, directory='/'):
        try:
            disk_info = psutil.disk_usage(directory)
            total_disk_gb = disk_info.total / (1024 ** 3)
            used_disk_gb = disk_info.used / (1024 ** 3)
            free_disk_gb = disk_info.free / (1024 ** 3)

            self.output.append("Disk Usage:")
            self.output.append(f"  Total Disk: {total_disk_gb:.2f} GB")
            self.output.append(f"  Used Disk: {used_disk_gb:.2f} GB")
            self.output.append(f"  Free Disk: {free_disk_gb:.2f} GB")
            self.output.append(f"  Disk Usage: {disk_info.percent}%")
            self.output.append("")
        except Exception as e:
            self.output.append(f"Error retrieving disk usage: {e}")

    def Network_Checker(self):
        try:
            network_info = psutil.net_io_counters()
            bytes_sent_mb = network_info.bytes_sent / (1024 ** 2)
            bytes_recv_mb = network_info.bytes_recv / (1024 ** 2)

            self.output.append("Network Usage:")
            self.output.append(f"  Data Sent: {bytes_sent_mb:.2f} MB")
            self.output.append(f"  Data Received: {bytes_recv_mb:.2f} MB")
            self.output.append(f"  Packets Sent: {network_info.packets_sent}")
            self.output.append(f"  Packets Received: {network_info.packets_recv}")
            self.output.append("")
        except Exception as e:
            self.output.append(f"Error retrieving network information: {e}")

    def OS_Info(self):
        try:
            self.output.append("Operating System Information:")
            self.output.append(f"  System: {platform.system()}")
            self.output.append(f"  Release: {platform.release()}")
            self.output.append(f"  Version: {platform.version()}")
            self.output.append("")
        except Exception as e:
            self.output.append(f"Error retrieving OS information: {e}")

    def Logged_Users(self):
        try:
            users = psutil.users()
            if not users:
                self.output.append("No users are currently logged in.")
                return

            self.output.append("Logged-in Users:")
            for index, user in enumerate(users):
                start_time = datetime.datetime.fromtimestamp(user.started).strftime("%Y-%m-%d %H:%M:%S")
                self.output.append(f"  User {index + 1}: {user.name}")
                self.output.append(f"    Terminal: {user.terminal or 'N/A'}")
                self.output.append(f"    Host: {user.host if user.host.strip() else 'Local'}")
                self.output.append(f"    Login Time: {start_time}")
                self.output.append("")
        except Exception as e:
            self.output.append(f"Error retrieving logged-in users: {e}")

    def Start_Sensor(self):
        self.output = []  # Clear output before starting
        self.Uptime()
        self.CPU_Checker()
        self.Component_Temp_Checker()
        self.Battery_Checker()
        self.Fan_Checker()
        self.Brightness_Checker()
        self.Memory_Checker()
        self.Disk_Checker()
        self.Network_Checker()
        self.OS_Info()
        self.Logged_Users()
        return "\n".join(self.output)
    

class PersonalInfo:
    def __init__(self):
        self.output = []

    def get_local_ip(self):
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return hostname, local_ip

    def get_mac_address(self):
        mac = uuid.getnode()
        mac_address = ':'.join(['{:02x}'.format((mac >> ele) & 0xff) for ele in range(40, -8, -8)])
        return mac_address

    def get_public_ip(self):
        try:
            public_ip = requests.get("https://api.ipify.org").text
        except requests.RequestException:
            public_ip = "Could not fetch public IP"
        return public_ip

    def run(self):
        hostname, local_ip = self.get_local_ip()
        mac_address = self.get_mac_address()
        public_ip = self.get_public_ip()
        self.output.append(f"Hostname    : {hostname}")
        self.output.append(f"Local IP    : {local_ip}")
        self.output.append(f"Public IP   : {public_ip}")
        self.output.append(f"MAC Address : {mac_address}")
        return self.output

if __name__ == "__main__":
    sensor = Sensor()
    print(sensor.Start_Sensor())

    # Example usage of PersonalInfo (performs a live network request).
    info = PersonalInfo()
    info.run()
    for line in info.output:
        print(line)