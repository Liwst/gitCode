import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import ConfigLoader


def setup_logger():
    """配置日志系统"""
    config = ConfigLoader()

    logger = logging.getLogger("weather_tool")
    logger.setLevel(logging.DEBUG)

    # 文件日志（带轮转）
    log_file = config.log_file
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=int(config.config["Logging"]["max_size"]),
        backupCount=int(config.config["Logging"]["backup_count"])
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = setup_logger()
