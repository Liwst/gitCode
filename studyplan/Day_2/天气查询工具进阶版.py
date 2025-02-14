import requests
from datetime import datetime


class WeatherAPI:
    def __init__(self, api_key):
        # 初始化API基础配置
        self.base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.api_key = api_key  # 高德地图Web服务Key
        self.timeout = 5  # 请求超时时间

    def get_weather(self, city_name: str) -> dict:
        """获取实时天气数据（核心方法）

        参数：
            city_name : 城市名称（支持中文/拼音）

        返回：
            包含天气数据的字典 或 错误信息字典
        """
        params = {
            "key": self.api_key,
            "city": city_name,
            "extensions": "base",  # 修正参数名（原代码写错成extension）
            "output": "JSON"
        }

        try:
            # 发送GET请求
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            # 解析JSON响应
            data = response.json()

            # 校验API响应状态
            if data["status"] == "1" and data["infocode"] == "10000":
                return self._parse_data(data)
            else:
                return {"error": self._map_error(data.get("infocode"))}

        except requests.exceptions.RequestException as e:
            return {"error": f"网络连接异常，请检查网络后重试（{str(e)}）"}
        except Exception as e:
            return {"error": f"系统处理异常（{str(e)}）"}

    def _parse_data(self, data: dict) -> dict:
        """解析原始JSON数据"""
        live_data = data["lives"][0]
        return {
            "城市": f'{live_data["province"]}{live_data["city"]}',
            "天气": live_data["weather"],
            "温度": f'{live_data["temperature"]}℃',
            "湿度": f'{live_data["humidity"]}%',
            "风力": f'{live_data["winddirection"]}{live_data["windpower"]}级',
            "更新时间": datetime.strptime(live_data["reporttime"], "%Y-%m-%d %H:%M:%S").strftime("%m/%d %H:%M")
        }

    def _map_error(self, code: str) -> str:
        """错误码映射"""
        error_map = {
            "10001": "API密钥无效",
            "10003": "超过每日请求限额",
            "207300": "城市名称不存在",
            "invalid_params": "请求参数错误"
        }
        return error_map.get(code, "未知服务错误")


def display_weather(weather_info: dict):
    """美化天气信息输出"""
    if "error" in weather_info:
        print(f"\033[91m✖ 错误：{weather_info['error']}\033[0m")
        return

    # ANSI颜色代码
    colors = {
        "title": "\033[95m",  # 品红
        "data": "\033[94m",  # 蓝色
        "reset": "\033[0m"
    }

    print(f"\n{colors['title']}✦ 实时天气简报 {'✦' * 30}{colors['reset']}")
    print(f"{colors['data']}📍 城市\t{weather_info['城市']}")
    print(f"⛅ 天气\t{weather_info['天气']}")
    print(f"🌡 温度\t{weather_info['温度']}")
    print(f"💧 湿度\t{weather_info['湿度']}")
    print(f"🌪 风力\t{weather_info['风力']}")
    print(f"🕒 更新\t{weather_info['更新时间']}")
    print(f"{colors['title']}{'=' * 45}{colors['reset']}\n")


# 使用示例
if __name__ == "__main__":
    # 需要先申请高德API密钥（免费）
    api = WeatherAPI(api_key="9bb5ee9e4dfdfc30aada73eea4ee492c")

    # 测试正常查询
    display_weather(api.get_weather("北京"))
    display_weather(api.get_weather("石家庄"))
    display_weather(api.get_weather("邢台"))
    display_weather(api.get_weather("巨鹿"))
    # 测试异常查询
    # display_weather(api.get_weather("哥谭市"))  # 不存在的城市
    # display_weather(api.get_weather(""))  # 空参数
