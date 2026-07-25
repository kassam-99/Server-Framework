import csv
import datetime
import json
import os
import sys

project_root = os.path.abspath(__file__)
# Resolve a data directory relative to the project root ("Server-Framework").
# Fall back to the directory containing this module if the marker is absent.
_marker = "Server-Framework"
index = project_root.find(_marker)
if index != -1:
    Data_dir = project_root[:index + len(_marker) + 1] + "Data" + os.sep
else:
    Data_dir = os.path.join(os.path.dirname(project_root), "Data") + os.sep

# Ensure the data directory exists so report writes never fail on a missing dir.
os.makedirs(Data_dir, exist_ok=True)
sys.path.append(Data_dir)






class Report_Generator:
    def __init__(self):
        self.default_name_csv  = 'ReportCSV'
        self.default_name_txt  = 'ReportText'
        self.default_name_json = 'ReportJSON'


    def _get_unique_filename(self, filename):
        """Generates a unique filename by appending numbers if the file already exists in the data directory."""
        base, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        while os.path.exists(os.path.join(Data_dir, new_filename)):
            new_filename = f"{base}({counter}){ext}"
            counter += 1
        return new_filename

    
    
    def _get_user_filename(self, default_name, extension):
        """Prompts user for a filename, using a default if none is provided."""
        filename = input(f"[>] Enter desired filename for the report (or press Enter for default: {default_name}): ")
        if not filename:
            filename = default_name
        if not filename.endswith(extension):
            filename += extension
        return filename


    def _add_metadata(self, file):
        """Adds metadata information to the report."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file.write(f"#Report generated on: {timestamp}\n")
        file.write("\n#=============================\n\n")


    def CSV_GenerateReport(self, Data, filename=None):
        """Generates a CSV report from the provided data."""
        try:
            if filename is None:
                filename = self._get_user_filename(self.default_name_csv, '.csv')
            filename = self._get_unique_filename(filename)
            all_fieldnames = set()
            for fdata in Data:
                all_fieldnames.update(fdata.keys())
            all_fieldnames = sorted(all_fieldnames)
            
            with open(Data_dir+filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)
                writer.writeheader()
                if not Data:
                    print("[!] No discovered data to write.")
                    return
                
                print("[>] Writing data to CSV file...")
                for fdata in Data:
                    writer.writerow(fdata)
                print("[>] Data writing completed.")
                
            print(f"[+] Report generated successfully in CSV format: {filename}")
            print(f"[+] Total records written: {len(Data)}")
            print(f"[+] Path of {filename}: {Data_dir+filename}")
            
        except Exception as e:
            print(f"[!] Error generating CSV report: {e}")
            print(f"[!] Detailed Error: {e.__class__.__name__} - {e}")


    def TXT_GenerateReport(self, Data, filename=None):
        """Generates a TXT report from the provided data."""
        try:
            if filename is None:
                filename = self._get_user_filename(self.default_name_txt, '.txt')
            filename = self._get_unique_filename(filename)
            with open(Data_dir+filename, 'w') as txtfile:
                self._add_metadata(txtfile)
                if not Data:
                    print("[!] No discovered data to write.")
                    return
                
                print("[>] Writing data to TXT file...")
                for index, fdata in enumerate(Data, start=1):
                    txtfile.write(f"Record {index}\n")
                    for key, value in fdata.items():
                        txtfile.write(f"{key}: {value}\n")
                    txtfile.write("\n-----------------------------\n")
                print("[>] Data writing completed.")
                
            print(f"[+] Report generated successfully in TXT format: {filename}")
            print(f"[+] Total records written: {len(Data)}")
            print(f"[+] Path of {filename}: {Data_dir+filename}")
            
        except Exception as e:
            print(f"[!] Error generating TXT report: {e}")
            print(f"[!] Detailed Error: {e.__class__.__name__} - {e}")


    def JSON_GenerateReport(self, Data, filename=None):
        """Generates a JSON report from the provided data."""
        try:
            if filename is None:
                filename = self._get_user_filename(self.default_name_json, '.json')
            filename = self._get_unique_filename(filename)
            with open(Data_dir+filename, 'w') as jsonfile:
                self._add_metadata(jsonfile)
                if not Data:
                    print("[!] No scan data to write.")
                    return
                print("[>] Writing data to JSON file...")
                
                json.dump(Data, jsonfile, indent=4)
                
            print("[>] Data writing completed.")            
            print(f"[+] Report generated successfully in TXT format: {filename}")
            print(f"[+] Total records written: {len(Data)}")    
            print(f"[+] Path of {filename}: {Data_dir+filename}")

        except Exception as e:
            print(f"[!] Error generating JSON report: {e}")
            print(f"[!] Detailed Error: {e.__class__.__name__} - {e}")  
            
            

if __name__ == "__main__":
    #Example usage
    generator = Report_Generator()
    generator.CSV_GenerateReport([{"Name": "John", "Age": 30}, {"Name": "Jane", "Age": 25}])
    generator.TXT_GenerateReport([{"Name": "John", "Age": 30}, {"Name": "Jane", "Age": 25}])
    generator.JSON_GenerateReport([{"Name": "John", "Age": 30}, {"Name": "Jane", "Age": 25}])
    