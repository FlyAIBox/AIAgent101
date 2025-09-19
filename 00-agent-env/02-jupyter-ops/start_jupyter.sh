#!/bin/bash

# Agent-101 Jupyter Lab 启动脚本
# 使用方法: ./start_jupyter.sh [password]

set -e

echo "🚀 启动 Jupyter Lab..."

# 检查是否在 agent101 环境中
if [[ "$CONDA_DEFAULT_ENV" != "agent101" ]]; then
    echo "⚠️  请先激活 agent101 环境:"
    echo "conda activate agent101"
    exit 1
fi

# 检查是否提供了密码参数
if [ -z "$1" ]; then
    echo "💡 使用方法: ./start_jupyter.sh your_password"
    echo "📝 示例: ./start_jupyter.sh mypassword123"
    exit 1
fi

PASSWORD="$1"
PORT=8000
NOTEBOOK_DIR="./"

# 获取服务器实际IP地址
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    echo "⚠️  无法获取服务器IP地址，使用默认localhost"
    SERVER_IP="localhost"
else
    echo "📍 检测到服务器IP地址: $SERVER_IP"
fi

# 检查端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $PORT 已被占用，请检查是否已有 Jupyter Lab 运行"
    echo "💡 查看运行的进程: ps aux | grep jupyter"
    echo "💡 停止进程: pkill -f jupyter"
    exit 1
fi

# 启动 Jupyter Lab
echo "🔧 启动配置:"
echo "   端口: $PORT"
echo "   密码: $PASSWORD"
echo "   工作目录: $NOTEBOOK_DIR"
echo "   访问地址: http://$SERVER_IP:$PORT"
echo ""

# 后台启动 Jupyter Lab
nohup jupyter lab \
    --port=$PORT \
    --ip=0.0.0.0 \
    --NotebookApp.token="$PASSWORD" \
    --notebook-dir="$NOTEBOOK_DIR" \
    --allow-root \
    > nohup.out 2>&1 &

JUPYTER_PID=$!

echo "✅ Jupyter Lab 已在后台启动!"
echo "📋 服务信息:"
echo "   进程ID: $JUPYTER_PID"
echo "   日志文件: nohup.out"
echo "   访问地址: http://$SERVER_IP:$PORT"
echo "   密码: $PASSWORD"
echo ""
echo "📝 常用命令:"
echo "   查看日志: tail -f nohup.out"
echo "   停止服务: pkill -f jupyter"
echo "   查看进程: ps aux | grep jupyter"
echo ""
echo "✅✅✅ Jupyter Lab 启动完成！" 