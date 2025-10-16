#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 服务器可以提供三种主要类型的功能：

资源：客户端可以读取的类似文件的数据（例如 API 响应或文件内容）
工具：可由 LLM 调用的函数（经用户批准）
提示：预先编写的模板，帮助用户完成特定任务

######################################

MCP 天气服务器

提供两个工具：
1. get_weather_warning: 获取指定城市ID或经纬度的天气灾害预警
2. get_daily_forecast: 获取指定城市ID或经纬度的天气预报

Author: FlyAIBox
Date: 2025.10.11
"""

from typing import Any, Dict, List, Optional, Union
import asyncio
import httpx
import os
import logging
from urllib.parse import urljoin
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 配置日志记录器
def setup_weather_server_logger():
    """设置天气服务器日志记录器"""
    logger = logging.getLogger('weather_server')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # 确保日志目录存在
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 创建文件处理器
        file_handler = logging.FileHandler('logs/backend.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger

# 创建全局日志记录器
weather_logger = setup_weather_server_logger()

# 加载 .env 文件中的环境变量
dotenv_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path)

# 初始化 FastMCP 服务器
mcp = FastMCP("weather",  # 服务器名称
              debug=True,  # 启用调试模式，会输出详细日志
              host="0.0.0.0") # 监听所有网络接口，允许远程连接

# 从环境变量中读取常量
QWEATHER_API_BASE = os.getenv("QWEATHER_API_BASE")
QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY")

def _normalize_base_url(raw_base: Optional[str]) -> str:
    """
    确保基础 URL 包含协议并以单个斜杠结尾，兼容 .env 中未写协议的情况
    """
    if not raw_base:
        raise RuntimeError("未配置 QWEATHER_API_BASE 环境变量")

    base = raw_base.strip()
    if not base.startswith(("http://", "https://")):
        base = f"https://{base.lstrip('/')}"

    # urljoin 要求目录风格以斜杠结尾，避免 'v7/weather/7d' 被覆盖
    if not base.endswith("/"):
        base = f"{base}/"

    return base

try:
    _QWEATHER_BASE_URL = _normalize_base_url(QWEATHER_API_BASE)
except RuntimeError as err:
    print(f"[配置错误] {err}")
    _QWEATHER_BASE_URL = None

async def make_qweather_request(endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    向和风天气 API 发送请求
    
    参数:
        endpoint: API 端点路径（不包含基础 URL）
        params: API 请求的参数
        
    返回:
        成功时返回 JSON 响应，失败时返回 None
    """
    weather_logger.info(f"发起和风天气 API 请求 - 端点: {endpoint}, 参数: {params}")
    
    if not _QWEATHER_BASE_URL:
        error_msg = "QWEATHER_API_BASE 未正确配置，已跳过请求。"
        weather_logger.error(error_msg)
        print(error_msg)
        return None

    if not QWEATHER_API_KEY:
        error_msg = "QWEATHER_API_KEY 未设置，已跳过请求。"
        weather_logger.error(error_msg)
        print(error_msg)
        return None

    safe_endpoint = endpoint.lstrip("/")
    url = urljoin(_QWEATHER_BASE_URL, safe_endpoint)
    weather_logger.info(f"构建请求 URL: {url}")

    # 使用 Header 方式认证（和风天气的新版本API）
    headers = {
        "X-QW-Api-Key": QWEATHER_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            weather_logger.info(f"请求 URL: {url}")
            weather_logger.info(f"请求参数: {params}")
            print(f"请求 URL: {url}")
            print(f"请求参数: {params}")
            
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            weather_logger.info(f"响应状态码: {response.status_code}")
            print(f"响应状态码: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            weather_logger.info(f"API 请求成功，响应数据长度: {len(str(result))} 字符")
            weather_logger.debug(f"响应内容: {result}")
            print(f"响应内容: {result}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP 状态错误: {e.response.status_code} - {e.response.text}"
            weather_logger.error(error_msg)
            print(error_msg)
            return None
            
        except Exception as e:
            error_msg = f"API 请求错误: {type(e).__name__}: {e}"
            weather_logger.error(error_msg)
            print(error_msg)
            return None

# ---------------------- 位置解析（城市名 -> 城市ID）----------------------
async def resolve_location_to_id(location: str) -> Optional[str]:
    """
    将用户输入的位置解析为和风天气城市ID或经纬度。

    规则：
    - 若为 "lon,lat" 或 "lat,lon" 形式（包含逗号），直接返回原始字符串（API支持经纬度）
    - 若为纯数字（可能是城市ID），直接返回
    - 否则调用城市查询接口 v2/city/lookup，取第一个匹配项的 id
    """
    if not location:
        return None

    text = location.strip()

    # 经纬度（包含逗号）
    if "," in text:
        weather_logger.info(f"位置解析: 检测到经纬度格式，直接使用 -> {text}")
        return text

    # 纯数字（城市ID）
    if text.isdigit():
        weather_logger.info(f"位置解析: 检测到数字ID，直接使用 -> {text}")
        return text

    # 调用城市查询接口
    params = {
        "location": text,
        "lang": "zh"
    }
    weather_logger.info(f"位置解析: 调用城市查询接口 v2/city/lookup，参数: {params}")

    try:
        data = await make_qweather_request("v2/city/lookup", params)
        if not data:
            weather_logger.error("位置解析失败：城市查询无返回数据")
            return None

        code = data.get("code") or str(data.get("status", ""))
        if code != "200":
            weather_logger.error(f"位置解析失败：API 返回错误码 {code}")
            return None

        locations = data.get("location") or data.get("locations") or []
        if not locations:
            weather_logger.error("位置解析失败：未找到匹配的城市")
            return None

        resolved_id = locations[0].get("id")
        name = locations[0].get("name")
        adm2 = locations[0].get("adm2")
        adm1 = locations[0].get("adm1")
        country = locations[0].get("country")
        weather_logger.info(f"位置解析成功: '{text}' -> id={resolved_id}, {country}/{adm1}/{adm2}/{name}")
        return resolved_id
    except Exception as e:
        weather_logger.error(f"位置解析异常: {str(e)}")
        return None

def format_warning(warning: Dict[str, Any]) -> str:
    """
    将天气预警数据格式化为可读字符串
    
    参数:
        warning: 天气预警数据对象
        
    返回:
        格式化后的预警信息
    """
    return f"""
预警ID: {warning.get('id', '未知')}
标题: {warning.get('title', '未知')}
发布时间: {warning.get('pubTime', '未知')}
开始时间: {warning.get('startTime', '未知')}
结束时间: {warning.get('endTime', '未知')}
预警类型: {warning.get('typeName', '未知')}
预警等级: {warning.get('severity', '未知')} ({warning.get('severityColor', '未知')})
发布单位: {warning.get('sender', '未知')}
状态: {warning.get('status', '未知')}
详细信息: {warning.get('text', '无详细信息')}
"""

@mcp.tool()
async def get_weather_warning(location: Union[str, int]) -> str:
    """
    获取指定位置的天气灾害预警
    
    参数:
        location: 城市ID或经纬度坐标（经度,纬度）
                例如：'101010100'（北京）或 '116.41,39.92'
                也可以直接传入数字ID，如 101010100
        
    返回:
        格式化的预警信息字符串
    """
    weather_logger.info(f"调用天气预警工具 - 位置: {location}")
    
    # 确保 location 为字符串类型并解析为ID/经纬度
    raw_location = str(location)
    weather_logger.info(f"转换位置参数为字符串: {raw_location}")
    resolved_location = await resolve_location_to_id(raw_location)
    if not resolved_location:
        return f"无法解析位置: {raw_location}"
    
    params = {
        "location": resolved_location,
        "lang": "zh"
    }
    
    weather_logger.info(f"天气预警请求参数: {params}")
    
    try:
        data = await make_qweather_request("v7/warning/now", params)
        
        if not data:
            error_msg = "无法获取预警信息或API请求失败。"
            weather_logger.error(error_msg)
            return error_msg
        
        if data.get("code") != "200":
            error_msg = f"API 返回错误: {data.get('code')}"
            weather_logger.error(error_msg)
            return error_msg
        
        warnings = data.get("warning", [])
        weather_logger.info(f"获取到 {len(warnings)} 个预警信息")
        
        if not warnings:
            result_msg = f"当前位置 {raw_location} 没有活动预警。"
            weather_logger.info(result_msg)
            return result_msg
        
        formatted_warnings = [format_warning(warning) for warning in warnings]
        result = "\n---\n".join(formatted_warnings)
        
        weather_logger.info(f"天气预警工具调用成功，返回 {len(formatted_warnings)} 个格式化预警")
        return result
        
    except Exception as e:
        error_msg = f"天气预警工具调用异常: {str(e)}"
        weather_logger.error(error_msg)
        return error_msg

def format_daily_forecast(daily: Dict[str, Any]) -> str:
    """
    将天气预报数据格式化为可读字符串
    
    参数:
        daily: 天气预报数据对象
        
    返回:
        格式化后的预报信息
    """
    return f"""
日期: {daily.get('fxDate', '未知')}
日出: {daily.get('sunrise', '未知')}  日落: {daily.get('sunset', '未知')}
最高温度: {daily.get('tempMax', '未知')}°C  最低温度: {daily.get('tempMin', '未知')}°C
白天天气: {daily.get('textDay', '未知')}  夜间天气: {daily.get('textNight', '未知')}
白天风向: {daily.get('windDirDay', '未知')} {daily.get('windScaleDay', '未知')}级 ({daily.get('windSpeedDay', '未知')}km/h)
夜间风向: {daily.get('windDirNight', '未知')} {daily.get('windScaleNight', '未知')}级 ({daily.get('windSpeedNight', '未知')}km/h)
相对湿度: {daily.get('humidity', '未知')}%
降水量: {daily.get('precip', '未知')}mm
紫外线指数: {daily.get('uvIndex', '未知')}
能见度: {daily.get('vis', '未知')}km
"""

@mcp.tool()
async def get_daily_forecast(location: Union[str, int], days: int = 3) -> str:
    """
    获取指定位置的天气预报
    
    参数:
        location: 城市ID或经纬度坐标（经度,纬度）
                例如：'101010100'（北京）或 '116.41,39.92'
                也可以直接传入数字ID，如 101010100
        days: 预报天数，可选值为 3、7、10、15、30，默认为 3
        
    返回:
        格式化的天气预报字符串
    """
    weather_logger.info(f"调用天气预报工具 - 位置: {location}, 天数: {days}")
    
    # 确保 location 为字符串类型并解析为ID/经纬度
    raw_location = str(location)
    weather_logger.info(f"转换位置参数为字符串: {raw_location}")
    resolved_location = await resolve_location_to_id(raw_location)
    if not resolved_location:
        return f"无法解析位置: {raw_location}"
    
    # 确保 days 参数有效
    valid_days = [3, 7, 10, 15, 30]
    original_days = days
    if days not in valid_days:
        days = 3  # 默认使用3天预报
        weather_logger.warning(f"无效的天数参数 {original_days}，使用默认值 {days}")
    
    params = {
        "location": resolved_location,
        "lang": "zh"
    }
    
    # 和风天气API文档 https://dev.qweather.com/docs/api/weather/weather-daily-forecast/
    endpoint = f"v7/weather/{days}d"
    weather_logger.info(f"天气预报请求端点: {endpoint}, 参数: {params}")
    
    try:
        data = await make_qweather_request(endpoint, params)
        
        if not data:
            error_msg = "无法获取天气预报或API请求失败。"
            weather_logger.error(error_msg)
            return error_msg
        
        if data.get("code") != "200":
            error_msg = f"API 返回错误: {data.get('code')}"
            weather_logger.error(error_msg)
            return error_msg
        
        daily_forecasts = data.get("daily", [])
        weather_logger.info(f"获取到 {len(daily_forecasts)} 天的天气预报数据")
        
        if not daily_forecasts:
            error_msg = f"无法获取 {raw_location} 的天气预报数据。"
            weather_logger.error(error_msg)
            return error_msg
        
        formatted_forecasts = [format_daily_forecast(daily) for daily in daily_forecasts]
        result = "\n---\n".join(formatted_forecasts)
        
        weather_logger.info(f"天气预报工具调用成功，返回 {len(formatted_forecasts)} 天的格式化预报")
        return result
        
    except Exception as e:
        error_msg = f"天气预报工具调用异常: {str(e)}"
        weather_logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    print("正在启动 MCP 天气服务器...")
    print("提供工具: get_weather_warning, get_daily_forecast")
    print("请确保环境变量 QWEATHER_API_KEY 已设置")
    print("使用 Ctrl+C 停止服务器")
    
    # 初始化并运行服务器
    mcp.run(transport='stdio') 
