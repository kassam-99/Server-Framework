# Libraries to handle I/O files, folders and Manage a system
import multiprocessing
import os
import sys
from io import StringIO


# Get the project root directory (two levels up from the script)
Project_Folder = "Server-Framework"
project_root = os.path.abspath(__file__)
index = project_root.find(Project_Folder)
index_length_project = len(Project_Folder)
if index != -1:
    core_dir = project_root[:index+index_length_project+1]+"Core"
sys.path.append(core_dir)



from Engine import ScriptEngine
from Modes import ModeManager
from Log import Logs
from Settings import Server_Settings, Path_Settings
from Engine import ScriptEngine
from Emergency import EmergencyPathManager
from SysMonitor import RealTime_Dir, Sensor
from Commands import *




class Dashboard_Panel:
    def __init__(self):
        EmergencyPathManager().StartEmergencyModePath()
        self.log_dashboard = Logs()
        self.log_dashboard.LogEngine("Dashboard_Panel", "LogCore_Dashboard")
        self.mode_dashboard = ModeManager()
        self.run_dashboard = ScriptEngine()
        self.settings_dashboard = Server_Settings()
        self.path_dashboard = Path_Settings()
        self.RealTime_Dir_dashboard = RealTime_Dir()
        self.Sensor_dashboard = Sensor()
        self.system_found = self.settings_dashboard.check_system()
        
        self.main_commands = {
            "list": lambda: self.mode_dashboard.list_modes(True),
            "rename": self.run_dashboard.rename_running,
            "stop": self.run_dashboard.stop_running,
            "stop_all": self.run_dashboard.stop_all_running,
            "restart": self.run_dashboard.restart_script,
            "map": lambda: self.mode_dashboard.list_modes(True),
            "info": self.Sensor_dashboard.Start_Sensor,
            "show": self.run_dashboard.show_running,
            "help": lambda: print(cmd_command),
            "read": banner,
            "admin_start": lambda: self.launch_admin_panel("start"),
            "admin_stop": lambda: self.launch_admin_panel("stop"),
            "web_start": lambda: self.launch_web_panel("start"),
            "web_stop": lambda: self.launch_web_panel("stop"),
        }


    def capture_output(self, func, *args, **kwargs):
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            func(*args, **kwargs)
            output = sys.stdout.getvalue()
            return output
        except Exception as e:
            self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\033[31m!\033[0m] Invalid capture_output: {e}", "ERROR") 
        finally:
            sys.stdout = original_stdout


    def main(self, func, *args, **kwargs):
        try:
            with StringIO() as buf:
                sys.stdout = buf
                func(*args, **kwargs)
                output = buf.getvalue()
        finally:
            sys.stdout = sys.__stdout__

        files = self.mode_dashboard.extract_folders_and_files(output)
        for i, file in enumerate(files, start=1):
            self.log_dashboard.print_and_log(f"[\u001b[36m{i}\u001b[0m] {file}")

        try:
            selected_file_index = int(input(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Enter the file option to run: "))
            selected_file = files[selected_file_index - 1]
            self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Script selected {selected_file}")
            self.settings_dashboard.get_available_terminals(self.system_found, True)
            terminal_mode = int(input(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Enter the terminal option to use: "))
            add_params = input(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Do you want to add parameters? (y/n): ").lower()
            if add_params == "y":
                params = input(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Enter parameters (separated by space): ").split()
                
                self.run_dashboard.start_running(start_script_name=selected_file, start_user_choice_terminal=terminal_mode, params=params)
            else:
                self.run_dashboard.start_running(start_script_name=selected_file, start_user_choice_terminal=terminal_mode)
                
        except (ValueError, IndexError):
            self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\033[31m!\033[0m] Invalid input.") 

    
    def launch_admin_panel(self, action=None):
        script_name = "AdminPanel.py"
        
        if action == "start":
            
            try:
                self.settings_dashboard.get_available_terminals(self.system_found, True)
                terminal_mode = int(input(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Enter the terminal option to use: "))
                print(terminal_mode)
                self.run_dashboard.start_running(start_script_name=script_name, start_user_choice_terminal=terminal_mode)
                
            except (ValueError, IndexError):
                self.log_dashboard.print_and_log(f"{project_name_terminal} [\u001b[31m!\u001b[0m] Invalid selection.", "ERROR")
                return
        
        elif action == "stop":
            self.run_dashboard.stop_running(script_name=script_name, stop_all=True)


    def launch_web_panel(self, action=None):
        script_name = "Web_Backend.py"
        
        if action == "start":
            
            try:
                self.settings_dashboard.get_available_terminals(self.system_found, True)
                terminal_mode = int(input(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Enter the terminal option to use: "))
                print(terminal_mode)
                self.run_dashboard.start_running(start_script_name=script_name, start_user_choice_terminal=terminal_mode)
                
            except (ValueError, IndexError):
                self.log_dashboard.print_and_log(f"{project_name_terminal} [\u001b[31m!\u001b[0m] Invalid selection.", "ERROR")
                return
        
        elif action == "stop":
            self.run_dashboard.stop_running(script_name=script_name, stop_all=True)
            
            
            
    def Main_Dashboard(self):
        process1 = multiprocessing.Process(target=self.RealTime_Dir_dashboard.Start_Monitor)
        process1.start()
    
        for logo in ListLogo:
            print(logo)
            break
    
        try:
            while True:
                user_input = input(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Enter option: ").lower()
    
                if user_input == "exit":
                    self.run_dashboard.stop_all_running()
    
                    if process1.is_alive():
                        process1.terminate()
                        process1.join()
                        self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\u001b[31m!\u001b[0m] Directory monitoring terminated", "INFO")
    
                    self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\u001b[31m!\u001b[0m] Dashboard exiting", "INFO")
                    sys.exit(0)
    
                elif user_input in self.main_commands:
                    self.main_commands[user_input]()
                    if user_input == "map":
                        user_input_map = input(f"\n{project_name_terminal} [\u001b[35m>\u001b[0m] Enter option - mapping: ")
                        if user_input_map.isdigit() and 1 <= int(user_input_map) <= len(self.mode_dashboard.available_modes):
                            self.mode_dashboard.select_mode(self.mode_dashboard.available_modes[int(user_input_map) - 1])
                        else:
                            self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\033[31m!\033[0m] Invalid input: {user_input_map}. Type 'list' to see available modes.")
                elif user_input.isdigit() and 1 <= int(user_input) <= len(self.mode_dashboard.available_modes):
                    self.main(self.mode_dashboard.select_mode, self.mode_dashboard.available_modes[int(user_input) - 1])
                else:
                    self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\033[31m!\033[0m] Invalid input: {user_input}. Type 'list' to see available modes.")
    
        except EOFError:
            self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\033[31m!\u001b[0m] Dashboard terminated via EOF", "INFO")
            self.run_dashboard.stop_all_running()
            if process1.is_alive():
                process1.terminate()
                process1.join()
            sys.exit(0)
    
        except KeyboardInterrupt:
            self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\033[31m!\u001b[0m] Dashboard interrupted by user", "INFO")
            self.run_dashboard.stop_all_running()
            if process1.is_alive():
                process1.terminate()
                process1.join()
            sys.exit(0)
    
        except Exception as e:
            self.log_dashboard.print_and_log(f"\n{project_name_terminal} [\033[31m!\033[0m] Unexpected Error: {e}", "ERROR")
            self.run_dashboard.stop_all_running()
            if process1.is_alive():
                process1.terminate()
                process1.join()
            sys.exit(1)
    
            

if __name__ == "__main__":
    Dashboard_Panel().Main_Dashboard()