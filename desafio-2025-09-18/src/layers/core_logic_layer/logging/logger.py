import logging


class Logger:
    def __init__(self):
        self.__logger = None

    @property
    def logger(self) -> logging.Logger:
        if self.__logger is None:
            self.__logger = self.__create_logger()
        return self.__logger

    @staticmethod
    def __create_logger() -> logging.Logger:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        log_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(log_format)
        logger.addHandler(handler)
        return logger
