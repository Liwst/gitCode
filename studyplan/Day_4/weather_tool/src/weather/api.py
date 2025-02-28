import requests
from datetime import datetime
from typing import Dict, Any
from .config import ConfigLoader


class WeatherAPI:
    """高德天气API封装"""

    def __init__(self):
        config = ConfigLoader()
        self.base_url = config.api_base_url
        self.api_key = config.api_key
        self.timeout = int(config.config["API"]["timeout"])

    def get_current(self, city: str) -> Dict[str, Any]:
        """获取实时天气"""
        params = {
            "key": self.api_key,
            "city": city,
            "extensions": "base",
            "output": "JSON"
        }
        return self._process_request(params, self._parse_current)

    def get_forecast(self, city: str) -> Dict[str, Any]:
        """获取7天预报"""
        params = {
            "key": self.api_key,
            "city": city,
            "extensions": "all",
            "output": "JSON"
        }
        return self._process_request(params, self._parse_forecast)

    def _process_request(self, params: Dict, parser: callable) -> Dict:
        """统一处理API请求"""
        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            data = response.json()
            if data["status"] == "1":
                return parser(data)
            return {"error": self._map_error(data.get("infocode"))}
        except requests.RequestException as e:
            return {"error": f"网络错误: {str(e)}"}

    def _parse_current(self, data: Dict) -> Dict:
        """解析实时天气数据"""
        live = data["lives"][0]
        return {
            "city": f"{live['province']}{live['city']}",
            "weather": live["weather"],
            "temp": f"{live['temperature']}℃",
            "humidity": f"{live['humidity']}%",
            "wind": f"{live['winddirection']}{live['windpower']}级",
            "update_time": self._format_time(live["reporttime"])
        }

    def _parse_forecast(self, data: Dict) -> Dict:
        """解析预报数据"""
        forecast = data["forecasts"][0]
        return {
            "city": f"{forecast['province']}{forecast['city']}",
            "casts": [
                {
                    "date": self._format_date(cast["date"]),
                    "day_weather": cast["dayweather"],
                    "night_weather": cast["nightweather"],
                    "day_temp": cast["daytemp"],
                    "night_temp": cast["nighttemp"],
                    "wind": f"{cast['daywind']}{cast['daypower']}级"
                } for cast in forecast["casts"]
            ]
        }

    def _format_time(self, time_str: str) -> str:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").strftime("%m/%d %H:%M")

    def _format_date(self, date_str: str) -> str:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%m/%d")

    def _map_error(self, code: str) -> str:
        errors = {
            "10001": "无效API密钥",
            "207300": "城市不存在",
            "208900": "请求内容不存在"
        }
        return errors.get(code, f"未知错误码: {code}")
