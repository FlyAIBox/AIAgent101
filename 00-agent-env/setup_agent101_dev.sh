#!/bin/bash

# Agent-101 环境配置脚本
# 适用于 Ubuntu 22.04 + Python 3.10.18

set -e

echo "🚀 开始配置 Agent-101 开发环境..."

# 检查系统版本
echo "📋 检查系统环境..."
if [[ $(lsb_release -rs) != "22.04" ]]; then
    echo "⚠️  警告: 推荐使用 Ubuntu 22.04 LTS"
fi

# 更新系统包
echo "🔄 更新系统包..."
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
echo "📦 安装基础依赖..."
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 安装 NVIDIA GPU 驱动
echo "🖥️  安装 NVIDIA GPU 驱动..."
if lspci | grep -i nvidia > /dev/null; then
    echo "✅ 检测到 NVIDIA GPU 硬件"
    
    # 检查是否已安装驱动
    if ! command -v nvidia-smi &> /dev/null; then
        echo "🔧 安装 NVIDIA GPU 驱动..."
        
        # 添加 NVIDIA 官方仓库
        sudo apt install -y ubuntu-drivers-common
        
        # 自动安装推荐的驱动
        sudo ubuntu-drivers autoinstall
        
        echo "✅ NVIDIA 驱动安装完成"
        echo "⚠️  请重启系统后再继续执行脚本"
        echo "重启命令: sudo reboot"
        
        # 提示用户重启
        read -p "是否现在重启系统? (y/n): " restart_choice
        if [[ $restart_choice == "y" || $restart_choice == "Y" ]]; then
            sudo reboot
        else
            echo "请手动重启系统后再运行此脚本"
            exit 0
        fi
    else
        echo "✅ NVIDIA 驱动已安装"
        nvidia-smi
    fi
else
    echo "⚠️  未检测到 NVIDIA GPU 硬件"
fi

# 安装 CUDA 12.1
echo "🔥 安装 CUDA 12.1..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU 检测成功，开始安装 CUDA 12.1"
    
    # 检查 CUDA 是否已安装
    if command -v nvcc &> /dev/null; then
        CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
        echo "✅ CUDA 已安装，版本: $CUDA_VERSION"
    else
        echo "🔧 安装 CUDA 12.1..."
        
        # 创建临时目录
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        
        # 下载 CUDA 12.1 安装包
        echo "📥 下载 CUDA 12.1 安装包..."
        wget -q --show-progress https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
        
        # 安装 CUDA（忽略驱动安装提示）
        echo "🔧 安装 CUDA 12.1 工具包..."
        sudo sh cuda_12.1.0_530.30.02_linux.run --silent --toolkit --toolkitpath=/usr/local/cuda-12.1 --no-opengl-libs --override
        
        # 检查环境变量是否已存在
        if ! grep -q "/usr/local/cuda-12.1/bin" ~/.bashrc; then
            echo 'export PATH="/usr/local/cuda-12.1/bin:$PATH"' >> ~/.bashrc
        fi
        
        if ! grep -q "/usr/local/cuda-12.1/lib64" ~/.bashrc; then
            echo 'export LD_LIBRARY_PATH="/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH"' >> ~/.bashrc
        fi
        
        # 创建符号链接
        sudo ln -sf /usr/local/cuda-12.1 /usr/local/cuda
        
        # 重新加载环境变量
        export PATH="/usr/local/cuda-12.1/bin:$PATH"
        export LD_LIBRARY_PATH="/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH"
        
        echo "✅ CUDA 12.1 安装完成"
        
        # 验证安装
        if command -v nvcc &> /dev/null; then
            echo "🎉 CUDA 安装验证成功:"
            nvcc --version
        else
            echo "⚠️  CUDA 安装可能有问题，请重新加载环境变量: source ~/.bashrc"
        fi
        
        # 清理安装文件
        cd /
        rm -rf "$TEMP_DIR"
    fi
else
    echo "⚠️  未检测到 NVIDIA GPU，跳过 CUDA 安装"
fi

# 安装 Python 3.10.18
echo "🐍 安装 Python 3.10.18..."
if python3.10 --version &> /dev/null; then
    PYTHON_VERSION=$(python3.10 --version | cut -d' ' -f2)
    echo "✅ Python 3.10 已安装，版本: $PYTHON_VERSION"
else
    echo "🔧 安装 Python 3.10.18..."
    
    # 添加 deadsnakes PPA（用于获取最新 Python 版本）
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    
    # 安装 Python 3.10 和相关工具
    sudo apt install -y \
        python3.10 \
        python3.10-dev \
        python3.10-distutils \
        python3.10-venv \
        python3-pip
    
    # 创建符号链接
    sudo ln -sf /usr/bin/python3.10 /usr/local/bin/python3.10
    
    echo "✅ Python 3.10.18 安装完成"
    python --version
fi


# 检查是否已安装 Conda
if ! command -v conda &> /dev/null; then
    echo "🐍 安装 Miniconda..."
    
    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # 下载 Miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    
    # 安装 Miniconda 到 ~/miniconda3 目录
    bash miniconda.sh -b -p $HOME/miniconda3
    
    # 添加到环境变量
    echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
    
    # 立即加载环境变量
    export PATH="$HOME/miniconda3/bin:$PATH"
    
    # 初始化 conda
    $HOME/miniconda3/bin/conda init bash
    
    # 清理安装文件
    cd /
    rm -rf "$TEMP_DIR"
    
    echo "✅ Miniconda 安装完成"
else
    echo "✅ Conda 已安装"
fi

# 初始化 Conda
echo "🔧 初始化 Conda..."
if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source $HOME/anaconda3/etc/profile.d/conda.sh
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source $HOME/miniconda3/etc/profile.d/conda.sh
elif [ -f "$HOME/miniconda/etc/profile.d/conda.sh" ]; then
    source $HOME/miniconda/etc/profile.d/conda.sh
