#!/bin/bash

# Ubuntu 22.04.4 快速配置脚本
# 作者: FlyAIBox
# 用途: 快速配置Ubuntu系统基础环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要以root用户身份运行此脚本"
        exit 1
    fi
}

# 更新系统
update_system() {
    log_step "更新系统软件包..."
    sudo apt update && sudo apt upgrade -y
    log_info "系统更新完成"
}

# 安装基础工具
install_basic_tools() {
    log_step "安装基础工具..."
    sudo apt install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        tree \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        bash-completion \
        xclip
    log_info "基础工具安装完成"
}

# 配置Git
configure_git() {
    log_step "配置Git环境..."
    
    read -p "请输入您的Git用户名: " git_username
    read -p "请输入您的Git邮箱: " git_email
    
    git config --global user.name "$git_username"
    git config --global user.email "$git_email"
    
    log_info "Git配置完成: $git_username <$git_email>"
    
    # 生成SSH密钥
    if [ ! -f ~/.ssh/id_ed25519 ]; then
        log_step "生成SSH密钥..."
        ssh-keygen -t ed25519 -C "$git_email" -f ~/.ssh/id_ed25519 -N ""
        eval "$(ssh-agent -s)"
        ssh-add ~/.ssh/id_ed25519
        
        echo -e "\n${GREEN}SSH公钥内容:${NC}"
        cat ~/.ssh/id_ed25519.pub
        echo -e "\n${YELLOW}请将上述公钥添加到您的Git服务商（GitHub/GitLab/Gitee）${NC}"
    else
        log_info "SSH密钥已存在，跳过生成"
    fi
}

# 安装Docker
install_docker() {
    log_step "安装Docker..."
    
    # 添加Docker官方GPG密钥
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # 添加Docker仓库
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # 将用户添加到docker组
    sudo usermod -aG docker $USER
    
    log_info "Docker安装完成，请重新登录以使用docker命令"
}

# 安装Node.js (使用NVM)
install_nodejs() {
    log_step "安装Node.js..."
    
    # 安装NVM
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    
    # 重新加载bashrc
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    
    # 安装Node.js 22.14.0
    nvm install 22.14.0
    nvm use 22.14.0
    nvm alias default 22.14.0
    
    # 配置npm镜像源
    npm config set registry https://registry.npmmirror.com
    
    log_info "Node.js安装完成，版本: $(node -v)"
}

# 配置时区
configure_timezone() {
    log_step "配置时区为北京时间..."
    sudo timedatectl set-timezone Asia/Shanghai
    log_info "时区配置完成: $(timedatectl | grep 'Time zone')"
}

# 配置DNS
configure_dns() {
    log_step "配置DNS服务器..."
    
    # 备份原配置
    sudo cp /etc/systemd/resolved.conf /etc/systemd/resolved.conf.bak
    
    # 配置DNS
    sudo tee /etc/systemd/resolved.conf > /dev/null <<EOF
[Resolve]
DNS=8.8.8.8 114.114.114.114
FallbackDNS=1.1.1.1
Domains=
LLMNR=yes
MulticastDNS=yes
DNSSEC=yes
Cache=no-negative
EOF
    
    sudo systemctl restart systemd-resolved
    log_info "DNS配置完成"
}

# 优化系统性能
optimize_system() {
    log_step "优化系统性能..."
    
    # 增加文件描述符限制
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    
    # 优化内核参数
    sudo tee -a /etc/sysctl.conf > /dev/null <<EOF

# 优化网络性能
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# 优化文件系统
fs.file-max = 2097152
vm.swappiness = 10
EOF
    
    log_info "系统性能优化完成"
}

# 安装Python开发环境
install_python_env() {
    log_step "安装Python开发环境..."
    
    sudo apt install -y python3-pip python3-venv python3-dev
    
    # 升级pip
    pip3 install --upgrade pip
    
    # 配置pip镜像源
    mkdir -p ~/.pip
    tee ~/.pip/pip.conf > /dev/null <<EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
    
    log_info "Python开发环境安装完成"
}

# 创建常用目录
create_directories() {
    log_step "创建常用目录..."
    
    mkdir -p ~/workspace
    mkdir -p ~/downloads
    mkdir -p ~/scripts
    mkdir -p ~/.config
    
    log_info "常用目录创建完成"
}

# 主菜单
main_menu() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}    Ubuntu 22.04.4 快速配置脚本${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo "请选择要执行的操作:"
    echo "1) 完整安装 (推荐新系统使用)"
    echo "2) 更新系统"
    echo "3) 安装基础工具"
    echo "4) 配置Git环境"
    echo "5) 安装Docker"
    echo "6) 安装Node.js"
    echo "7) 配置时区"
    echo "8) 配置DNS"
    echo "9) 优化系统性能"
    echo "10) 安装Python环境"
    echo "11) 创建常用目录"
    echo "0) 退出"
    echo -e "${BLUE}===========================================${NC}"
}

# 完整安装
full_install() {
    log_info "开始完整安装配置..."
    
    update_system
    install_basic_tools
    configure_git
    install_docker
    install_nodejs
    configure_timezone
    configure_dns
    optimize_system
    install_python_env
    create_directories
    
    log_info "完整安装配置完成！"
    log_warn "请重新登录系统以使所有配置生效"
}

# 主函数
main() {
    check_root
    
    if [ "$1" = "--full" ]; then
        full_install
        exit 0
    fi
    
    while true; do
        main_menu
        read -p "请输入选项 [0-11]: " choice
        
        case $choice in
            1)
                full_install
                break
                ;;
            2)
                update_system
                ;;
            3)
                install_basic_tools
                ;;
            4)
                configure_git
                ;;
            5)
                install_docker
                ;;
            6)
                install_nodejs
                ;;
            7)
                configure_timezone
                ;;
            8)
                configure_dns
                ;;
            9)
                optimize_system
                ;;
            10)
                install_python_env
                ;;
            11)
                create_directories
                ;;
            0)
                log_info "感谢使用Ubuntu快速配置脚本！"
                exit 0
                ;;
            *)
                log_error "无效的选项，请重新选择"
                ;;
        esac
        
        echo
        read -p "按任意键继续..." -n 1
        echo
    done
}

# 执行主函数
main "$@" 