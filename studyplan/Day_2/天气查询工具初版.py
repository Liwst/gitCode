import requests
class WeatherAPI:
    def __init__(self, api_key):
        self.base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.api_key = api_key
        self.timeout = 5

    def get_weather(self, city_name:str) -> dict:
        """获取实时天气数据"""
        params = {
            "key": self.api_key,
            "city": city_name,
            "extension": "base",  # 基础实时天气
            "output": "JSON"
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            data = response.json()

            if data["status"] == "1" and data["infocode"] == "10000":
                return self._parse_data(data)
            else:
                return {"error": f'API错误: {data.get("info", "未知错误")}'}
        except requests.exceptions.RequestException as e:
            return {"error": f"网络错误: {str(e)}"}
        except Exception as e:
            return {"error": f"系统错误: {str(e)}"}

    def _parse_data(self, data: dict) -> dict:
        """解析原始数据"""
        live_data = data["lives"][0]
        return {
            "city": f'{live_data["province"]}{live_data["city"]}',
            "weather": live_data["weather"],
            "temperature": f'{live_data["temperature"]}℃',
            "humidity": f'{live_data["humidity"]}%',
            "wind": f'{live_data["winddirection"]}风{live_data["windpower"]}级',
            "report_time": live_data["reporttime"]
            }

# 使用示例（替换your_key）
if __name__ == "__main__":
    api = WeatherAPI(api_key="9bb5ee9e4dfdfc30aada73eea4ee492c")  # ← 替换为真实Key

    # 测试查询
    print(api.get_weather("北京"))
    # 输出成功示例：
    # {
    #     'city': '北京市北京市',
    #     'weather': '晴',
    #     'temperature': '28℃',
    #     'humidity': '45%',
    #     'wind': '南风风2级',
    #     'report_time': '2023-08-20 16:30:00'
    # }

    print(api.get_weather("纽约"))  # 错误示例
    # {'error': 'API错误: INVALID_USER_KEY'}