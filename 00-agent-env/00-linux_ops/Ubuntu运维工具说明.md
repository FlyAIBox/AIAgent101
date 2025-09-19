# Ubuntu 运维工具说明

## 📋 工具概述

本项目为 Ubuntu 22.04.4 用户提供了一套完整的运维配置工具，包括详细的手册文档、自动化脚本和便捷的操作命令。

## 📚 文档资源

### 📖 主要文档
- **[Ubuntu22.04.4-运维配置手册.md](Ubuntu22.04.4-运维配置手册.md)** - 完整的配置手册，面向Linux初学者

### 🎯 文档特色
- 零基础友好，循序渐进
- 详细的操作步骤和命令
- 安全提示和最佳实践
- 实战导向的配置方案

## 🛠️ 自动化脚本

### 📦 快速配置脚本 (`scripts/ubuntu-quick-setup.sh`)
**功能**：自动化配置Ubuntu系统基础环境
- ✅ 系统更新和基础工具安装
- ✅ Git环境配置和SSH密钥生成  
- ✅ Docker容器化环境安装
- ✅ Node.js开发环境配置
- ✅ 系统时间、DNS和性能优化
- ✅ Python开发环境配置

**使用方法**：
```bash
# 交互式配置（推荐）
./scripts/ubuntu-quick-setup.sh

# 一键完整安装
./scripts/ubuntu-quick-setup.sh --full
```

### 🔍 系统检查脚本 (`scripts/system-check.sh`)
**功能**：全面检查系统配置状态和健康度
- 🔧 系统基本信息检查
- 💻 硬件资源评估
- 🌐 网络连接测试
- 📦 软件环境验证
- 🐳 容器环境检查
- ⚙️ 系统配置验证
- 📊 性能测试（可选）

**使用方法**：
```bash
./scripts/system-check.sh
```

## 🚀 便捷操作 (Makefile)

### 📋 可用命令
```bash
make help           # 显示帮助信息
make setup          # 交互式系统配置  
make setup-full     # 一键完整系统配置
make check          # 系统健康检查
make info           # 显示系统信息
make diagnose       # 快速诊断
make install-deps   # 安装基础依赖
make update-system  # 更新系统
make clean          # 清理临时文件
```

### 🎯 使用场景
- **新系统配置**：`make setup-full`
- **环境检查**：`make check`
- **快速诊断**：`make diagnose` 
- **系统维护**：`make update-system` + `make clean`

## 📋 配置清单

### 🔧 基础配置
- [x] SSH工具配置 (Xshell/Xftp推荐)
- [x] 静态IP地址配置 (Netplan)
- [x] root用户登录配置
- [x] 系统时间同步 (Chrony/NTP)
- [x] 命令行自动补全
- [x] DNS服务器配置

### 💾 系统优化  
- [x] 磁盘管理和LVM扩容
- [x] 系统性能优化
- [x] 文件描述符限制调整
- [x] 内核参数优化

### 🛠️ 开发环境
- [x] Git环境配置和SSH密钥
- [x] Docker容器化环境
- [x] Node.js开发环境 (NVM管理)
- [x] Python开发环境
- [x] 包管理器镜像源配置

### 🌐 网络配置
- [x] 网络代理配置 (v2rayA)
- [x] 防火墙配置
- [x] 网络连接诊断

### 📊 监控运维
- [x] 系统资源监控工具
- [x] 日志管理和轮转
- [x] 定期维护脚本
- [x] 备份策略配置

## ⚡ 快速开始

### 🚀 新用户推荐流程
1. **阅读文档**：浏览 `Ubuntu22.04.4-运维配置手册.md`
2. **快速配置**：运行 `make setup-full`
3. **环境检查**：运行 `make check` 验证配置
4. **个性化调整**：根据需要进行细节调整

### 🔧 维护用户推荐流程
1. **健康检查**：定期运行 `make check`
2. **系统更新**：定期运行 `make update-system`
3. **快速诊断**：遇到问题时运行 `make diagnose`
4. **清理维护**：定期运行 `make clean`

## 📞 技术支持

- **文档问题**：查阅详细手册或提交Issue
- **脚本问题**：检查执行权限和系统兼容性
- **配置问题**：参考手册中的故障排除章节

## 🤝 贡献指南

欢迎提交：
- 配置优化建议
- 新工具脚本
- 文档改进
- 问题反馈

---

*持续改进中，感谢您的使用和反馈！* 🙏 