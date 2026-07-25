from flask import Flask, request, jsonify, redirect, url_for, render_template, send_file
from BlueWeb import run_bluetooth_scan
from WebSysMonitor import Sensor, PersonalInfo
from BluewebParseai import BlueAi
import asyncio
import csv
import os
import io

app = Flask(__name__)
# A secret key is required for secure session/flash handling. Override via env.
app.config["SECRET_KEY"] = os.environ.get("SERVER_FRAMEWORK_SECRET_KEY", os.urandom(24).hex())

users = {
    "admin": "admin123",
    "demon": "demon123"
}

messages = []
wifi_messages = []  # List for Wi-Fi-specific messages
latest_bluetooth_devices = []  # Store latest scan results for download

# Define the help message
help_message = """
*---------------------------------------------------------------------*
| Command   | Description                                             |
*---------------------------------------------------------------------|
|  exit     | Exit the dashboard and terminate the program            |
*---------------------------------------------------------------------|
|  list     | List available modes and scripts                        |
*---------------------------------------------------------------------|
|  rename   | Rename a running script                                 |
*---------------------------------------------------------------------|
|  stop     | Stop a running script                                   |
*---------------------------------------------------------------------|
|  stop_all | Stop all running scripts                                |
*---------------------------------------------------------------------|
|  restart  | Restart a running script                                |
*---------------------------------------------------------------------|
|  map      | Display available modes (map)                           |
*---------------------------------------------------------------------|
|  info     | Start system information and monitoring                 |
*---------------------------------------------------------------------|
|  show     | Show running scripts and their status                   |
*---------------------------------------------------------------------|
|  Admin    | Connect to the admin panel                              |
*---------------------------------------------------------------------|
|  Web      | Launch the web dashboard on localhost                   |
*---------------------------------------------------------------------|
|  upload   | Upload files or data to the admin panel                 |
*---------------------------------------------------------------------|
|  download | Download files or data from the admin panel             |
*---------------------------------------------------------------------|
|  read     | Read a file or data from the admin panel                |
*---------------------------------------------------------------------|
|  delete   | Delete a file or data from the admin panel              |
*---------------------------------------------------------------------|
|  execute  | Execute a specific task or script in the admin panel    |
*---------------------------------------------------------------------|
|  help     | Display this help message                               |
*---------------------------------------------------------------------*
"""

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            messages.append(f"Info: User {username} logged in successfully")
            return redirect(url_for('dashboard', username=username))
        else:
            error = "Invalid credentials. Please try again."
    return render_template('0xLogin.html', error=error)

@app.route('/dashboard/<username>')
def dashboard(username):
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    return render_template('0xDashboard.html', username=username, messages=messages)

@app.route('/help/<username>')
def help(username):
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    
    messages.append(help_message.strip())
    return redirect(url_for('dashboard', username=username))

@app.route('/0XHelp/<username>')
def xhelp(username):
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    
    return render_template('0xHelp.html', username=username)

@app.route('/wifi/<username>')
def wifi(username):
    if username not in users:
        wifi_messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    
    # Placeholder for Wi-Fi functionality
    if not wifi_messages:
        wifi_messages.append("Info: Welcome to 0xWIFI. Select an option to begin.")
    
    return render_template('0xWIFI.html', username=username, wifi_messages=wifi_messages)

@app.route('/bluetooth/<username>')
def bluetooth(username):
    global latest_bluetooth_devices
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    
    should_scan = request.args.get('scan', '').lower() == 'true'
    should_ai_scan = request.args.get('aiscan', '').lower() == 'true'
    scan_completed = False
    
    if should_scan:
        try:
            status_messages, bluetooth_devices = run_bluetooth_scan(scan_duration=10, verbose=True)
            # Add default VulnerabilityReport for regular scan
            bluetooth_devices = [
                {
                    "Name": device["Name"],
                    "Address": device["Address"],
                    "RSSI": device["RSSI"],
                    "Distance": device["Distance"],
                    "Status": device["Status"],
                    "UUID": device["UUID"],
                    "Timestamp": device["Timestamp"],
                    "VulnerabilityReport": "N/A"
                } for device in bluetooth_devices
            ]
            latest_bluetooth_devices = bluetooth_devices  # Store for download
            if status_messages:
                status_messages = "Scan Completed Successfully.\nYou can Download the results"
            scan_completed = True
        except Exception as e:
            status_messages = f"Error scanning Bluetooth devices: {str(e)}"
            bluetooth_devices = []
            latest_bluetooth_devices = []
    elif should_ai_scan:
        try:
            scanner = BlueAi(verbose=True)
            # Run the async analyze_devices and capture results
            ai_reports = asyncio.run(scanner.analyze_devices())
            # Transform AI reports to match table structure
            bluetooth_devices = [
                {
                    "Name": row["Name"],
                    "Address": row["MAC Address"],
                    "RSSI": row["RSSI (dBm)"],
                    "Distance": row["Distance (Meter)"],
                    "Status": row["Range"],
                    "UUID": "",  # UUID not included in report
                    "Timestamp": "",  # Timestamp not included
                    "VulnerabilityReport": row["Vulnerability Report"]
                } for row in ai_reports
            ]
            latest_bluetooth_devices = bluetooth_devices  # Store for download
            status_messages = "AI Scan Completed Successfully.\nVulnerability reports generated. \nYou can Download the results"
            scan_completed = True
            # Check if CSV exists as a fallback
            filename = "Blue_AI_Report.csv"
            if not bluetooth_devices and os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    bluetooth_devices = [
                        {
                            "Name": row["Name"],
                            "Address": row["MAC Address"],
                            "RSSI": row["RSSI (dBm)"],
                            "Distance": row["Distance (Meter)"],
                            "Status": row["Range"],
                            "UUID": "",
                            "Timestamp": "",
                            "VulnerabilityReport": row["Vulnerability Report"]
                        } for row in reader
                    ]
                    latest_bluetooth_devices = bluetooth_devices
                status_messages = "AI Scan Completed Successfully.\nVulnerability reports loaded from CSV."
            if not bluetooth_devices:
                status_messages = "AI Scan completed, but no devices were found."
        except Exception as e:
            status_messages = f"Error during AI scan: {str(e)}"
            bluetooth_devices = []
            latest_bluetooth_devices = []
    else:
        status_messages = "[!] No scan performed. Please select a scan option."
        bluetooth_devices = latest_bluetooth_devices
        scan_completed = len(bluetooth_devices) > 0  # Set to True if devices exist from a previous scan

    return render_template('0xBluetooth.html', username=username, status_messages=status_messages, bluetooth_devices=bluetooth_devices, scan_completed=scan_completed)

