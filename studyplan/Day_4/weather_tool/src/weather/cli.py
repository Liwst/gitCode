import argparse
from typing import List, Dict
from .database import WeatherDatabase
from .api import WeatherAPI
from .logger import logger
from .config import ConfigLoader


class WeatherCLI:
    """命令行界面处理器"""

    def __init__(self):
        self.config = ConfigLoader()
        self.db = WeatherDatabase(self.config.db_path)
        self.api = WeatherAPI()

    def handle(self):
        """处理命令行参数"""
        args = self._parse_args()

        try:
            if args.history:
                self._show_history(args.history)
            elif args.city:
                self._process_query(args.city, args.forecast)
            else:
                logger.error("必须指定城市名称")
        finally:
            self.db.close()

    def _parse_args(self):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(description="天气查询工具")
        parser.add_argument("city", nargs="?", help="要查询的城市名称")
        parser.add_argument("-f", "--forecast",
                            action="store_true",
                            help="显示7天天气预报")
        parser.add_argument("-H", "--history",
                            type=int,
                            metavar="N",
                            help="显示最近N条查询历史")
        return parser.parse_args()

    def _process_query(self, city: str, is_forecast: bool):
        """处理天气查询"""
        logger.info(f"开始查询: {city} {'预报' if is_forecast else '实时'}")

        if is_forecast:
            result = self.api.get_forecast(city)
            self.db.save_query(city, "forecast")
        else:
            result = self.api.get_current(city)
            self.db.save_query(city, "current")

        if "error" in result:
            logger.error(result["error"])
        else:
            self._display_result(result)

    def _display_result(self, data: Dict):
        """显示查询结果"""
        if "casts" in data:
            self._display_forecast(data)
        else:
            self._display_current(data)

    def _display_current(self, data: Dict):
        """显示实时天气"""
        print(f"\n城市: {data['city']}")
        print(f"天气: {data['weather']}")
        print(f"温度: {data['temp']}")
        print(f"更新时间: {data['update_time']}")

    def _display_forecast(self, data: Dict):
        """显示预报"""
        print(f"\n{data['city']} 7天预报:")
        for cast in data["casts"]:
            print(f"{cast['date']} 白天{cast['day_weather']} "
                  f"夜间{cast['night_weather']} {cast['wind']}")

    def _show_history(self, limit: int):
        """显示历史记录"""
        records = self.db.get_history(limit)
        print(f"\n最近{limit}条查询记录:")
        for idx, rec in enumerate(records, 1):
            print(f"{idx}. {rec['time']} {rec['city']} ({rec['type']})")


def main():
    WeatherCLI().handle()


if __name__ == "__main__":
    main()
