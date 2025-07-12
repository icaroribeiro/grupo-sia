import logging


class Logger:
    def __init__(self):
        self.__logger = None

    @property
    def custom_logger(self) -> logging.Logger:
        if self.__logger is None:
            self.__logger = logging.getLogger(__name__)
            self.__logger.setLevel(logging.DEBUG)

            log_format = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(log_format)

            self.__logger.addHandler(handler)

        return self.__logger