@app.route('/download_scan_report/<username>')
def download_scan_report(username):
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    
    if not latest_bluetooth_devices:
        note = "Error: No scan results available to download"
        return redirect(url_for('bluetooth', username=username))
    
    # Generate CSV in memory
    output = io.StringIO()
    fieldnames = ["Name", "Address", "RSSI (dBm)", "Distance", "Status", "UUID", "Timestamp", "Vulnerability Report"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for device in latest_bluetooth_devices:
        writer.writerow({
            "Name": device["Name"],
            "Address": device["Address"],
            "RSSI (dBm)": device["RSSI"],
            "Distance": device["Distance"],
            "Status": device["Status"],
            "UUID": device["UUID"],
            "Timestamp": device["Timestamp"],
            "Vulnerability Report": device["VulnerabilityReport"]
        })
    
    # Prepare response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='Bluetooth_Scan_Report.csv'
    )

# Commented out as the "Download AI Scan Report" button is removed from 0xBluetooth.html
# @app.route('/download_ai_scan_report/<username>')
# def download_ai_scan_report(username):
#     if username not in users:
#         messages.append("Error: Unauthorized access attempt")
#         return redirect(url_for('login'))
#     
#     filename = "Blue_AI_Report.csv"
#     if not os.path.exists(filename):
#         note = "Error: No AI scan report available to download"
#         return redirect(url_for('bluetooth', username=username))
#     
#     return send_file(
#         filename,
#         mimetype='text/csv',
#         as_attachment=True,
#         download_name='Bluetooth_AI_Scan_Report.csv'
#     )

@app.route('/info/<username>')
def info(username):
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    sys = Sensor()
    message = sys.Start_Sensor()
    if message:
        messages.append(message)
    else:
        messages.append("Error: Failed to start system information monitoring")
    return redirect(url_for('dashboard', username=username))

@app.route('/myinfo/<username>')
def myinfo(username):
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    my = PersonalInfo()
    message = my.run()
    if message:
        for line in message:
            messages.append(line)
    else:
        messages.append("Error: Failed to start personal information monitoring")
    return redirect(url_for('dashboard', username=username))

@app.route('/clear_dashboard_messages/<username>')
def clear_dashboard_messages(username):
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    
    messages.clear()
    messages.append("Messages cleared.")
    return redirect(url_for('dashboard', username=username))

@app.route('/clear_wifi_messages/<username>')
def clear_wifi_messages(username):
    if username not in users:
        wifi_messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    
    wifi_messages.clear()
    wifi_messages.append("Messages cleared.")
    return redirect(url_for('wifi', username=username))

@app.route('/change_password/<username>', methods=['POST'])
def change_password(username):
    if username not in users:
        messages.append("Error: Unauthorized access attempt")
        return redirect(url_for('login'))
    
    new_password = request.form['new_password']
    if new_password:
        users[username] = new_password
        messages.append(f"Success: Password updated for {username}")
    else:
        messages.append("Error: New password cannot be empty")
    
    return redirect(url_for('dashboard', username=username))

@app.route('/logout')
def logout():
    messages.append("Info: User logged out")
    return redirect(url_for('login'))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Server-Framework web dashboard")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Interface to bind (default: 127.0.0.1; use 0.0.0.0 to expose)")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable Flask debug mode (disabled by default; do NOT use in production)")
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=args.debug)
