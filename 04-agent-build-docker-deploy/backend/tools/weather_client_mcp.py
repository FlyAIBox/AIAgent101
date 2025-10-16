"""
# 集成 DeepSeek 的 MCP 客户端
#参考官方案例：https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/clients/simple-chatbot/mcp_simple_chatbot/main.py


# 本模块实现了一个模型上下文协议（MCP）客户端，该客户端使用大语言模型的 API
# 来处理查询并与 MCP 工具进行交互。它演示了如何：
# 1. 连接到 MCP 服务器
# 2. 使用大语言模型的 API 来处理查询
# 3. 处理工具调用和响应
# 4. 维护一个交互式聊天循环


Author: FlyAIBox
Date: 2025.10.11
"""

import json
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List, Tuple
from contextlib import AsyncExitStack
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 配置详细日志记录器
def setup_weather_client_logger():
    """设置天气客户端日志记录器"""
    logger = logging.getLogger('weather_client')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # 确保日志目录存在
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 创建文件处理器
        file_handler = logging.FileHandler('logs/backend.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 设置详细日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger

# 创建全局日志记录器
logger = setup_weather_client_logger()

load_dotenv()


def _resolve_mcp_server_path() -> str:
    """解析 MCP 天气服务器脚本路径，尝试多个候选位置并返回首个存在的路径。"""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(backend_dir, "server", "weather_server_mcp.py"),
        os.path.join(backend_dir, "server", "weather_server.py"),
        os.path.join(backend_dir, "tools", "weather_server_mcp.py"),
        os.path.join(backend_dir, "tools", "weather_server.py"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(
        "找不到MCP天气服务器文件，已检查: " + ", ".join(candidates)
    )


def _resolve_city_location(location: str) -> str:
    """
    解析位置参数，将中文城市名转换为城市ID
    
    Args:
        location: 位置信息，可以是中文城市名、城市ID或经纬度
        
    Returns:
        str: 标准化的位置参数（城市ID或经纬度）
    """
    logger.info(f"开始解析城市位置参数: {location}")
    
    # 如果已经是数字ID或经纬度格式，直接返回
    if location.isdigit() or ',' in location:
        logger.info(f"位置参数已是标准格式（城市ID或经纬度）: {location}")
        return location
        
    # 尝试使用LLM转换城市名为城市ID
    try:
        logger.info(f"尝试使用LLM转换城市名: {location}")
        city_id = _convert_city_name_to_id_with_llm(location)
        if city_id:
            logger.info(f"LLM城市名转换成功: {location} → {city_id}")
            return city_id
    except Exception as e:
        logger.warning(f"LLM转换失败: {str(e)}，回退到备用映射")
    
    # 备用：常用城市硬编码映射
    city_mapping = {
        "北京": "101010100", "上海": "101020100", "广州": "101280101",
        "深圳": "101280601", "杭州": "101210101", "南京": "101190101",
        "成都": "101270101", "武汉": "101200101", "重庆": "101040100",
        "天津": "101030100", "西安": "101110101", "苏州": "101190401",
        "郑州": "101180101", "长沙": "101250101", "青岛": "101120201",
        "大连": "101070201", "宁波": "101210401", "厦门": "101230201",
        "福州": "101230101", "沈阳": "101070101"
    }
    
    if location in city_mapping:
        resolved = city_mapping[location]
        logger.info(f"使用备用映射转换成功: {location} → {resolved}")
        return resolved
    
    # 如果都无法转换，返回原值
    logger.warning(f"无法转换城市名: {location}，使用原值进行天气查询")
    return location


def _convert_city_name_to_id_with_llm(city_name: str) -> Optional[str]:
    """
    使用大模型将城市名转换为和风天气城市ID
    
    Args:
        city_name: 中文城市名
        
    Returns:
        str: 和风天气城市ID，如果转换失败返回None
    """
    try:
        # 检查是否有可用的OpenAI配置
        config = Configuration()
        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        
        # 设计转换提示词
        system_prompt = """你是一个专业的城市信息助手，专门负责将中文城市名转换为和风天气API的城市ID。

和风天气城市ID规则：
- 北京: 101010100
- 上海: 101020100  
- 广州: 101280101
- 深圳: 101280601
- 杭州: 101210101
- 南京: 101190101
- 成都: 101270101
- 武汉: 101200101
- 重庆: 101040100
- 天津: 101030100
- 西安: 101110101

请根据上述规律和你的知识，为用户提供的城市名返回对应的和风天气城市ID。

要求：
1. 只返回数字格式的城市ID，不要返回其他内容
2. 如果不确定，返回 "UNKNOWN"
3. 城市ID通常是9位数字，格式类似 101XXXXXX"""

        user_prompt = f"请提供 {city_name} 的和风天气城市ID："
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=20,
            temperature=0.1  # 降低随机性，提高准确性
        )
        
        result = response.choices[0].message.content.strip()
        
        # 验证返回结果格式
        if result == "UNKNOWN":
            return None
        elif result.isdigit() and len(result) == 9:
            return result
        else:
            logger.warning(f"LLM返回格式异常: {result}")
            return None
            
    except Exception as e:
        logger.error(f"LLM城市ID转换失败: {str(e)}")
        return None


class Configuration:
    """配置管理类，负责管理和验证环境变量"""
    
    def __init__(self) -> None:
        """初始化配置并加载环境变量"""
        self.load_env()
        self._validate_env()
        
    @staticmethod
    def load_env() -> None:
        """从.env文件加载环境变量"""
        load_dotenv()
        
    def _validate_env(self) -> None:
        """验证必需的环境变量是否存在"""
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"缺少必需的环境变量: {', '.join(missing_vars)}")
    
    @property
    def api_key(self) -> str:
        """获取 DeepSeek API 密钥"""
        return os.getenv("OPENAI_API_KEY", "")
    
    @property
    def base_url(self) -> str:
        """获取 DeepSeek API 基础 URL"""
        return os.getenv("OPENAI_BASE_URL")
    
    @property
    def model(self) -> str:
        """获取 DeepSeek 模型名称"""
        return os.getenv("OPENAI_MODEL", "gpt-4o")

