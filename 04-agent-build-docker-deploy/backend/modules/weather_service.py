"""
天气服务模块

这个模块负责获取和处理天气数据，包括：
- 当前天气信息获取
- 多日天气预报
- 天气数据的格式化和验证
- 模拟天气数据（当API不可用时）

适用于大模型技术初级用户：
本模块示范了如何对接国内可访问的和风天气 (QWeather) 服务，
同时保留健壮的错误处理与回退机制。
"""

import requests
from typing import List, Optional
from datetime import datetime, timedelta

from ..config.api_config import api_config
from ..data.models import Weather

class WeatherService:
    """
    天气数据获取服务类

    这个类负责从和风天气 (QWeather) 获取天气信息，包括：
    1. 当前天气状况查询
    2. 多日天气预报获取
    3. 天气数据的处理和格式化
    4. API错误处理和模拟数据回退

    适用于大模型技术初级用户：
    展示了如何封装国内可访问的天气服务，并对外提供统一接口。
    """

    def __init__(self) -> None:
        """
        初始化天气服务

        设置 API 密钥、基础 URL、城市查询 URL 和 HTTP 会话，
        为后续的天气数据请求做准备。
        """
        self.api_key = api_config.QWEATHER_API_KEY
        self.base_url = (api_config.QWEATHER_API_BASE).rstrip("/")
        self.session = requests.Session()

        # QWeather 建议使用请求头携带密钥，兼容参数方式
        self._auth_headers = {"X-QW-Api-Key": self.api_key} if self.api_key else {}

    def get_current_weather(self, city: str) -> Optional[Weather]:
        """
        获取指定城市的当前天气

        参数：
        - city: 城市名称或经纬度（如 "北京" 或 "116.41,39.92"）

        返回：Weather 对象，若失败返回模拟数据
        """
        if not self.api_key:
            print("未配置 QWEATHER_API_KEY，使用模拟天气数据。")
            return self._get_mock_weather()

        location = self._resolve_location(city)
        if not location:
            print(f"无法解析城市位置: {city}，使用模拟天气数据。")
            return self._get_mock_weather()

        try:
            url = f"{self.base_url}/v7/weather/now"
            params = {"location": location, "lang": "zh"}
            response = self.session.get(url, params=params, headers=self._auth_headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("code") != "200":
                print(f"和风天气返回错误代码: {data.get('code')}, 消息: {data.get('fxLink')}")
                return self._get_mock_weather()

            now = data.get("now", {})
            temperature = float(now.get("temp", 22.0))
            humidity = int(float(now.get("humidity", 60)))
            wind_speed = float(now.get("windSpeed", 5.0))
            feels_like = float(now.get("feelsLike", temperature))
            description = now.get("text", "多云")

            return Weather(
                temperature=temperature,
                description=description,
                humidity=humidity,
                wind_speed=wind_speed,
                feels_like=feels_like,
                date=datetime.now().strftime("%Y-%m-%d")
            )
        except Exception as exc:
            print(f"获取当前天气时出错: {exc}")
            return self._get_mock_weather()

    def get_weather_forecast(self, city: str, days: int = 5) -> List[Weather]:
        """
        获取多日天气预报

        参数：
        - city: 城市名称或经纬度
        - days: 预报天数（默认 5 天，QWeather 支持 3/7/10/15/30 天）

        返回：Weather 对象列表
        """
        if not self.api_key:
            print("未配置 QWEATHER_API_KEY，返回模拟预报数据。")
            return self._get_mock_forecast(days)

        location = self._resolve_location(city)
        if not location:
            print(f"无法解析城市位置: {city}，返回模拟预报数据。")
            return self._get_mock_forecast(days)

        # 和风天气支持的固定天数
        supported_days = [3, 7, 10, 15, 30]
        request_days = next((d for d in supported_days if d >= max(1, days)), supported_days[0])

        try:
            url = f"{self.base_url}/v7/weather/{request_days}d"
            params = {"location": location, "lang": "zh"}
            response = self.session.get(url, params=params, headers=self._auth_headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("code") != "200":
                print(f"和风天气预报返回错误代码: {data.get('code')}")
                return self._get_mock_forecast(days)

            daily_items = data.get("daily", []) or []
            forecasts: List[Weather] = []

            for item in daily_items[:days]:
                temp_max = float(item.get("tempMax", 26.0))
                temp_min = float(item.get("tempMin", temp_max - 5))
                avg_temp = round((temp_max + temp_min) / 2, 1)
                humidity = int(float(item.get("humidity", 60)))
                wind_speed = float(item.get("windSpeedDay", item.get("windSpeedNight", 5.0)))
                feels_like = round((temp_max * 2 + temp_min) / 3, 1)
                description = item.get("textDay") or item.get("textNight") or "多云"

                forecasts.append(
                    Weather(
                        temperature=avg_temp,
                        description=description,
                        humidity=humidity,
                        wind_speed=wind_speed,
                        feels_like=feels_like,
                        date=item.get("fxDate", datetime.now().strftime("%Y-%m-%d"))
                    )
                )

            if not forecasts:
                return self._get_mock_forecast(days)

            return forecasts

        except Exception as exc:
            print(f"获取天气预报时出错: {exc}")
            return self._get_mock_forecast(days)

    def _resolve_location(self, city: str) -> Optional[str]:
        """
        将城市名称解析为和风天气的 location ID 或经纬度字符串。
        """
        if not city:
            return None

        stripped = city.strip()
        if "," in stripped:
            # 已经是经纬度
            return stripped

        if not self.api_key:
            return None

        try:
            # API文档地址：https://dev.qweather.com/docs/api/geoapi/city-lookup/
            url = f"{self.base_url}/geo/v2/city/lookup"
            params = {"location": stripped, "lang": "zh"}
            response = self.session.get(url, params=params, headers=self._auth_headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "200":
                print(f"和风天气城市查询失败: {data.get('code')} {data.get('fxLink')}")
                return None

            locations = data.get("location") or []
            if not locations:
                return None

            return locations[0].get("id")
        except Exception as exc:
            print(f"解析和风天气城市 ID 时出错: {exc}")
            return None

    def _get_mock_weather(self) -> Weather:
        """
        当 API 失败时返回模拟天气数据
        """
        return Weather(
            temperature=22.0,
            description="多云",
            humidity=65,
            wind_speed=5.2,
            feels_like=24.0,
            date=datetime.now().strftime("%Y-%m-%d")
        )

    def _get_mock_forecast(self, days: int) -> List[Weather]:
        """
        当 API 失败时返回模拟预报数据
        """
        forecasts: List[Weather] = []
        base_date = datetime.now()
        weather_conditions = ["晴朗", "多云", "阴天", "小雨"]

        for i in range(max(1, days)):
            date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            temp = 20 + (i % 8)
            description = weather_conditions[i % len(weather_conditions)]

            forecasts.append(
                Weather(
                    temperature=float(temp),
                    description=description,
                    humidity=60 + (i % 5) * 5,
                    wind_speed=4.5 + (i % 3),
                    feels_like=float(temp) + 1.5,
                    date=date_str
                )
            )

        return forecasts
