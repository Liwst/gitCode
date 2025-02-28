import configparser
from pathlib import Path


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

    @property
    def api_key(self) -> str:
        return self.config["API"]["key"]

    @property
    def api_base_url(self) -> str:
        return self.config["API"]["base_url"]

    @property
    def db_path(self) -> Path:
        return Path(self.config["Database"]["path"])

    @property
    def log_file(self) -> Path:
        return Path(self.config["Logging"]["file"])
