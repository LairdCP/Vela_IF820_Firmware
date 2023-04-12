import logging
import sys

class AppLogging():
    
    @property
    def CRITICAL(self): 
        return logging.CRITICAL
    @property
    def ERROR(self): 
        return logging.ERROR
    @property
    def WARNING(self): 
        return logging.WARNING
    @property
    def INFO(self): 
        return logging.INFO
    @property
    def DEBUG(self): 
        return logging.DEBUG
    @property
    def NOTSET(self):
        return logging.NOTSET

    def configure_app_logging (self, 
                   root_level: int = logging.DEBUG,
                   stdout_level: int = logging.NOTSET,
                   file_level: int = logging.NOTSET,
                   log_file_name: str = "log.log"):
        
        self.logger = logging.getLogger()
        self.logger.setLevel(root_level)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        if (stdout_level):
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(stdout_level)
            stdout_handler.setFormatter(formatter)
            self.logger.addHandler(stdout_handler)
        if (file_level):
            file_handler = logging.FileHandler(log_file_name)
            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            file_handler.flush()
            self.logger.addHandler(file_handler)

    def app_log_critical (self, msg: str):
        self.logger.critical(msg)    

    def app_log_error (self, msg: str):
        self.logger.error(msg) 

    def app_log_warning (self, msg: str):
        self.logger.warning(msg)            

    def app_log_info (self, msg: str):
        self.logger.info(msg)    

    def app_log_debug (self, msg: str):
        self.logger.debug(msg)

    def log_test(self):
        #in order of severity
        #this function is handy to have around to check logging levels are set properly
        #after calling "configure_debug" function
        self.logger.debug("Log Debug")
        self.logger.info("Log Info")
        self.logger.warning("Log Warning")
        self.logger.error("Log Error")
        self.logger.critical("Log Critical")

    def disable_logging (self):
         #set root logger to not set to disable all logging
         self.logger.setLevel(logging.NOTSET)    