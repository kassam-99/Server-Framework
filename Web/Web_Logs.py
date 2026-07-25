import logging
import os
from datetime import datetime
import traceback

# DEBUG, INFO, WARNING, ERROR, CRITICAL
"""

DEBUG - Detailed information, typically of interest only when diagnosing problems.

INFO - Confirmation that things are working as expected.

WARNING - An indication that something unexpected happened, or indicative of some problem in the near future (e.g. disk space low). The software is still working as expected.

ERROR - Due to a more serious problem, the software has not been able to perform some function.

CRITICAL - A serious error, indicating that the program itself may be unable to continue running.     
    
"""


        

class Logs:
    def __init__(self, default_log_level=logging.DEBUG, verbose=False):
        self.default_log_level = default_log_level
        self.verbose = verbose
        self.logger = None
        self.server_log_path = __file__
        self.script_dir = os.path.dirname(self.server_log_path)
        self.mainloggerfile = os.path.join(self.script_dir, "Main_logger.log")
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    def log_to_file(self, message, TypeLog):
        with open(self.mainloggerfile, "a", encoding="utf-8") as error_log_file:
            error_log_file.write(f"{datetime.now()} - {TypeLog}: {message}\n")
        if self.verbose:
            print(f"{datetime.now()} - {TypeLog}: {message}")

    def checkpath(self, target_folder, target_file):
        try:
            folder_path = os.path.join(self.script_dir, target_folder)
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            if not target_file.endswith(".log"):
                target_file += ".log"
            file_path = os.path.join(folder_path, target_file)
            if not os.path.exists(file_path):
                open(file_path, 'w').close()
            return file_path
        except Exception as e:
            error_message = f"Error creating path: {e}\n{traceback.format_exc()}"
            self.log_to_file(error_message, "Error")
            return None

    def LogEngine(self, folder_name="logs", log_name="application"):
        if not log_name:
            log_name = "default"
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(self.default_log_level)
        logfile = self.checkpath(folder_name, log_name)
        if logfile:
            handler = logging.FileHandler(logfile)
            handler.setLevel(self.default_log_level)
            formatter = logging.Formatter(self.log_format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def LogsMessages(self, message, message_type="info", verbose=False):
        if self.logger:
            message_type = message_type.lower()
            if message_type == "debug":
                self.logger.debug(message)
            elif message_type == "info":
                self.logger.info(message)
            elif message_type == "warning":
                self.logger.warning(message)
            elif message_type == "error":
                self.logger.error(message)
            elif message_type == "critical":
                self.logger.critical(message)
            else:
                self.logger.warning(f"Unknown log level '{message_type}', using 'warning' instead.")
                self.logger.warning(message)
                
        if verbose == True:
            print(message)


if __name__ == "__main__":
    logger = Logs(verbose=True)
    logger.LogEngine("ExampleLogger", "Log")
    logger.LogsMessages("This is a debug message", message_type="debug")
    logger.LogsMessages("This is an info message", message_type="info")
    logger.LogsMessages("This is a warning message", message_type="warning")
    logger.LogsMessages("This is an error message", message_type="error")
    logger.LogsMessages("This is a critical message", message_type="critical")

