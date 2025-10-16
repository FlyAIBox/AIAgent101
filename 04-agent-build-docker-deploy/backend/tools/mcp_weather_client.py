"""
MCP 天气客户端助手模块

该模块提供了连接本地 MCP 天气服务器的异步客户端功能，
支持调用天气服务器提供的工具（如天气预报查询）。

主要功能：
1. 建立与 MCP 天气服务器的 stdio 连接
2. 加载并调用服务器提供的天气查询工具
3. 提供便捷的异步上下文管理器接口
4. 自动处理连接的建立和清理

作者：FlyAIBox
日期：2025.10.16
"""

import os
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

# 配置日志记录，输出到 logs/backend.log 文件
def setup_logger():
    """
    设置日志记录器，将日志输出到 logs/backend.log 文件
    
    返回:
        logger: 配置好的日志记录器实例
    """
    logger = logging.getLogger('mcp_weather_client')
    logger.setLevel(logging.INFO)
    
    # 避重复添加handler
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
logger = setup_logger()


class MCPWeatherClient:
    """
    MCP 天气客户端类
    
    该类提供与 MCP 天气服务器的连接和交互功能，支持异步上下文管理器模式，
    可以自动处理连接的建立和清理工作。
    
    属性:
        server_path (str): MCP 天气服务器脚本的路径
        _exit_stack (AsyncExitStack): 异步资源管理器
        _session (ClientSession): MCP 客户端会话对象
    """
    
    def __init__(self, server_path: Optional[str] = None) -> None:
        """
        初始化 MCP 天气客户端
        
        参数:
            server_path (Optional[str]): MCP 服务器脚本路径，默认为当前目录下的 weather_server.py
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.server_path = server_path or os.path.join(base_dir, "weather_server.py")
        self._exit_stack: Optional[AsyncExitStack] = None
        self._session: Optional[ClientSession] = None
        
        logger.info(f"初始化 MCP 天气客户端，服务器路径: {self.server_path}")

    async def __aenter__(self) -> "MCPWeatherClient":
        """
        异步上下文管理器入口
        
        自动建立与 MCP 服务器的连接
        
        返回:
            MCPWeatherClient: 已连接的客户端实例
        """
        logger.info("进入 MCP 天气客户端上下文")
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """
        异步上下文管理器出口
        
        自动清理连接资源
        
        参数:
            exc_type: 异常类型
            exc: 异常实例
            tb: 异常追踪信息
        """
        logger.info("退出 MCP 天气客户端上下文")
        await self.close()

    async def connect(self) -> None:
        """
        建立与 MCP 天气服务器的连接
        
        该方法会启动一个子进程运行天气服务器，并通过 stdio 协议进行通信。
        
        异常:
            FileNotFoundError: 当服务器脚本文件不存在时抛出
        """
        logger.info(f"开始连接 MCP 天气服务器: {self.server_path}")
        
        if not os.path.exists(self.server_path):
            error_msg = f"MCP 天气服务器未找到: {self.server_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        self._exit_stack = AsyncExitStack()

        # 配置服务器启动参数
        server_params = StdioServerParameters(
            command="python",  # 使用 Python 解释器启动服务器
            args=[self.server_path],  # 传递服务器脚本路径作为参数
            env=None,  # 使用当前环境变量
        )
        
        logger.info(f"启动 MCP 服务器进程: python {self.server_path}")

        try:
            # 建立 stdio 通信通道
            stdio, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
            
            # 创建 MCP 客户端会话
            self._session = await self._exit_stack.enter_async_context(ClientSession(stdio, write))
            
            # 初始化会话
            await self._session.initialize()
            
            logger.info("MCP 天气服务器连接成功")
            
        except Exception as e:
            logger.error(f"连接 MCP 天气服务器失败: {str(e)}")
            raise

    async def close(self) -> None:
        """
        关闭与 MCP 服务器的连接并清理资源
        
        该方法会优雅地关闭所有打开的连接和子进程。
        """
        if self._exit_stack is not None:
            logger.info("关闭 MCP 天气服务器连接")
            try:
                await self._exit_stack.aclose()
                logger.info("MCP 连接资源清理完成")
            except Exception as e:
                logger.error(f"清理 MCP 连接资源时出错: {str(e)}")
            finally:
                self._exit_stack = None
                self._session = None

    async def _load_tools(self) -> List[Any]:
        """
        从 MCP 服务器加载可用工具列表
        
        返回:
            List[Any]: 可用工具列表
            
        异常:
            RuntimeError: 当 MCP 会话未初始化时抛出
        """
        if not self._session:
            error_msg = "MCP 会话未初始化"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("开始加载 MCP 服务器工具")
        try:
            tools = await load_mcp_tools(self._session)
            tool_names = [tool.name for tool in tools]
            logger.info(f"成功加载 {len(tools)} 个工具: {tool_names}")
            return tools
        except Exception as e:
            logger.error(f"加载 MCP 工具失败: {str(e)}")
            raise

    async def get_daily_forecast(self, location: str, days: int = 3) -> str:
        """
        获取指定位置的天气预报
        
        该方法会调用 MCP 服务器的 get_daily_forecast 工具来获取天气预报信息。
        
        参数:
            location (str): 位置信息，可以是城市名、城市ID或经纬度坐标
            days (int): 预报天数，默认为3天，支持3、7、10、15、30天
            
        返回:
            str: 格式化的天气预报信息
            
        异常:
            RuntimeError: 当找不到 get_daily_forecast 工具时抛出
        """
        logger.info(f"调用天气预报工具 - 位置: {location}, 天数: {days}")
        
        try:
            # 加载服务器工具
            tools = await self._load_tools()
            
            # 查找天气预报工具
            tool = next((t for t in tools if t.name == "get_daily_forecast"), None)
            if tool is None:
                error_msg = "MCP 服务器中未找到 get_daily_forecast 工具"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            # 准备工具调用参数
            tool_params = {"location": str(location), "days": int(days)}
            logger.info(f"工具调用参数: {tool_params}")
            
            # 调用 MCP 工具获取天气预报
            result = await tool.ainvoke(tool_params)
            result_str = str(result)
            
            logger.info(f"天气预报工具调用成功，返回数据长度: {len(result_str)} 字符")
            logger.info(f"天气预报结果: {result_str[:200]}..." if len(result_str) > 200 else f"天气预报结果: {result_str}")
            
            return result_str
            
        except Exception as e:
            logger.error(f"获取天气预报失败: {str(e)}")
            raise


async def fetch_forecast_via_mcp(location: str, days: int = 3) -> str:
    """
    便捷函数：通过 MCP 获取天气预报
    
    这是一个简化的接口函数，自动处理 MCP 客户端的创建、连接和清理工作。
    适用于只需要获取一次天气预报的场景。
    
    参数:
        location (str): 位置信息，可以是城市名、城市ID或经纬度坐标
        days (int): 预报天数，默认为3天，支持3、7、10、15、30天
        
    返回:
        str: 格式化的天气预报信息
        
    示例:
        >>> forecast = await fetch_forecast_via_mcp("北京", 7)
        >>> print(forecast)
    """
    logger.info(f"便捷函数调用 - 获取天气预报: 位置={location}, 天数={days}")
    
    try:
        async with MCPWeatherClient() as client:
            result = await client.get_daily_forecast(location=location, days=days)
            logger.info(f"便捷函数调用成功")
            return result
    except Exception as e:
        logger.error(f"便捷函数调用失败: {str(e)}")
        raise