else
    echo "⚠️  Conda 配置文件未找到，尝试重新加载环境变量..."
    source ~/.bashrc
fi




# 创建虚拟环境
echo "🌟 创建 Agent-101 虚拟环境..."

# 确保 conda 命令可用
if ! command -v conda &> /dev/null; then
    echo "⚠️  Conda 命令不可用，尝试重新加载环境变量..."
    source ~/.bashrc
    
    # 如果还是不可用，手动设置路径
    if ! command -v conda &> /dev/null; then
        if [ -f "$HOME/anaconda3/bin/conda" ]; then
            export PATH="$HOME/anaconda3/bin:$PATH"
        elif [ -f "$HOME/miniconda3/bin/conda" ]; then
            export PATH="$HOME/miniconda3/bin:$PATH"
        elif [ -f "$HOME/miniconda/bin/conda" ]; then
            export PATH="$HOME/miniconda/bin:$PATH"
        else
            echo "❌ 无法找到 conda 命令，请检查 Conda 安装"
            exit 1
        fi
    fi
fi

# 检查环境是否已存在
if conda env list | grep -q "^agent101\s"; then
    echo "✅ agent101 环境已存在"
else
    echo "🔧 创建 agent101 虚拟环境..."
    conda create -n agent101 python=3.10.18 -y
fi

# 激活虚拟环境
echo "🔧 激活 agent101 虚拟环境..."
conda activate agent101

# 安装项目依赖
echo "📚 安装项目依赖..."
pip install -r requirements.txt

# 安装和配置 Jupyter Lab
echo "📓 安装 Jupyter Lab..."
conda install -c conda-forge jupyterlab -y

echo "🔧 配置 Jupyter Lab..."
# 生成 Jupyter Lab 配置文件
jupyter lab --generate-config

# 获取配置文件路径
CONFIG_FILE="$HOME/.jupyter/jupyter_lab_config.py"

# 备份原配置文件
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    echo "✅ 已备份原配置文件到 $CONFIG_FILE.backup"
fi

# 修改配置文件
echo "🔧 修改 Jupyter Lab 配置..."
cat >> "$CONFIG_FILE" << 'EOF'

# Agent-101 Jupyter Lab 配置
c.ServerApp.allow_root = True  # 允许 root 用户启动（非 root 用户可注释此行）
c.ServerApp.ip = '*'           # 允许所有 IP 访问
c.ServerApp.open_browser = False  # 不自动打开浏览器
c.ServerApp.port = 8000        # 设置端口为 8000
EOF

echo "✅ Jupyter Lab 配置完成！"
echo ""
echo "📋 Jupyter Lab 使用说明："
echo "1. 后台启动命令: nohup jupyter lab --port=8000 --NotebookApp.token='your_password' --notebook-dir=./ &"
echo "2. 日志文件: nohup.out"
echo "3. 访问地址: http://your_server_ip:8000"
echo "4. 请将 'your_password' 替换为您的密码"
echo ""

# 安装开发工具
echo "🛠️  安装开发工具..."

#!/bin/bash

# 检查 Git 是否安装
if ! command -v git &> /dev/null
then
    echo "🚨 检测到 Git 未安装。"
    echo "请先在 Ubuntu 22.04 上安装 Git，运行以下命令："
    echo "-----------------------------------"
    echo "sudo apt update"
    echo "sudo apt install git"
    echo "-----------------------------------"
    echo "安装完成后，请再次运行此脚本。"
    exit 1
fi

# 检查 Git 用户名是否已配置
if [[ -z $(git config --global user.name) ]]; then
    echo "🔧 配置 Git 用户信息..."
    read -p "请输入您的 Git 用户名: " git_name
    read -p "请输入您的 Git 邮箱: " git_email
    git config --global user.name "$git_name"
    git config --global user.email "$git_email"
    echo "✅ Git 用户信息配置完成！"
else
    echo "✅ Git 用户名已配置: $(git config --global user.name)"
    echo "✅ Git 邮箱已配置: $(git config --global user.email)"
fi

# 创建环境变量文件
echo "🔐 创建环境变量模板..."
if [ ! -f "env.template" ]; then
    echo "❌ 环境变量模板文件不存在，请确保 env.template 文件存在"
    exit 1
fi

echo "📝 请复制 env.template 为 .env 并填入您的 API Keys"

# 完成提示
echo ""
echo "🎉 Agent-101 环境配置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 重新加载环境变量: source ~/.bashrc"
echo "2. 激活虚拟环境: conda activate agent101"
echo "3. 复制环境变量: cp env.template .env"
echo "4. 编辑 .env 文件，填入您的 API Keys"
echo "5. 检查GPU和CUDA环境: python chapter01-llm-env/linux_ops/check_gpu_cuda.py"
echo "6. 启动 Jupyter Lab: ./chapter01-llm-env/jupyter-ops/start_jupyter.sh your_password"
echo "7. 运行第一个应用: python first_llm_app.py"
echo ""
echo "🛠️  实用工具脚本："
echo "• GPU/CUDA检查: python chapter01-llm-env/check_gpu_cuda.py"
echo "• Jupyter Lab启动: ./chapter01-llm-env/start_jupyter.sh [password]"
echo ""
echo "⚠️  重要提示："
echo "• 如果 conda 命令不可用，请运行: source ~/.bashrc"
echo "• 如果仍有问题，请重新启动终端或重新登录"
echo ""
echo "🔗 更多信息请查看 README.md"
echo "💡 如有问题，请访问项目 GitHub 仓库获取帮助"
echo ""
echo "⭐ 如果这个项目对您有帮助，请给个 Star 支持！" 