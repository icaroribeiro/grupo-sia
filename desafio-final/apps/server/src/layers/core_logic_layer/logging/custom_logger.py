import logging


def setup_custom_logger():
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
