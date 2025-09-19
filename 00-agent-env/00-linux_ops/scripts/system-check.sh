#!/bin/bash

# Ubuntu 22.04.4 系统检查脚本
# 作者: FlyAIBox
# 用途: 检查系统配置状态和开发环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 符号定义
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"

# 报告变量
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNINGS=0

# 检查函数
check_passed() {
    echo -e "${GREEN}${CHECK}${NC} $1"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_failed() {
    echo -e "${RED}${CROSS}${NC} $1"
    ((TOTAL_CHECKS++))
}

check_warning() {
    echo -e "${YELLOW}${WARNING}${NC} $1"
    ((WARNINGS++))
    ((TOTAL_CHECKS++))
}

check_info() {
    echo -e "${CYAN}${INFO}${NC} $1"
}

section_header() {
    echo
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

# 检查系统基本信息
check_system_info() {
    section_header "系统基本信息"
    
    # 操作系统版本
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo -e "${PURPLE}操作系统:${NC} $PRETTY_NAME"
        if [[ "$VERSION_ID" == "22.04" ]]; then
            check_passed "Ubuntu 22.04 LTS 版本正确"
        else
            check_warning "不是Ubuntu 22.04 LTS版本"
        fi
    else
        check_failed "无法获取操作系统信息"
    fi
    
    # 内核版本
    KERNEL_VERSION=$(uname -r)
    echo -e "${PURPLE}内核版本:${NC} $KERNEL_VERSION"
    
    # 系统架构
    ARCH=$(uname -m)
    echo -e "${PURPLE}系统架构:${NC} $ARCH"
    if [[ "$ARCH" == "x86_64" ]]; then
        check_passed "x86_64 架构支持良好"
    else
        check_warning "非x86_64架构，某些软件可能不兼容"
    fi
    
    # 系统运行时间
    UPTIME=$(uptime -p)
    echo -e "${PURPLE}运行时间:${NC} $UPTIME"
}

# 检查硬件资源
check_hardware() {
    section_header "硬件资源检查"
    
    # CPU信息
    CPU_CORES=$(nproc)
    CPU_INFO=$(grep "model name" /proc/cpuinfo | head -n1 | cut -d: -f2 | xargs)
    echo -e "${PURPLE}CPU:${NC} $CPU_INFO"
    echo -e "${PURPLE}CPU核心数:${NC} $CPU_CORES"
    if [ $CPU_CORES -ge 2 ]; then
        check_passed "CPU核心数满足要求 (>= 2)"
    else
        check_warning "CPU核心数较少，可能影响性能"
    fi
    
    # 内存信息
    TOTAL_MEM=$(free -h | grep Mem | awk '{print $2}')
    USED_MEM=$(free -h | grep Mem | awk '{print $3}')
    FREE_MEM=$(free -h | grep Mem | awk '{print $4}')
    echo -e "${PURPLE}内存总量:${NC} $TOTAL_MEM"
    echo -e "${PURPLE}已用内存:${NC} $USED_MEM"
    echo -e "${PURPLE}可用内存:${NC} $FREE_MEM"
    
    # 检查内存是否足够
    TOTAL_MEM_GB=$(free -g | grep Mem | awk '{print $2}')
    if [ $TOTAL_MEM_GB -ge 8 ]; then
        check_passed "内存容量充足 (>= 8GB)"
    elif [ $TOTAL_MEM_GB -ge 4 ]; then
        check_warning "内存容量较小，建议增加到8GB以上"
    else
        check_failed "内存容量不足，强烈建议升级内存"
    fi
    
    # 磁盘空间
    DISK_USAGE=$(df -h / | tail -1)
    DISK_USED_PERCENT=$(echo $DISK_USAGE | awk '{print $5}' | sed 's/%//')
    echo -e "${PURPLE}根分区使用情况:${NC} $DISK_USAGE"
    
    if [ $DISK_USED_PERCENT -lt 80 ]; then
        check_passed "磁盘空间充足 (使用率 < 80%)"
    elif [ $DISK_USED_PERCENT -lt 90 ]; then
        check_warning "磁盘空间紧张 (使用率 >= 80%)"
    else
        check_failed "磁盘空间严重不足 (使用率 >= 90%)"
    fi
}

# 检查网络连接
check_network() {
    section_header "网络连接检查"
    
    # 检查网络接口
    ACTIVE_INTERFACES=$(ip link show | grep "state UP" | wc -l)
    echo -e "${PURPLE}活动网络接口数:${NC} $ACTIVE_INTERFACES"
    if [ $ACTIVE_INTERFACES -gt 0 ]; then
        check_passed "网络接口正常"
    else
        check_failed "没有活动的网络接口"
    fi
    
    # 检查DNS解析
    if nslookup google.com >/dev/null 2>&1; then
        check_passed "DNS解析正常"
    else
        check_failed "DNS解析失败"
    fi
    
    # 检查外网连通性
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        check_passed "外网连通性正常"
    else
        check_failed "无法连接外网"
    fi
    
    # 检查HTTPS连接
    if curl -s --max-time 5 https://www.google.com >/dev/null 2>&1; then
        check_passed "HTTPS连接正常"
    else
        check_warning "HTTPS连接可能存在问题（可能需要代理）"
    fi
}

# 检查基础软件
check_basic_software() {
    section_header "基础软件检查"
    
    # 检查包管理器
    if command -v apt >/dev/null 2>&1; then
        check_passed "APT包管理器可用"
    else
        check_failed "APT包管理器不可用"
    fi
    
    # 检查基础工具
    tools=("curl" "wget" "git" "vim" "htop" "tree" "unzip")
    for tool in "${tools[@]}"; do
        if command -v $tool >/dev/null 2>&1; then
            check_passed "$tool 已安装"
        else
            check_warning "$tool 未安装"
        fi
    done
    
    # 检查SSH服务
    if systemctl is-active --quiet ssh; then
        check_passed "SSH服务正在运行"
    else
        check_warning "SSH服务未运行"
    fi
}

# 检查开发环境
check_development_env() {
    section_header "开发环境检查"
    
    # 检查Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        echo -e "${PURPLE}Python版本:${NC} $PYTHON_VERSION"
        check_passed "Python3 已安装"
        
        if command -v pip3 >/dev/null 2>&1; then
            PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
            echo -e "${PURPLE}pip版本:${NC} $PIP_VERSION"
            check_passed "pip3 已安装"
        else
            check_warning "pip3 未安装"
        fi
    else
        check_warning "Python3 未安装"
    fi
    
    # 检查Node.js
    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node --version)
        echo -e "${PURPLE}Node.js版本:${NC} $NODE_VERSION"
        check_passed "Node.js 已安装"
        
        if command -v npm >/dev/null 2>&1; then
            NPM_VERSION=$(npm --version)
            echo -e "${PURPLE}npm版本:${NC} $NPM_VERSION"
            check_passed "npm 已安装"
        else
            check_warning "npm 未安装"
        fi
    else
        check_warning "Node.js 未安装"
    fi
    
    # 检查NVM
    if [ -d "$HOME/.nvm" ]; then
        check_passed "NVM 已安装"
    else
        check_warning "NVM 未安装"
    fi
    
    # 检查Git配置
    if git config --global user.name >/dev/null 2>&1; then
        GIT_USER=$(git config --global user.name)
        GIT_EMAIL=$(git config --global user.email)
        echo -e "${PURPLE}Git用户:${NC} $GIT_USER <$GIT_EMAIL>"
        check_passed "Git 用户配置正常"
    else
        check_warning "Git 用户未配置"
    fi
    
    # 检查SSH密钥
    if [ -f "$HOME/.ssh/id_ed25519" ] || [ -f "$HOME/.ssh/id_rsa" ]; then
        check_passed "SSH密钥已生成"
    else
        check_warning "SSH密钥未生成"
    fi
}

# 检查容器环境
check_container_env() {
    section_header "容器环境检查"
    
    # 检查Docker
    if command -v docker >/dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        echo -e "${PURPLE}Docker版本:${NC} $DOCKER_VERSION"
        check_passed "Docker 已安装"
        
        # 检查Docker服务状态
        if systemctl is-active --quiet docker; then
            check_passed "Docker服务正在运行"
        else
            check_warning "Docker服务未运行"
        fi
        
        # 检查Docker权限
        if docker ps >/dev/null 2>&1; then
            check_passed "Docker权限配置正确"
        else
            check_warning "Docker权限配置可能有问题，需要将用户加入docker组"
        fi
        
        # 检查Docker Compose
        if docker compose version >/dev/null 2>&1; then
            COMPOSE_VERSION=$(docker compose version --short)
            echo -e "${PURPLE}Docker Compose版本:${NC} $COMPOSE_VERSION"
            check_passed "Docker Compose 已安装"
        else
            check_warning "Docker Compose 未安装"
        fi
    else
        check_warning "Docker 未安装"
    fi
}

# 检查系统配置
check_system_config() {
    section_header "系统配置检查"
    
    # 检查时区
    TIMEZONE=$(timedatectl | grep "Time zone" | awk '{print $3}')
    echo -e "${PURPLE}时区设置:${NC} $TIMEZONE"
    if [[ "$TIMEZONE" == "Asia/Shanghai" ]]; then
        check_passed "时区设置为北京时间"
    else
        check_warning "时区不是北京时间"
    fi
    
    # 检查时间同步
    if timedatectl | grep -q "NTP service: active"; then
        check_passed "时间同步服务正常"
    else
        check_warning "时间同步服务未激活"
    fi
    
    # 检查防火墙状态
    if command -v ufw >/dev/null 2>&1; then
        UFW_STATUS=$(ufw status | head -n1 | awk '{print $2}')
        echo -e "${PURPLE}防火墙状态:${NC} $UFW_STATUS"
        if [[ "$UFW_STATUS" == "active" ]]; then
            check_info "防火墙已启用"
        else
            check_info "防火墙未启用"
        fi
    fi
    
    # 检查swap使用情况
    SWAP_USAGE=$(free | grep Swap | awk '{printf "%.1f%%", $3/$2 * 100}')
    echo -e "${PURPLE}Swap使用率:${NC} $SWAP_USAGE"
    
    # 检查文件描述符限制
    ULIMIT_N=$(ulimit -n)
    echo -e "${PURPLE}文件描述符限制:${NC} $ULIMIT_N"
    if [ $ULIMIT_N -ge 65536 ]; then
        check_passed "文件描述符限制充足"
    else
        check_warning "文件描述符限制较低，建议增加到65536"
    fi
}

# 性能测试
performance_test() {
    section_header "性能测试"
    
    # CPU测试
    echo -e "${PURPLE}正在进行CPU测试...${NC}"
    CPU_TIME=$(time (yes > /dev/null &) 2>&1 | sleep 1; kill $! 2>/dev/null; echo "done" | awk '/real/{print $2}')
    check_info "CPU测试完成"
    
    # 磁盘IO测试
    echo -e "${PURPLE}正在进行磁盘IO测试...${NC}"
    DD_RESULT=$(dd if=/dev/zero of=/tmp/test_io bs=1M count=100 2>&1 | grep -o '[0-9.]* MB/s' | tail -1)
    rm -f /tmp/test_io
    echo -e "${PURPLE}磁盘写入速度:${NC} $DD_RESULT"
    check_info "磁盘IO测试完成"
    
    # 网络测试
    echo -e "${PURPLE}正在测试网络延迟...${NC}"
    PING_RESULT=$(ping -c 3 8.8.8.8 2>/dev/null | tail -1 | awk -F '/' '{print $5}' 2>/dev/null)
    if [ ! -z "$PING_RESULT" ]; then
        echo -e "${PURPLE}平均网络延迟:${NC} ${PING_RESULT}ms"
        check_info "网络延迟测试完成"
    else
        check_warning "网络延迟测试失败"
    fi
}

# 生成总结报告
generate_report() {
    section_header "检查总结"
    
    echo -e "${PURPLE}总检查项:${NC} $TOTAL_CHECKS"
    echo -e "${GREEN}通过检查:${NC} $PASSED_CHECKS"
    echo -e "${YELLOW}警告项目:${NC} $WARNINGS"
    echo -e "${RED}失败项目:${NC} $((TOTAL_CHECKS - PASSED_CHECKS - WARNINGS))"
    
    # 计算健康度
    HEALTH_SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo -e "${PURPLE}系统健康度:${NC} ${HEALTH_SCORE}%"
    
    if [ $HEALTH_SCORE -ge 90 ]; then
        echo -e "${GREEN}${CHECK} 系统状态优秀！${NC}"
    elif [ $HEALTH_SCORE -ge 70 ]; then
        echo -e "${YELLOW}${WARNING} 系统状态良好，建议优化警告项${NC}"
    else
        echo -e "${RED}${CROSS} 系统状态需要改进，请处理失败项${NC}"
    fi
    
    echo
    echo -e "${CYAN}建议:${NC}"
    echo "1. 处理所有标记为❌的失败项"
    echo "2. 优化标记为⚠️的警告项"
    echo "3. 定期运行此检查脚本监控系统状态"
    echo "4. 参考Ubuntu运维配置手册进行详细配置"
}

# 主函数
main() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}    Ubuntu 22.04.4 系统检查脚本${NC}"
    echo -e "${BLUE}    开始时间: $(date)${NC}"
    echo -e "${BLUE}===========================================${NC}"
    
    check_system_info
    check_hardware
    check_network
    check_basic_software
    check_development_env
    check_container_env
    check_system_config
    
    # 询问是否进行性能测试
    echo
    read -p "是否进行性能测试？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        performance_test
    fi
    
    generate_report
    
    echo
    echo -e "${BLUE}检查完成时间: $(date)${NC}"
}

# 执行主函数
main "$@" 