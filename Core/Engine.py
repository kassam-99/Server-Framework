# Libraries to handle I/O files, folders and Manage a system  Server-Framework
import os
import shlex
import subprocess
import uuid
import psutil
from multiprocessing import Process, Queue
import time
from datetime import datetime, timedelta


# Other:
from Log import Logs
from Settings import Server_Settings, Path_Settings
from DirectoryManager import ProcessManager
from SysMonitor import RealTime_Process

     
     
     
     

class EngineServer():
    
    
    def __init__(self):
        self.engine_logs = Logs()
        self.engine_logs.LogEngine("Engine - EngineServer", "LogCore_Engine")
        self.Engine_ServerSettings = Server_Settings()
        self.Engine_PathSettings = Path_Settings()
        self.Engine_ProcessManager = ProcessManager()
        self.Engine_Realtime_Process = RealTime_Process()
        
        self.Script_Operation = dict()
        self.Script_Params = dict()
        
        self.system_type = self.Engine_ServerSettings.check_system()
        
        self.project_name_terminal = "\u001b[34mServer-Framework\u001b[0m - \u001b[33mServer\u001b[0m"
        
     
        """
        self.Script_Operation[script_nickname_process] = {
            'terminal': terminal,
            'pid': process_id,
            'Unique ID': process_unique,
            'Script Path' : script_path_proc,

        }
        """

     
     
     
     

class ProcessEngine(EngineServer):
    
    
    def __init__(self):
        super().__init__()


    def find_process_id_by_name(self, script_name):
        tracked_pids = {info['pid'] for info in self.Script_Operation.values()}
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if (script_name in proc.info['name'] or 
                (proc.info['cmdline'] and script_name in ' '.join(proc.info['cmdline']))):
                if proc.info['pid'] not in tracked_pids:
                    return proc.info['pid']
        return None


    def get_process_id_by_name(self, script_name):
        try:
            if self.system_type == "Linux":
                process_id = self.find_process_id_by_name(script_name)
                if process_id is not None:
                    return process_id
                else:
                    self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] No process found", "CRITICAL")
                    

        except Exception as e:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Error: {str(e)}", "ERROR")
            
        
    def Process_Organiser(self, script_name_process, terminal, script_nickname_process=None):
        process_id_org = self.get_process_id_by_name(script_name_process)
        script_path_proc = self.Engine_PathSettings.checkpath(script_name_process)
        
        if process_id_org == None:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Couldn't launch a script", "CRITICAL")
            
        else:
            process_unique = str(uuid.uuid4())
            if 'Unique ID' in self.Script_Operation:
                existing_unique_id = self.Script_Operation['Unique ID']
                while existing_unique_id == process_unique:
                    process_unique = str(uuid.uuid4())
            
            if script_nickname_process is not None:           
                self.engine_logs.print_and_log(f"{script_nickname_process} - Unique ID {process_unique}")
                self.Script_Operation[script_nickname_process] = {
                    "Script Name" : os.path.basename(script_path_proc),
                    "Mode" : os.path.basename(os.path.dirname(script_path_proc)),
                    'terminal': terminal,
                    'pid': process_id_org,
                    'Unique ID': process_unique,
                    'Script Path' : script_path_proc,
                    } 
                
                self.Engine_ProcessManager.write_to_process_engine_file(
                    script_name_dir=script_nickname_process, 
                    used_terminal_dir=terminal, 
                    process_id_dir=process_id_org, 
                    process_unique_dir=process_unique,
                    script_path=script_path_proc
                    )         
            
            elif script_name_process in self.Script_Operation:
                i = 2
                while f"{script_name_process} ({i})" in self.Script_Operation:
                    i += 1
                SameScript = f"{script_name_process} ({i})"
                self.engine_logs.print_and_log(f"{SameScript} - Unique ID {process_unique}")
                self.Script_Operation[SameScript] = {
                    "Script Name" : os.path.basename(script_path_proc),
                    "Mode" : os.path.basename(os.path.dirname(script_path_proc)),
                    'terminal': terminal,
                    'pid': process_id_org,
                    'Unique ID': process_unique,
                    'Script Path' : script_path_proc,
                    } 
                
                self.Engine_ProcessManager.write_to_process_engine_file(
                    script_name_dir=SameScript, 
                    used_terminal_dir=terminal, 
                    process_id_dir=process_id_org, 
                    process_unique_dir=process_unique,
                    script_path=script_path_proc
                )
                
            else:
                self.engine_logs.print_and_log(f"{script_name_process} - Unique ID {process_unique}")
                self.Script_Operation[script_name_process] = {
                    "Script Name" : os.path.basename(script_path_proc),
                    "Mode" : os.path.basename(os.path.dirname(script_path_proc)),
                    'terminal': terminal,
                    'pid': process_id_org,
                    'Unique ID': process_unique,
                    'Script Path' : script_path_proc,
                    }
                
                self.Engine_ProcessManager.write_to_process_engine_file(
                    script_name_dir=script_name_process, 
                    used_terminal_dir=terminal, 
                    process_id_dir=process_id_org, 
                    process_unique_dir=process_unique,
                    script_path=script_path_proc
                    )
     
     
     
     
     
     
     
     
     
     

