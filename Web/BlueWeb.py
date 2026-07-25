import asyncio
from datetime import datetime
from Web_Logs import Logs
from ReportGenerator import Report_Generator

try:
    from bleak import BleakScanner
except ImportError:
    BleakScanner = None


class BloodDiscover:
    def __init__(self, scan_duration=20, verbose=False):
        self.verbose = verbose
        self.scan_duration = scan_duration
        self.discovered_devices = {}
        self.logger_web = Logs()
        self.report_txt = Report_Generator()
        self.logger_web.LogEngine("WebSpiderBlueLogs", "BluetoothDiscover")
        self.output = []  # For status messages (e.g., "Scanning...", "Scanner started...")
        self.devices_list = []  # For structured device data

    def calculate_distance(self, rssi, A=-59, n=2):
        if rssi == 0:
            return -1
        return 10 ** ((A - rssi) / (10 * n))

    def classify_connection(self, rssi):
        if rssi > -50:
            return "Strong Connection"
        elif -70 <= rssi <= -50:
            return "Moderate Connection"
        else:
            return "Weak Connection"

    def on_device_discovered(self, device, advertisement_data):
        if device.rssi is not None:
            device_name = device.name if device.name else "Unknown"
            distance = self.calculate_distance(device.rssi)
            mac_address = device.address

            if mac_address in self.discovered_devices:
                if device.rssi > self.discovered_devices[mac_address]["RSSI"]:
                    self.discovered_devices[mac_address]["RSSI"] = device.rssi
                    self.discovered_devices[mac_address]["Distance"] = distance
                    self.discovered_devices[mac_address]["Status"] = self.classify_connection(device.rssi)
                    self.discovered_devices[mac_address]["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if advertisement_data.local_name:
                        self.discovered_devices[mac_address]["Name"] = advertisement_data.local_name
                    if advertisement_data.service_uuids:
                        self.discovered_devices[mac_address]["UUID"] = advertisement_data.service_uuids[0]
                    if self.verbose:
                        self.output.append(f"[+] Updated device {mac_address} with stronger RSSI: {device.rssi}")
            else:
                self.discovered_devices[mac_address] = {
                    "Name": device_name,
                    "RSSI": device.rssi,
                    "Distance": distance,
                    "Status": self.classify_connection(device.rssi),
                    "UUID": advertisement_data.service_uuids[0] if advertisement_data.service_uuids else "No UUID Advertised",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if self.verbose:
                    self.output.append(f"[!] New device stored: {mac_address} with RSSI: {device.rssi}")

    async def scan_ble_devices(self):
        if BleakScanner is None:
            self.output.append("[!] bleak is not installed; BLE scanning is unavailable.")
            return
        self.output.append(f"Scanning for BLE devices for {self.scan_duration} seconds...")
        scanner = BleakScanner()
        scanner.register_detection_callback(self.on_device_discovered)
        await scanner.start()
        self.output.append("Scanner started...")
        await asyncio.sleep(self.scan_duration)
        await scanner.stop()
        self.output.append("Scanner stopped.")
        self.display_results()

    def display_results(self):
        if not self.discovered_devices:
            self.output.append("No devices found.")
            return

        self.output.append("\nScan Complete. Devices Found:\n")
        for mac, info in self.discovered_devices.items():
            device_info = {
                "Name": info["Name"],
                "Address": mac,
                "RSSI": info["RSSI"],
                "Distance": f"{info['Distance']:.2f} meters",
                "Status": info["Status"],
                "UUID": info["UUID"],
                "Timestamp": info["Timestamp"]
            }
            self.devices_list.append(device_info)
            # Keep the string output for logging purposes
            self.output.append(f"Device Name       : {info['Name']}")
            self.output.append(f"Device Address    : {mac}")
            self.output.append(f"RSSI (dBm)        : {info['RSSI']}")
            self.output.append(f"Estimated Distance: {info['Distance']:.2f} meters")
            self.output.append(f"Connection Status : {info['Status']}")
            self.output.append(f"Device UUID       : {info['UUID']}")
            self.output.append(f"Timestamp         : {info['Timestamp']}")
            self.output.append("-" * 50)

        Device_count = len(self.discovered_devices)
        self.output.append(f"\n[!] Total Devices Found: {Device_count}")
        self.output.append("-" * 50)

        bluelist = [self.discovered_devices]
        #self.report_txt.TXT_GenerateReport(Data=bluelist, filename="BlueDiscoverTXT")
        self.report_txt.JSON_GenerateReport(Data=bluelist, filename="BlueDiscoverJSON")


def run_bluetooth_scan(scan_duration=20, verbose=False):
    """
    Synchronous wrapper to run the Bluetooth scan and return the results.
    Returns a tuple: (status_messages, devices_list)
    - status_messages: List of status messages (e.g., "Scanning...", "Scanner started...")
    - devices_list: List of dictionaries containing device details
    """
    # Create an instance of BloodDiscover
    scanner = BloodDiscover(scan_duration=scan_duration, verbose=verbose)
    
    # Run the asynchronous scan_ble_devices method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(scanner.scan_ble_devices())
    finally:
        loop.close()
    
    # Return both the status messages and the structured device list
    return scanner.output, scanner.devices_list


if __name__ == "__main__":
    # Test the script standalone
    status_messages, devices = run_bluetooth_scan(scan_duration=10, verbose=True)
    print("Status Messages:")
    for line in status_messages:
        print(line)
    print("\nDevices List:")
    for device in devices:
        print(device)