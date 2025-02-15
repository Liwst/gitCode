import argparse
import sqlite3
import requests
from datetime import datetime
from pathlib import Path


# ============= 数据库模块 =============
class WeatherDB:
    def __init__(self):
        self.db_path = Path("weather.db")
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()

    def _create_table(self):
        """创建历史记录表"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            query_type TEXT CHECK(query_type IN ('current', 'forecast')),
            query_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature TEXT,
            weather TEXT
            )''')
        self.conn.commit()

    def save_record(self, city: str, query_type: str, temp: str, weather: str):
        """保存查询记录"""
        self.conn.execute(
            "INSERT INTO history (city, query_type, temperature, weather) VALUES (?, ?, ?, ?)",
            (city, query_type, temp, weather)
        )
        self.conn.commit()

    def get_history(self, limit: int = 5) -> list:
        """获取查询历史"""
        cursor = self.conn.execute(
            "SELECT city, query_type, query_time, temperature, weather "
            "FROM history ORDER BY query_time DESC LIMIT ?", (limit,)
        )
        return [{
            "city": row[0],
            "type": "实时" if row[1] == "current" else "预报",
            "time": row[2],
            "temp": row[3],
            "weather": row[4]
        } for row in cursor]

    def close(self):
        self.conn.close()


# ========== API模块 ==========
class WeatherAPI:
    def __init__(self, api_key: str):
        self.base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.api_key = api_key
        self.timeout = 5

    def _request(self, city: str, extensions: str) -> dict:
        """发送API请求"""
        params = {
            "key": self.api_key,
            "city": city,
            "extensions": extensions,
            "output": "JSON"
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            data = response.json()
            if data["status"] == "1" and data["infocode"] == "10000":
                return data
            return {"error": self._map_error(data.get("infocode"))}
        except requests.exceptions.RequestException as e:
            return {"error": f"网络错误：{e}"}

    def get_current(self, city: str) -> dict:
        """获取实时天气"""
        data = self._request(city, "base")
        if "error" in data:
            return data
        return self._parse_current(data)

    def get_forecast(self, city: str) -> dict:
        """获取7天预报"""
        data = self._request(city, "all")
        if "error" in data:
            return data
        return self._parse_forecast(data)

    def _parse_current(self, data: dict) -> dict:
        """解析实时数据"""
        live = data["lives"][0]
        return {
            "city": f"{live['province']}{live['city']}",
            "weather": live["weather"],
            "temp": f"{live['temperature']}℃",
            "humidity": f"{live['humidity']}%",
            "wind": f"{live['winddirection']}{live['windpower']}级",
            "time": datetime.strptime(live["reporttime"], "%Y-%m-%d %H:%M:%S").strftime("%m/%d %H:%M")
        }

    def _parse_forecast(self, data: dict) -> dict:
        """解析预报数据"""
        forecast = data["forecasts"][0]
        return {
            "city": f"{forecast['province']}{forecast['city']}",
            "casts": [{
                "date": datetime.strptime(cast["date"], "%Y-%m-%d").strftime("%m/%d"),
                "day_weather": cast["dayweather"],
                "night_weather": cast["nightweather"],
                "day_temp": cast["daytemp"],
                "night_temp": cast["nighttemp"],
                "wind": f"{cast['daywind']}{cast['daypower']}级"
            } for cast in forecast["casts"]]
        }

    def _map_error(self, code: str) -> str:
        """错误码转换"""
        errors = {
            "10001": "无效的API密钥",
            "10003": "超过每日限额",
            "207300": "城市不存在",
            "invalid_params": "请求参数错误"
        }
        return errors.get(code, "未知错误")

# ==================== 显示模块 ====================
def print_error(msg: str):
    """显示错误信息"""
    print(f"\033[91m✖ {msg}\033[0m")

def print_current(weather: dict):
    """显示实时天气"""
    print(f"\n\033[95m✦ {weather['city']}实时天气 {'✦'*20}\033[0m")
    print(f"\033[94m⛅ 天气\t{weather['weather']}")
    print(f"🌡 温度\t{weather['temp']}")
    print(f"💧 湿度\t{weather['humidity']}")
    print(f"🌪 风力\t{weather['wind']}")
    print(f"🕒 更新\t{weather['time']}")
    print("\033[95m" + "="*50 + "\033[0m\n")

def print_forecast(forecast: dict):
    """显示7天预报"""
    print(f"\n\033[95m🌈 {forecast['city']}7天预报 {'🌈'*20}\033[0m")
    for cast in forecast["casts"]:
        print(f"\033[94m📅 {cast['date']} 白天{cast['day_weather']} 夜间{cast['night_weather']}")
        print(f"   🌞 {cast['day_temp']}℃ | 🌙 {cast['night_temp']}℃ | 🌪 {cast['wind']}")
    print("\033[95m" + "="*50 + "\033[0m\n")

def print_history(records: list):
    """显示历史记录"""
    print(f"\n\033[95m📜 最近{len(records)}条查询记录 {'📜'*15}\033[0m")
    for idx, rec in enumerate(records, 1):
        print(f"\033[94m{idx}. [{rec['time']}] {rec['city']} ({rec['type']})")
        print(f"   {rec['weather']} {rec['temp']}\033[0m")
    print("\033[95m" + "="*50 + "\033[0m\n")

# ==================== 主程序 ====================
def main():
    # 配置参数解析
    parser = argparse.ArgumentParser(description="高德天气查询工具")
    parser.add_argument("city", nargs="?", help="要查询的城市名称")
    parser.add_argument("-f", "--forecast", action="store_true", help="显示7天预报")
    parser.add_argument("-H", "--history", type=int, metavar="N", help="显示最近N条历史记录")
    args = parser.parse_args()

    # 初始化组件
    db = WeatherDB()
    api = WeatherAPI(api_key="9bb5ee9e4dfdfc30aada73eea4ee492c")  # ⚠️ 需要替换成真实密钥！

    try:
        # 处理历史查询
        if args.history:
            records = db.get_history(args.history)
            print_history(records)
            return

        # 校验城市参数
        if not args.city:
            print_error("必须指定要查询的城市名称")
            return

        # 执行查询
        if args.forecast:
            result = api.get_forecast(args.city)
            if "error" in result:
                print_error(result["error"])
            else:
                print_forecast(result)
                db.save_record(args.city, "forecast", "N/A", "7天预报")
        else:
            result = api.get_current(args.city)
            if "error" in result:
                print_error(result["error"])
            else:
                print_current(result)
                db.save_record(args.city, "current", result["temp"], result["weather"])

    finally:
        db.close()

if __name__ == "__main__":
    main()