class Tool:
    """MCP 工具类，表示一个具有属性的工具"""
    
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]) -> None:
        """
        初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入参数模式
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema
        
    def to_openai_format(self) -> Dict[str, Any]:
        """将工具转换为 OpenAI API 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema
            }
        }

class MCPServer:
    """MCP 服务器管理类，处理服务器连接和工具执行"""
    
    def __init__(self, server_path: str) -> None:
        """
        初始化服务器管理器
        
        Args:
            server_path: 服务器脚本路径
        """
        self.server_path = server_path
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self._cleanup_lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """初始化服务器连接，包含重试机制"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                if not os.path.exists(self.server_path):
                    raise FileNotFoundError(f"找不到服务器文件: {self.server_path}")
                
                server_params = StdioServerParameters(
                    command='python',
                    args=[self.server_path],
                    env=None
                )
                
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                stdio, write = stdio_transport
                
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(stdio, write)
                )
                await self.session.initialize()
                logger.info("成功连接到 MCP 服务器")
                break
                
            except Exception as e:
                logger.error(f"第 {attempt + 1}/{max_retries} 次尝试失败: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise
                    
    async def list_tools(self) -> List[Tool]:
        """获取服务器提供的可用工具列表"""
        if not self.session:
            raise RuntimeError("服务器未初始化")
            
        response = await self.session.list_tools()
        return [
            Tool(tool.name, tool.description, tool.inputSchema)
            for tool in response.tools
        ]
        
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        retries: int = 2,
        delay: float = 1.0
    ) -> Any:
        """
        执行工具，包含重试机制
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            retries: 重试次数
            delay: 重试延迟时间（秒）
            
        Returns:
            工具执行结果
        """
        if not self.session:
            raise RuntimeError("服务器未初始化")
            
        for attempt in range(retries):
            try:
                logger.info(f"执行工具 {tool_name}，参数: {arguments}")
                result = await self.session.call_tool(tool_name, arguments)
                return result
                
            except Exception as e:
                logger.error(f"工具执行失败 (第 {attempt + 1}/{retries} 次尝试): {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise
                    
    async def cleanup(self) -> None:
        """清理服务器资源"""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                logger.info("服务器资源清理完成")
            except Exception as e:
                logger.error(f"清理过程中出错: {str(e)}")

class MCPClient:
    """MCP 客户端实现，集成了 DeepSeek API"""
    
    def __init__(self, config: Configuration) -> None:
        """
        初始化 MCP 客户端
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.server: Optional[MCPServer] = None
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        
    async def initialize(self) -> None:
        """初始化客户端并连接到服务器"""
        server_path = _resolve_mcp_server_path()
        self.server = MCPServer(server_path)
        await self.server.initialize()
        

    async def process_query(self, query: str) -> str:
        """
        处理用户查询，集成工具调用，支持多轮工具交互

        Args:
            query: 用户查询字符串

        Returns:
            处理后的响应结果
        """
        if not self.server:
            raise RuntimeError("客户端未初始化")

        system_prompt = (
            "You are a helpful assistant specializing in weather information.\n"
            "You have access to the MCP Weather Server tool with the following functions:\n"
            "- get_weather_warning(city_id=None, latitude=None, longitude=None): Retrieves weather disaster warnings for a specified city ID or coordinates.\n"
            "- get_daily_forecast(city_id=None, latitude=None, longitude=None): Retrieves the multi-day weather forecast for a specified city ID or coordinates.\n"
            "\n"
            "Core Instructions:\n"
            "1.  **Carefully analyze the user's request**: Understand all components of the user's query. Determine if the user needs weather warning information, weather forecast information, or both.\n"
            "2.  **Identify Information Needs**:\n"
            "    * If the user only asks for warnings (e.g., \"Are there any warnings in Beijing?\"), only use `get_weather_warning`.\n"
            "    * If the user only asks for the forecast (e.g., \"What's the weather like in Beijing tomorrow?\"), only use `get_daily_forecast`.\n"
            "    * **If the user's question includes multiple aspects**, such as asking about **warning status** and also asking **if it's suitable for a certain activity** (which implies a query about future weather, like \"Have there been high temperature warnings in Beijing in the last week? Is it suitable for outdoor activities?\"), you need to **call both tools sequentially**.\n"
            "3.  **Call Tools as Needed**:\n"
            "    * **Prioritize getting warning information**: If warning information is needed, first call `get_weather_warning`.\n"
            "    * **Get the weather forecast**: If the user mentions a specific time period (e.g., \"weekend\", \"next three days\", \"next week\") or asks about activity suitability (which typically concerns the next few days), call `get_daily_forecast` to get the forecast for the corresponding period. For vague phrases like \"last week\" or \"recently\", interpret it as asking about *current* conditions and the *upcoming* few days (covered by the forecast). For questions like \"Is it suitable for outdoor activities?\", you should get the forecast for at least the next 2-3 days (e.g., today, tomorrow, the day after tomorrow, or the upcoming weekend) to support your judgment.\n"
            "    * **Ensure tool call order**: When multiple tools need to be called, they should be called in a logical sequence. For example, first get the warning, then get the forecast. Wait for one tool to finish executing before deciding whether to call the next tool or generate a response.\n"
            "4.  **Information Integration and Response**:\n"
            "    * After obtaining all necessary information (warning, forecast), you **must synthesize and analyze this information**.\n"
            "    * **Completely answer the user's question**: Ensure you answer all parts of the user's query.\n"
            "    * **Provide advice**: If the user asks about activity suitability, based on the retrieved warning status and forecast information (temperature, weather condition - clear/rainy, wind strength, etc.), provide a clear, data-supported recommendation (e.g., \"Currently there are no high temperature warnings, but it's expected to rain this weekend, so it's not very suitable for outdoor activities,\" or \"It will be sunny for the next few days with no warnings, suitable for outdoor activities.\").\n"
            "5.  **Tool Usage Details**:\n"
            "    * When using the tools, retain the full context of the user's original question.\n"
            "    * Unless explicitly requested by the user, do not insert specific times of day (e.g., \"3 PM\") into the search query or your response.\n"
            "    * When city information is needed, if the user provides a city name (e.g., \"Beijing\"), use the corresponding `city_id` (e.g., Beijing's city_id might be '101010100').\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        tools = await self.server.list_tools()
        available_tools = [tool.to_openai_format() for tool in tools]

        max_tool_turns = 5 # 设置一个最大工具调用回合数，防止无限循环

        for _ in range(max_tool_turns):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=available_tools,
                    tool_choice="auto" # 允许模型决定是否调用工具
                )

                content = response.choices[0].message
                finish_reason = response.choices[0].finish_reason

                if finish_reason == "stop":
                    # 模型生成了最终的文本回复
                    messages.append({"role": "assistant", "content": content.content})
                    return content.content
                elif finish_reason == "tool_calls":
                    # 模型预测了工具调用
                    messages.append(content.model_dump()) # 将 assistant tool_calls 消息添加到历史

                    tool_outputs = []
                    for tool_call in content.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        try:
                            # 执行工具
                            result = await self.server.execute_tool(tool_name, tool_args)
                            logger.info(f"工具执行完成: {tool_name}")
                            # 将工具结果添加到 tool_outputs 列表
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                # MCP tool results have 'content' which is a list of Parts
                                # Assuming text content is the first part
                                "output": result.content[0].text
                            })
                        except Exception as tool_exec_error:
                            logger.error(f"工具执行失败 {tool_name}: {str(tool_exec_error)}")
                            # 如果工具执行失败，也需要向模型反馈失败信息
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": f"Error executing tool {tool_name}: {str(tool_exec_error)}"
                            })

                    # 将所有工具结果作为 tool 消息添加到历史
                    # 注意：OpenAI API 要求每个 tool_call_id 对应一个 tool 消息
                    # 如果模型预测了多个工具调用，这里需要为每个结果添加 tool 消息
                    for output in tool_outputs:
                        messages.append({
                            "role": "tool",
                            "content": output["output"],
                            "tool_call_id": output["tool_call_id"],
                        })

                    # 继续下一轮循环，将完整的消息历史发送给模型，让它根据工具结果继续
                    logger.info(f"工具调用回合完成，继续与模型交互...")
                    continue # 继续循环，发送包含工具结果的消息历史给模型
                else:
                    # 发生未知情况或错误
                    logger.error(f"模型返回意外的 finish_reason: {finish_reason}")
                    return f"处理你的查询时遇到意外情况 ({finish_reason})"

            except Exception as e:
                logger.error(f"处理查询时出错: {str(e)}")
                return f"处理你的查询时发生错误: {str(e)}"

        # 如果循环达到最大次数仍未得到最终回复
        logger.warning("达到最大工具调用回合数，未能获得最终回复")
        return "抱歉，处理你的请求时出现问题，未能获得最终结果。"

    @classmethod
    async def ask_once(cls, query: str) -> str:
        """
        便捷方法：一次性完成初始化、查询与清理

        用法:
            result = await MCPClient.ask_once("北京这个周末适合户外活动吗？")

        说明:
            - 内部自动创建 `Configuration` 和 `MCPClient`
            - 自动完成 `initialize()` 与 `cleanup()`
            - 适合无需持久会话的单次调用场景
        """
        logger.info(f"便捷方法调用 - ask_once: query={query}")
        config = Configuration()
        client = cls(config)
        try:
            await client.initialize()
            return await client.process_query(query)
        except Exception as e:
            logger.error(f"ask_once 执行失败: {str(e)}")
            raise
        finally:
            try:
                await client.cleanup()
            except Exception as cleanup_error:
                logger.error(f"ask_once 清理失败: {str(cleanup_error)}")

    async def chat_loop(self) -> None:
        """运行交互式聊天循环"""
        logger.info("开始聊天会话...")
        
        while True:
            try:
                query = input("\n请输入你的问题 (输入 'quit' 或 'exit' 退出): ").strip()
                
                if query.lower() in ['quit', 'exit']:
                    logger.info("结束聊天会话...")
                    break
                    
                response = await self.process_query(query)
                print(f"\n助手: {response}")
                
            except KeyboardInterrupt:
                logger.info("\n收到键盘中断，结束会话...")
                break
            except Exception as e:
                logger.error(f"聊天循环中出错: {str(e)}")
                print(f"\n发生错误: {str(e)}")
                
    async def cleanup(self) -> None:
        """清理客户端资源"""
        if self.server:
            await self.server.cleanup()