class ScriptEngine(ProcessEngine):


    def __init__(self):
        super().__init__()
        
        

    def start_running(self, start_script_name, start_user_choice_terminal, start_script_nickname=None, params=None):
        """
        Start running a script with the specified terminal and optional nickname/parameters.
        
        Args:
            start_script_name (str): Path or name of the script to run.
            start_user_choice_terminal (int or str): Terminal index or name.
            start_script_nickname (str, optional): Nickname for the script.
            params (list or str, optional): Parameters to pass to the script.
        """
        script_path = self.Engine_PathSettings.checkpath(start_script_name)
        if not script_path or not os.path.exists(script_path):
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Script '{start_script_name}' not found at {script_path or 'None'}", "CRITICAL")
            return

        script_extension = os.path.splitext(start_script_name)[1].lower()
        extension_to_command = {
            '.py': 'python3',  # Use Python 3 explicitly
            '.sh': 'bash',
            '.js': 'node',
            '.rb': 'ruby',
            '.php': 'php',
            '.bat': 'cmd',
            '.cpp': 'g++',
            '.java': 'java',
            '.pl': 'perl',
            '.ps1': 'powershell',
            '.psm1': 'powershell',
            '.vbs': 'cscript'
        }
        interpreter = extension_to_command.get(script_extension)
        if not interpreter:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Unsupported script type: {start_script_name}", "CRITICAL")
            return

        # Shell-escape the path and any params so spaces / quotes / metacharacters
        # cannot break the command or inject extra shell commands.
        command = f"{interpreter} {shlex.quote(script_path)}"
        if params:
            if isinstance(params, list):
                param_tokens = [str(p) for p in params]
            else:
                # A single string may hold several space-separated arguments.
                param_tokens = shlex.split(str(params))
            command += " " + " ".join(shlex.quote(p) for p in param_tokens)
            self.Script_Params[start_script_name] = {'Params': params}

        if isinstance(start_user_choice_terminal, int):
            available_terminals = self.Engine_ServerSettings.get_available_terminals(self.system_type)
            if not available_terminals or start_user_choice_terminal < 1 or start_user_choice_terminal > len(available_terminals):
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Invalid terminal index: {start_user_choice_terminal}", "ERROR")
                return
            chosen_terminal = available_terminals[start_user_choice_terminal - 1]
        else:
            chosen_terminal = start_user_choice_terminal

        try:
            self.execute_script_multiprocess(command, chosen_terminal, start_script_name, start_script_nickname)
            self.engine_logs.LogsMessages(f"{start_script_name} launched" + (f" as {start_script_nickname}" if start_script_nickname else ""), "INFO")
        except Exception as e:
            self.engine_logs.LogsMessages(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Error starting script: {e}", "ERROR")


    def _resolve_launched_pid(self, script_path, fallback_pid):
        """Best-effort resolution of the real interpreter/script PID.

        The script is launched inside a terminal emulator, so subprocess.Popen
        only owns the emulator process. Poll psutil briefly for the process whose
        cmdline actually references the script path (excluding the keep-open
        wrapper shell), and fall back to the emulator PID if none is found.
        """
        if not script_path:
            return fallback_pid
        deadline = time.time() + 3
        while time.time() < deadline:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline') or []
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                if proc.pid == fallback_pid:
                    continue
                joined = ' '.join(cmdline)
                # The interpreter process runs "<interpreter> <script_path>";
                # the wrapper shell contains "exec bash", so skip it.
                if script_path in joined and 'exec bash' not in joined:
                    return proc.pid
            time.sleep(0.2)
        return fallback_pid


    def execute_script(self, command, choice_terminal, script_name, queue):
        if self.system_type != "Linux":
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Unsupported OS: {self.system_type}", "CRITICAL")
            queue.put((None, None))
            return
        
        available_terminals = self.Engine_ServerSettings.get_available_terminals(self.system_type)
        if choice_terminal not in available_terminals:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Unsupported or unavailable terminal: {choice_terminal}. Available: {available_terminals}", "ERROR")
            queue.put((None, None))
            return
        
        # Keep the launched shell open after the script finishes. `command` is
        # already shlex-quoted, so we pass the inner script as a separate argv
        # element (bash -c <inner>) instead of interpolating it into another
        # single-quoted string -- that avoids the nested-quote command injection.
        inner_command = f"{command}; exec bash"

        if choice_terminal == "konsole":
            cmd = [choice_terminal, "--noclose", "-e", "bash", "-c", inner_command]
        elif choice_terminal in ["xfce4-terminal", "lxterminal", "xterm"]:
            cmd = [choice_terminal, "-e", "bash", "-c", inner_command]
        elif choice_terminal == "terminator":
            cmd = [choice_terminal, "-x", "bash", "-c", inner_command]
        elif choice_terminal == "screen":
            cmd = [choice_terminal, "-dmS", "script_session", "bash", "-c", inner_command]
        else:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Unsupported terminal: {choice_terminal}", "ERROR")
            queue.put((None, None))
            return

        try:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[34m+\u001b[0m] Launching: {' '.join(cmd)}", "DEBUG")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # process.pid is the terminal emulator's PID (often short-lived for
            # terminator/screen). Resolve the actual interpreter/script PID so the
            # tracking / status features report the real process.
            script_path = self.Engine_PathSettings.checkpath(script_name)
            pid = self._resolve_launched_pid(script_path, fallback_pid=process.pid)
            creation_time = psutil.Process(pid).create_time()
            queue.put((pid, creation_time))
            
        except FileNotFoundError:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Terminal '{choice_terminal}' not found on system", "ERROR")
            queue.put((None, None))
        except Exception as e:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Error launching script with '{choice_terminal}': {e}", "ERROR")
            queue.put((None, None))


    def execute_script_multiprocess(self, command, terminal, script_name, script_nickname=None):
        script_path_proc = self.Engine_PathSettings.checkpath(script_name)
        queue = Queue()
        p = Process(target=self.execute_script, args=(command, terminal, script_name, queue))
        p.start()
        pid, creation_time = queue.get()  # Retrieve PID and creation time
        p.join()
        if pid:
            unique_id = str(uuid.uuid4())
            key = script_nickname if script_nickname else script_name
            if key in self.Script_Operation:
                i = 2
                while f"{key} ({i})" in self.Script_Operation:
                    i += 1
                key = f"{key} ({i})"
            # Updated dictionary with additional data
            self.Script_Operation[key] = {
                "Script Name" : os.path.basename(script_path_proc),
                "Mode" : os.path.basename(os.path.dirname(script_path_proc)),
                'terminal': terminal,
                'pid': pid,
                'Unique ID': unique_id,
                "Script Path": script_path_proc,
                'creation_time': creation_time,  
            }
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[34m+\u001b[0m] {key} - Unique ID {unique_id}", "INFO")
            
            self.Engine_ProcessManager.write_to_process_engine_file(
                script_name_dir=key, 
                used_terminal_dir=terminal, 
                process_id_dir=pid, 
                process_unique_dir=unique_id,
                script_path=script_path_proc
                )
            self.Engine_Realtime_Process.send_notification("Information - Execute", f"Script '{key}' launched with PID {pid} in {terminal}")
        else:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Failed to launch script '{script_name}' in {terminal}", "ERROR")
        
        
    def show_running(self):
        if not self.Script_Operation:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] No scripts are currently tracked", "INFO")
            return
        for script_name, operation_info in self.Script_Operation.items():
            orgine_script_name = operation_info['Script Name']
            mode_name = operation_info['Mode']
            terminal = operation_info['terminal']
            script_pid = operation_info['pid']
            script_id = operation_info['Unique ID']
            script_path = operation_info['Script Path']
            creation_time = operation_info.get('creation_time')  # Get creation time from dictionary
            
            try:
                # Convert creation_time to human-readable date and time
                creation_datetime = datetime.fromtimestamp(creation_time)
                creation_str = creation_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
                if psutil.pid_exists(script_pid):
                    status = "Running"
                    process = psutil.Process(script_pid)
                    current_time = datetime.now().timestamp()
                    running_time_seconds = current_time - creation_time  # Calculate running time in seconds
                    # Format running time as HH:MM:SS
                    total_seconds = int(running_time_seconds)  # Truncate microseconds
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    running_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    cpu_usage = process.cpu_percent()
                    memory_usage = process.memory_info().rss / (1024 ** 2)  # Convert to MB
                else:
                    status = "Not Running"
                    running_str = "N/A"
                    cpu_usage = "N/A"
                    memory_usage = "N/A"
    
                # Log all required data
                self.engine_logs.print_and_log("\n")
                self.engine_logs.print_and_log(f"[\u001b[33m$\u001b[0m] Script Name: {script_name}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Running Script: {orgine_script_name}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Running Mode: {mode_name}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Path: {script_path}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Terminal: {terminal}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Status: {status}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] PID: {script_pid}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Creation Time: {creation_str}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Running Time: {running_str}")
                self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Unique ID: {script_id}")
                if status == "Running":
                    self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] CPU Usage: {cpu_usage}%")
                    self.engine_logs.print_and_log(f"[\u001b[36m-\u001b[0m] Memory Usage: {memory_usage:.2f} MB")
                    
            except Exception as e:
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Error checking status for {script_name}: {e}", "ERROR")
        

    def rename_running(self, script_name=None, new_name=None):
        # Non-interactive path (e.g. driven over the admin socket): rename a
        # known script directly without reading from the server's stdin.
        if script_name is not None and new_name is not None:
            if script_name not in self.Script_Operation:
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [[31m![0m] {script_name} not found in running scripts.", "WARNING")
                return
            if new_name in self.Script_Operation:
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [[31m![0m] {new_name} already exists. Choose a different name.", "WARNING")
                return
            script_info = self.Script_Operation[script_name]
            terminal_old = script_info.get('terminal')
            real_name = script_info.get('Script Name')
            self.stop_running(script_name=script_name, stop_all=True)
            time.sleep(1)
            self.start_running(start_script_name=real_name, start_user_choice_terminal=terminal_old, start_script_nickname=new_name)
            self.engine_logs.print_and_log(f"[[34m+[0m] {script_name} -> {new_name} changed successfully!")
            self.Engine_Realtime_Process.send_notification("Information - Rename", f"{script_name} -> {new_name} changed successfully")
            return

        # List all running scripts and prompt user selection
        script_list = list(self.Script_Operation.items())
        if not script_list:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] No scripts are currently tracked", "INFO")
            return
        
        self.engine_logs.print_and_log("[\u001b[35m*\u001b[0m] Running scripts:")
        for i, (script_name, operation_info) in enumerate(script_list, start=1):
            self.engine_logs.print_and_log(f"[\u001b[36m{i}\u001b[0m] {script_name} (PID: {operation_info['pid']})")
        
        # Get user choice for script to rename
        try:
            choice = int(input(f"{self.project_name_terminal} [\u001b[35m>\u001b[0m] Enter the number of the script to rename: "))
            if 1 <= choice <= len(script_list):
                selected_script_name, script_info = script_list[choice - 1]
                terminal_old = script_info.get('terminal')
                real_name = script_info.get('Script Name')
                            
                # Get new name from user
                script_name_new = input(f"{self.project_name_terminal} [\u001b[35m>\u001b[0m] Enter the new name for the script: ").strip()
                
                # Check if new name already exists
                if script_name_new in self.Script_Operation:
                    self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] {script_name_new} already exists. Choose a different name.")
                    return
                    
                # Perform the rename operation
                self.stop_running(script_name=selected_script_name, stop_all=True)
                time.sleep(1)
                self.start_running(start_script_name=real_name, start_user_choice_terminal=terminal_old, start_script_nickname=script_name_new)
                
                self.engine_logs.print_and_log(f"[\u001b[34m+\u001b[0m] {selected_script_name} -> {script_name_new} changed successfully!")
                message_rename = f"{selected_script_name} -> {script_name_new} changed successfully"
                self.Engine_Realtime_Process.send_notification("Information - Rename", message_rename)
                
            else:
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Invalid selection. Please choose a number between 1 and {len(script_list)}", "WARNING")
                
        except ValueError:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Invalid input. Please enter a number.", "WARNING")
    
        
    def restart_script(self, script_name=None):
        # Non-interactive path (e.g. driven over the admin socket): restart a
        # known script directly without reading from the server's stdin.
        if script_name is not None:
            if script_name not in self.Script_Operation:
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [[31m![0m] {script_name} not found in running scripts.", "WARNING")
                return
            script_info = self.Script_Operation[script_name]
            terminal = script_info['terminal']
            real_name = script_info.get('Script Name')
            self.stop_running(script_name=script_name, stop_all=True)
            time.sleep(1)
            self.start_running(start_script_name=real_name, start_user_choice_terminal=terminal, start_script_nickname=script_name)
            self.engine_logs.print_and_log(f"[[34m+[0m] Script '{script_name}' restarted successfully.")
            self.Engine_Realtime_Process.send_notification("Information - Restart", f"Script '{script_name}' restarted successfully.")
            return

        # List all running scripts and prompt user selection
        script_list = list(self.Script_Operation.items())
        if not script_list:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] No scripts are currently tracked", "INFO")
            return
        
        self.engine_logs.print_and_log("[\u001b[35m*\u001b[0m] Running scripts:")
        for i, (script_name, operation_info) in enumerate(script_list, start=1):
            self.engine_logs.print_and_log(f"[\u001b[36m{i}\u001b[0m] {script_name} (PID: {operation_info['pid']})")
        
        try:
            choice = int(input(f"{self.project_name_terminal} [\u001b[35m>\u001b[0m] Enter the number of the script to restart: "))
            if 1 <= choice <= len(script_list):
                selected_script_name, script_info = script_list[choice - 1]
                terminal = script_info['terminal']
                real_name = script_info.get('Script Name')
                
                self.stop_running(script_name=selected_script_name, stop_all=True)
                time.sleep(1)
                self.start_running(start_script_name=real_name, start_user_choice_terminal=terminal, start_script_nickname=selected_script_name)
                
                self.engine_logs.print_and_log(f"[\u001b[34m+\u001b[0m] Script '{selected_script_name}' restarted successfully.")
                message_restart = f"Script '{selected_script_name}' restarted successfully."
                self.Engine_Realtime_Process.send_notification("Information - Restart", message_restart)
            else:
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Invalid selection. Please choose a number between 1 and {len(script_list)}", "WARNING")
        except ValueError:
            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Invalid input. Please enter a number.", "WARNING")
    
    
    def stop_running(self, script_name=None, stop_all=False):
        if stop_all:
            if script_name in self.Script_Operation:
                process_info = self.Script_Operation[script_name]
                process_script_pid = process_info['pid']
                
                if psutil.pid_exists(process_script_pid):
                    try:
                        process = psutil.Process(process_script_pid)
                        process.terminate()
                        process.wait(timeout=5)  # Graceful termination with a timeout
                        
                        if psutil.pid_exists(process_script_pid):
                            process.kill()  # Force kill if still running
                            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Force killed process with PID {process_script_pid}.", "ERROR")
                        else:
                            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[34m+\u001b[0m] Process with PID {process_script_pid} terminated successfully.", "WARNING")
                        
                        self.Script_Operation.pop(script_name)
                        self.Engine_ProcessManager.delete_from_process_engine_file(
                            script_name_dir=script_name, 
                            process_id_dir=process_script_pid, 
                            process_unique_dir=process_info['Unique ID']
                        )
                        message_stop = f"{script_name} - Terminated successfully"
                        self.Engine_Realtime_Process.send_notification("Information - Stop", message_stop)
                    except psutil.NoSuchProcess:
                        self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Process with PID {process_script_pid} does not exist.", "WARNING")
                    except psutil.AccessDenied:
                        self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Access denied. Unable to terminate process with PID {process_script_pid}.", "WARNING")
                    except psutil.TimeoutExpired:
                        self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Timeout expired while terminating process with PID {process_script_pid}.", "ERROR")
                    except Exception as e:
                        self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Error terminating process with PID {process_script_pid}: {e}", "ERROR")
                else:
                    self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Script '{script_name}' is not running and has been removed from tracking.", "WARNING")
                    self.Script_Operation.pop(script_name)
                    self.Engine_ProcessManager.delete_from_process_engine_file(
                        script_name_dir=script_name, 
                        process_id_dir=process_script_pid, 
                        process_unique_dir=process_info['Unique ID']
                    )
            else:
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] {script_name} not found in running scripts.", "WARNING")
        
        else:
            # List all running scripts and prompt user selection
            script_list = list(self.Script_Operation.items())
            if not script_list:
                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] No scripts are currently tracked", "INFO")
            else:
                self.engine_logs.print_and_log("[\u001b[35m*\u001b[0m] Running scripts:")
                for i, (script_name, operation_info) in enumerate(script_list, start=1):
                    self.engine_logs.print_and_log(f"[\u001b[36m{i}\u001b[0m] {script_name} (PID: {operation_info['pid']})")
                
                try:
                    choice = int(input(f"{self.project_name_terminal} [\u001b[35m>\u001b[0m] Enter the number of the script to stop: "))
                    if 1 <= choice <= len(script_list):
                        selected_script_name, process_info = script_list[choice - 1]
                        process_script_pid = process_info['pid']
                        
                        if psutil.pid_exists(process_script_pid):
                            try:
                                process = psutil.Process(process_script_pid)
                                process.terminate()
                                process.wait(timeout=5)  # Graceful termination with a timeout
                                
                                if psutil.pid_exists(process_script_pid):
                                    process.kill()  # Force kill if still running
                                    self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Force killed process with PID {process_script_pid}.", "ERROR")
                                else:
                                    self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[34m+\u001b[0m] Process with PID {process_script_pid} terminated successfully.", "WARNING")
                                
                                self.Script_Operation.pop(selected_script_name)
                                self.Engine_ProcessManager.delete_from_process_engine_file(
                                    script_name_dir=selected_script_name, 
                                    process_id_dir=process_script_pid, 
                                    process_unique_dir=process_info['Unique ID']
                                )
                                message_stop = f"{selected_script_name} - Terminated successfully"
                                self.Engine_Realtime_Process.send_notification("Information - Stop", message_stop)
                                
                            except psutil.NoSuchProcess:
                                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Process with PID {process_script_pid} does not exist.", "WARNING")
                            except psutil.AccessDenied:
                                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Access denied. Unable to terminate process with PID {process_script_pid}.", "WARNING")
                            except psutil.TimeoutExpired:
                                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Timeout expired while terminating process with PID {process_script_pid}.", "ERROR")
                            except Exception as e:
                                self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Error terminating process with PID {process_script_pid}: {e}", "ERROR")
                        else:
                            self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Script '{selected_script_name}' is not running and has been removed from tracking.", "WARNING")
                            self.Script_Operation.pop(selected_script_name)
                            self.Engine_ProcessManager.delete_from_process_engine_file(
                                script_name_dir=selected_script_name, 
                                process_id_dir=process_script_pid, 
                                process_unique_dir=process_info['Unique ID']
                            )
                    else:
                        self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Invalid selection: {choice}. Please choose a number between 1 and {len(script_list)}.", "WARNING")
                except ValueError:
                    self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] Invalid input: Please enter a number.", "WARNING")
                    
                          
    def stop_all_running(self):
        for script_name in list(self.Script_Operation.keys()):
            self.stop_running(script_name, stop_all=True)

        self.engine_logs.print_and_log(f"{self.project_name_terminal} [\u001b[31m!\u001b[0m] All running scripts stopped.", "CRITICAL")
        message_stop_all = "All running scripts stopped."
        self.Engine_Realtime_Process.send_notification("Information - Stop/All ", message_stop_all)
     
     
     
     
    


if __name__ == "__main__":
    pass