import json
import glob
import os
import asyncio
from datetime import datetime
import csv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from bleak import BleakClient, BleakError
except ImportError:
    BleakClient = None

    class BleakError(Exception):
        """Fallback error type used when bleak is not installed."""
        pass

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False


class BlueAi:
    def __init__(self, verbose=False):
        self.verbose = verbose
        if OpenAI is None:
            raise ImportError("openai is not installed; AI vulnerability analysis is unavailable.")
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=api_key)
        self.report_data = []
        self.selected_mac_address = None

    def get_files(self):
        data = glob.glob("BlueDiscoverJSON*")
        if not data:
            if self.verbose:
                print("No files found matching 'BlueDiscoverJSON*'")
            return None
        
        newest_file = max(data, key=os.path.getmtime)
        if self.verbose:
            print(f"Selected newest file: {newest_file}")
        self.selected_mac_address = newest_file
        return self.selected_mac_address

    def open_file(self):
        self.selected_mac_address = self.get_files()
        if not self.selected_mac_address:
            if self.verbose:
                print("No file selected.")
            return {}

        try:
            with open(self.selected_mac_address, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < 3:
                    if self.verbose:
                        print("File too short to contain expected JSON data.")
                    return {}
                json_data = "".join(lines[3:])
                data = json.loads(json_data)
        except (IOError, json.JSONDecodeError) as e:
            if self.verbose:
                print(f"Error reading or parsing {self.selected_mac_address}: {e}")
            return {}

        devices = data[0] if data and isinstance(data, list) and isinstance(data[0], dict) else {}
        transformed_devices = {}
        for mac, details in devices.items():
            transformed_devices[mac] = {
                "mac": mac,
                "name": details["Name"],
                "rssi": details["RSSI"],
                "distance": details["Distance"],
                "status": details["Status"],
                "uuid": details["UUID"],
                "timestamp": details["Timestamp"]
            }

        if self.verbose:
            print(f"Mac Addresses in {self.selected_mac_address}")
            if transformed_devices:
                for i, mac in enumerate(transformed_devices.keys(), start=1):
                    print(f"|{i}| ------ |{mac}|")
            print(f"\n[!] Found {len(transformed_devices)} devices")
        return transformed_devices

    async def get_gatt_info(self, mac):
        if BleakClient is None:
            return {"mac": mac, "error": "bleak not installed"}
        try:
            async with BleakClient(mac, timeout=20.0) as client:
                if self.verbose:
                    print(f"Connected to {mac}, extracting GATT services...")
                services = await client.get_services()
                gatt_info = {"mac": mac, "connected": True, "services": []}
                for service in services:
                    service_data = {"uuid": service.uuid, "characteristics": []}
                    for char in service.characteristics:
                        char_data = {
                            "uuid": char.uuid,
                            "properties": char.properties,
                            "readable": "read" in char.properties,
                            "writable": any(prop in char.properties for prop in ["write", "write-without-response"]),
                            "value": None
                        }
                        if char_data["readable"]:
                            try:
                                value = await client.read_gatt_char(char.uuid)
                                char_data["value"] = value.hex() if value else "Empty"
                            except Exception:
                                char_data["value"] = "Read failed"
                        service_data["characteristics"].append(char_data)
                    gatt_info["services"].append(service_data)
                return gatt_info
        except BleakError as e:
            if self.verbose:
                print(f"Bleak error for {mac}: {e}")
            return {"mac": mac, "error": f"Bleak error: {e}"}
        except Exception as e:
            if self.verbose:
                print(f"Unexpected error for {mac}: {e}")
            return {"mac": mac, "error": f"Unexpected error: {e}"}

    def Ai_Ble_Scan(self, device_info, gatt_info):
        prompt = (
            "Analyze the following Bluetooth Low Energy (BLE) device for potential vulnerabilities:\n"
            f"MAC Address: {device_info.get('mac', 'N/A')}\n"
            f"Name: {device_info.get('name', 'Unknown')}\n"
            f"RSSI: {device_info.get('rssi', 'Unknown')} dBm\n"
            f"UUID: {device_info.get('uuid', 'Unknown')}\n\n"
            "GATT Services and Characteristics:\n"
        )
        if gatt_info.get("error"):
            prompt += f"Error: {gatt_info['error']}\n"
        else:
            for service in gatt_info.get("services", []):
                prompt += f" - Service UUID: {service['uuid']}\n"
                for char in service["characteristics"]:
                    prompt += f"   - Characteristic UUID: {char['uuid']}\n"
                    prompt += f"     Properties: {char['properties']}\n"
                    if char["readable"] and char["value"]:
                        prompt += f"     Value: {char['value']}\n"
        prompt += (
            "\nBased on this information, what are the potential security risks or known vulnerabilities "
            "for this BLE device? Include specific concerns related to the GATT services and characteristics."
            "Mention the CVE IDs for potential vulnerabilities if applicable."
        )
        try:
            if self.verbose:
                print("[!] Querying AI For Vulnerability Assessment...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You Are A professional Bluetooth security analyst."},
                          {"role": "user", "content": prompt}],
                max_tokens=600
            )
            vuln_report = response.choices[0].message.content
            if self.verbose:
                print(f"Vulnerability Report:\n{vuln_report}\n{'-'*50}")
            return vuln_report
        except Exception as e:
            error_msg = f"Error Querying OpenAI API: {e}"
            if self.verbose:
                print(error_msg)
            return error_msg

    def save_device_reports(self, device, gatt_info=None, vuln_report=None):
        mac = device["mac"]
        report_row = {
            "MAC Address": mac,
            "Name": device["name"],
            "RSSI (dBm)": device["rssi"],
            "Distance (Meter)": device["distance"],
            "Range": device["status"],
            "Manufacturer": device.get("manufacturer", "Unknown"),
            "Vulnerability Report": vuln_report.strip() if vuln_report else "Not connected - no vulnerability analysis performed"
        }
        self.report_data.append(report_row)
        if self.verbose:
            print(f"[!] Report data saved for {mac}")

    def write_csv_report(self):
        if not self.report_data:
            if self.verbose:
                print("No report data to save.")
            return
        fieldnames = ["MAC Address", "Name", "RSSI (dBm)", "Distance (Meter)", "Range", "Manufacturer", "Vulnerability Report"]
        timestamp = datetime.now().strftime("%d%m%Y")
        filename = f"Blue_AI_Report_{timestamp}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.report_data)
        if self.verbose:
            print(f"[!] Consolidated report saved to {filename}")

    async def analyze_devices(self):
        devices = self.open_file()
        if not devices:
            if self.verbose:
                print("No devices to analyze.")
            return []
        for mac, device_info in devices.items():
            if self.verbose:
                print(f"\nProcessing {device_info['name']} ({mac})...")
            gatt_info = await self.get_gatt_info(mac)
            if gatt_info.get("connected", False):
                vuln_report = self.Ai_Ble_Scan(device_info, gatt_info)
                self.save_device_reports(device_info, gatt_info, vuln_report)
            else:
                self.save_device_reports(device_info)
        self.write_csv_report()
        return self.report_data

if __name__ == "__main__":
    scanner = BlueAi(verbose=True)
    asyncio.run(scanner.analyze_devices())