class MCPWeatherClient:
    """精简版 MCP 天气客户端，用于直接调用 MCP 天气工具。

    提供易用的上下文管理与方法封装，适合编程式调用而非经由 LLM 的工具编排。
    """

    def __init__(self) -> None:
        self.server: Optional[MCPServer] = None

    async def __aenter__(self) -> "MCPWeatherClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def connect(self) -> None:
        """建立到本地 MCP 天气服务器的连接。"""
        server_path = _resolve_mcp_server_path()
        self.server = MCPServer(server_path)
        await self.server.initialize()

    async def close(self) -> None:
        """关闭连接并清理资源。"""
        if self.server:
            await self.server.cleanup()
            self.server = None

    async def get_daily_forecast(self, location: str, days: int = 3) -> str:
        """调用 MCP 工具 `get_daily_forecast` 获取天气预报。

        参数:
            location: 位置（城市名/城市ID/经纬度）
            days: 预报天数，支持 3、7、10、15、30

        返回:
            格式化后的天气预报字符串
        """
        if not self.server:
            raise RuntimeError("MCPWeatherClient 尚未连接。请先调用 connect() 或使用 async with。")

        valid_days = {3, 7, 10, 15, 30}
        if days not in valid_days:
            logger.warning(f"无效的 days={days}，将回退为 3")
            days = 3

        # 解析位置参数，将中文城市名转换为城市ID
        resolved_location = _resolve_city_location(location)
        arguments: Dict[str, Any] = {"location": resolved_location, "days": int(days)}
        result = await self.server.execute_tool("get_daily_forecast", arguments)

        # MCP 返回结果通常包含 content 列表与 Part 文本
        try:
            # result.content[0].text 形态（与上文 MCPClient.process_query 保持一致）
            return result.content[0].text  # type: ignore[attr-defined]
        except Exception:
            # 兜底返回字符串
            return str(result)



