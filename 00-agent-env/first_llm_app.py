#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 第一个大模型应用 - 持续交互版本
====================================

这是一个完整的大模型应用示例，展示如何：
1. 从环境变量读取API配置
2. 调用OpenAI兼容的大模型API
3. 处理基础对话和角色扮演
4. 实现错误处理机制
5. 支持持续交互和多轮对话
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

def init_environment():
    """初始化环境配置"""
    # 获取项目根目录路径（当前脚本所在目录的上级目录）
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    # 加载环境变量文件
    load_dotenv(dotenv_path=env_file)
    
    # 显示环境文件路径信息
    print(f"📁 项目根目录: {project_root}")
    print(f"📄 环境文件路径: {env_file}")
    print(f"📋 环境文件存在: {'✅ 是' if env_file.exists() else '❌ 否'}")
    
    return env_file

def check_api_config():
    """检查API配置"""
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL')
    model = os.getenv('DEFAULT_MODEL')
    
    if not api_key:
        print("❌ 错误：未找到API密钥！")
        print("请确保：")
        print("1. 已在项目根目录创建.env文件（可从env.template复制）")
        print("2. 在.env文件中设置了OPENAI_API_KEY")
        return None, None, None
    
    return api_key, base_url, model

def create_client(api_key, base_url):
    """创建OpenAI客户端"""
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    return client

def print_welcome():
    """打印欢迎信息"""
    print("\n" + "="*60)
    print("🤖 欢迎使用AI助手！")
    print("="*60)
    print("💡 使用说明：")
    print("   • 直接输入您的问题或想法")
    print("   • 输入 'quit'、'exit' 或 'q' 退出程序")
    print("   • 输入 'clear' 清空对话历史")
    print("   • 输入 'help' 查看帮助信息")
    print("="*60)

def print_help():
    """打印帮助信息"""
    print("\n📚 帮助信息：")
    print("="*40)
    print("🔤 基本命令：")
    print("   quit/exit/q  - 退出程序")
    print("   clear        - 清空对话历史")
    print("   help         - 显示帮助信息")
    print("   stats        - 显示会话统计")
    print("\n💬 对话技巧：")
    print("   • 可以进行多轮对话，AI会记住上下文")
    print("   • 尝试不同类型的问题：翻译、编程、创意等")
    print("   • 如果回答不满意，可以要求更详细的解释")
    print("="*40)

def print_stats(total_messages, total_tokens):
    """打印会话统计信息"""
    print(f"\n📊 会话统计：")
    print(f"   💬 总对话轮数: {total_messages}")
    print(f"   🔤 总消耗tokens: {total_tokens}")

def get_user_input():
    """获取用户输入"""
    try:
        user_input = input("\n👤 您: ").strip()
        return user_input
    except KeyboardInterrupt:
        print("\n\n👋 检测到Ctrl+C，正在退出...")
        return "quit"
    except EOFError:
        print("\n\n👋 检测到EOF，正在退出...")
        return "quit"

def chat_with_ai(client, model, messages, max_tokens, temperature):
    """与AI进行对话"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        reply = response.choices[0].message.content
        usage = response.usage
        
        return reply, usage
    except Exception as e:
        print(f"❌ API调用失败: {str(e)}")
        print("\n🔧 故障排除建议：")
        print("1. 检查API密钥是否正确")
        print("2. 确认网络连接是否正常")
        print("3. 检查API服务是否可用")
        print("4. 确认账户余额是否充足")
        return None, None

def main():
    """主程序入口"""
    print("🚀 Agent-101: 大模型持续交互应用")
    print("=" * 50)
    
    # 1. 初始化环境
    env_file = init_environment()
    
    # 2. 检查API配置
    api_key, base_url, model = check_api_config()
    if not api_key:
        return
    
    # 3. 创建客户端
    client = create_client(api_key, base_url)
    
    print(f"✅ 客户端初始化成功")
    print(f"📡 API地址: {base_url}")
    print(f"🤖 使用模型: {model}")
    
    # 4. 获取配置参数
    max_tokens = int(os.getenv('MAX_TOKENS', '1000'))
    temperature = float(os.getenv('TEMPERATURE', '0.7'))
    
    # 5. 初始化对话历史
    messages = [
        {
            "role": "system", 
            "content": "你是一个友好的AI助手，用中文回答问题。请简洁明了地回答用户的问题，保持对话的连贯性。"
        }
    ]
    
    # 6. 会话统计
    total_messages = 0
    total_tokens = 0
    
    # 7. 显示欢迎信息
    print_welcome()
    
    # 8. 主对话循环
    while True:
        # 获取用户输入
        user_input = get_user_input()
        
        # 处理特殊命令
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 感谢使用AI助手，再见！")
            print_stats(total_messages, total_tokens)
            break
        elif user_input.lower() == 'clear':
            # 清空对话历史，保留系统提示
            messages = [messages[0]]  # 只保留系统消息
            total_messages = 0
            total_tokens = 0
            print("🧹 对话历史已清空！")
            continue
        elif user_input.lower() == 'help':
            print_help()
            continue
        elif user_input.lower() == 'stats':
            print_stats(total_messages, total_tokens)
            continue
        elif not user_input:
            print("⚠️  请输入您的问题，或输入 'help' 查看帮助")
            continue
        
        # 添加用户消息到对话历史
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        # 调用AI进行对话
        print("🤖 AI助手正在思考...")
        reply, usage = chat_with_ai(client, model, messages, max_tokens, temperature)
        
        if reply is None:
            # 如果API调用失败，移除刚添加的用户消息
            messages.pop()
            continue
        
        # 添加AI回复到对话历史
        messages.append({
            "role": "assistant",
            "content": reply
        })
        
        # 显示AI回复
        print(f"\n🤖 AI助手: {reply}")
        
        # 显示本轮统计
        print(f"\n📊 本轮统计: 输入{usage.prompt_tokens} + 输出{usage.completion_tokens} = 总计{usage.total_tokens} tokens")
        
        # 更新总统计
        total_messages += 1
        total_tokens += usage.total_tokens
        
        # 控制对话历史长度（可选）
        # 如果对话历史太长，可以保留最近的几轮对话
        if len(messages) > 21:  # 系统消息 + 10轮对话（每轮2条消息）
            # 保留系统消息和最近的10轮对话
            messages = [messages[0]] + messages[-20:]
            print("💡 对话历史已自动精简，保留最近10轮对话")

if __name__ == "__main__":
    main() 