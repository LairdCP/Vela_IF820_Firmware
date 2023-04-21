import logging


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

    @property
    def LOGGER_NAME(self):
        return self.logger.name

    @property
    def LOG_FILE_FORMAT(self) -> str:
        return '%(asctime)s | %(name)s | %(levelname)s | %(message)s'

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.log_file_handler = logging.FileHandler(
            f'{self.LOGGER_NAME}.log', mode='a')

    def configure_app_logging(self,
                              level: int = logging.NOTSET,
                              file_level: int = logging.NOTSET):
        """Configure the log level of the module

        Args:
            level (int, optional): std out log level. NOTSET disables logging. Defaults to logging.NOTSET.
            file_level (int, optional): file log level. NOTSET disables logging. Defaults to logging.NOTSET.
        """
        self.logger.setLevel(level)
        if level == self.NOTSET:
            self.logger.disabled = True
        else:
            self.logger.disabled = False

        if file_level:
            self.log_file_handler.setLevel(file_level)
            self.log_file_handler.setFormatter(
                logging.Formatter(self.LOG_FILE_FORMAT))
            self.log_file_handler.flush()
            self.logger.removeHandler(self.log_file_handler)
            self.logger.addHandler(self.log_file_handler)

    def app_log_critical(self, msg: str):
        self.logger.critical(msg)

    def app_log_error(self, msg: str):
        self.logger.error(msg)

    def app_log_warning(self, msg: str):
        self.logger.warning(msg)

    def app_log_info(self, msg: str):
        self.logger.info(msg)

    def app_log_debug(self, msg: str):
        self.logger.debug(msg)

    def log_test(self):
        """_summary_ This function is handy to have around to check logging levels are set properly
        after calling "configure_debug" function
        """
        # In order of less severe to more
        self.logger.debug("Log Debug")
        self.logger.info("Log Info")
        self.logger.warning("Log Warning")
        self.logger.error("Log Error")
        self.logger.critical("Log Critical")

    def disable_logging(self):
        self.logger.disabled = True