async def fetch_forecast_via_mcp(location: str, days: int = 3) -> str:
    """
    通过 MCP 获取天气预报
    
    这是一个简化的接口函数，自动处理 MCP 客户端的创建、连接和清理工作。
    适用于只需要获取一次天气预报的场景。
    
    参数:
        location (str): 位置信息，支持以下格式：
                       - 中文城市名（如"北京"、"上海"等，会自动转换为城市ID）
                       - 城市ID（如"101010100"表示北京）  
                       - 经纬度坐标（如"116.41,39.92"）
        days (int): 预报天数，默认为3天，支持3、7、10、15、30天
        
    返回:
        str: 格式化的天气预报信息
        
    示例:
        >>> forecast = await fetch_forecast_via_mcp("北京", 7)        # 中文城市名
        >>> forecast = await fetch_forecast_via_mcp("101010100", 7)   # 城市ID
        >>> forecast = await fetch_forecast_via_mcp("116.41,39.92", 7) # 经纬度
        >>> print(forecast)
    """
    logger.info(f"通过 MCP 工具获取天气预报: 位置={location}, 天数={days}")
    try:
        async with MCPWeatherClient() as client:
            result = await client.get_daily_forecast(location=location, days=days)
            logger.info("MCP 工具调用成功")
            return result
    except Exception as e:
        logger.error(f"MCP 工具调用失败: {str(e)}")
        raise
