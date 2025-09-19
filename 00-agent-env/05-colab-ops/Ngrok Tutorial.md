# 🌐 Ngrok 隧道服务详解

### 什么是 Ngrok？

Ngrok 是一个强大的内网穿透工具，可以将您在本地（或 Colab）运行的服务通过安全隧道暴露到公网上。在我们的项目中，Ngrok 用于将 Colab 中运行的 VLLM 服务暴露到公网，让您可以从任何地方访问您的大模型 API。

### 🎯 为什么需要 Ngrok？

**🔒 Colab 网络限制**
- Google Colab 默认不允许外部直接访问内部端口
- 本地服务（如 FastAPI）只能在 Colab 内部访问
- 需要隧道服务将内部端口暴露到公网

**🌍 远程访问需求**
- 让团队成员访问您的模型服务
- 在移动设备上测试 API
- 与外部应用程序集成
- 演示和分享您的项目

**⚡ 即时部署**
- 无需复杂的服务器配置
- 几秒钟内获得公网 URL
- 支持 HTTPS 加密传输

## 📝 Ngrok 注册使用完整流程

#### 第一步：注册 Ngrok 账户

1. **访问 Ngrok 官网**
   - 打开浏览器，访问 [ngrok.com](https://ngrok.com)
   - 点击右上角的 "Sign up" 按钮

2. **选择注册方式**
   ```bash
   方式一：邮箱注册
   - 输入邮箱地址
   - 设置密码（至少8位，包含字母和数字）
   - 点击 "Sign up"
   
   方式二：第三方登录
   - GitHub 账户登录
   - Google 账户登录(推荐)
   - Microsoft 账户登录
   ```

3. **验证邮箱**
   - 检查您的邮箱收件箱
   - 点击验证链接完成邮箱验证
   - 返回 Ngrok 网站登录

#### 第二步：获取 Authtoken

1. **登录 Ngrok Dashboard**
   - 使用注册的账户登录 [dashboard.ngrok.com](https://dashboard.ngrok.com)
   - 进入控制台主页

2. **获取 Authtoken**
   ```bash
   位置：Dashboard → Getting Started → Your Authtoken
   或者：Dashboard → Auth → Your Authtoken
   
   示例 Token：
   2abc123def456ghi789jkl012mno345_6pqrstu7vwxyz8ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk
   ```

3. **复制并保存 Token**
   
   - 点击 "Copy" 按钮复制完整的 authtoken
   - 将 token 保存到安全的地方（如密码管理器）
   - ⚠️ **重要**：不要将 token 分享给他人或提交到公共代码仓库

#### 第三步：在 Colab 中配置 Ngrok

1. **安装 pyngrok**
   ```bash
   # 安装 pyngrok 包
   !pip install pyngrok
   ```

2. **设置 Authtoken**
   ```bash
   from pyngrok import ngrok
   
   # 方法一：直接设置（适合临时使用）
   ngrok.set_auth_token("your_authtoken_here")
   
   # 方法二：使用环境变量（推荐）
   import os
   os.environ['NGROK_AUTHTOKEN'] = 'your_authtoken_here'
   ngrok.set_auth_token(os.environ['NGROK_AUTHTOKEN'])
   ```

3. **创建隧道**
   ```python
   # 创建 HTTP 隧道到端口 8000
   public_url = ngrok.connect(8000)
   print(f"🌐 公网访问地址: {public_url}")
   
   # 获取隧道信息
   tunnels = ngrok.get_tunnels()
   for tunnel in tunnels:
       print(f"隧道名称: {tunnel.name}")
       print(f"本地地址: {tunnel.config['addr']}")
       print(f"公网地址: {tunnel.public_url}")
   ```

#### 第四步：验证隧道连接

1. **检查隧道状态**
   ```python
   import requests
   import time
   
   def check_tunnel_status(public_url):
       try:
           # 检查健康端点
           health_url = f"{public_url}/health"
           response = requests.get(health_url, timeout=10)
           
           if response.status_code == 200:
               print(f"✅ 隧道连接成功！")
               print(f"🌐 API 基础地址: {public_url}")
               print(f"🔍 健康检查: {health_url}")
               print(f"📝 API 文档: {public_url}/docs")
               return True
           else:
               print(f"❌ 隧道连接失败，状态码: {response.status_code}")
               return False
               
       except requests.exceptions.RequestException as e:
           print(f"❌ 连接错误: {e}")
           return False
   
   # 等待服务启动
   time.sleep(5)
   check_tunnel_status(public_url)
   ```

2. **测试 API 调用**
   ```python
   def test_api_call(public_url):
       try:
           api_url = f"{public_url}/v1/chat/completions"
           
           payload = {
               "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
               "messages": [
                   {"role": "user", "content": "你好，请介绍一下你自己"}
               ],
               "max_tokens": 100,
               "temperature": 0.7
           }
           
           headers = {
               "Content-Type": "application/json"
           }
           
           response = requests.post(api_url, json=payload, headers=headers, timeout=30)
           
           if response.status_code == 200:
               result = response.json()
               print("✅ API 调用成功！")
               print(f"🤖 模型回复: {result['choices'][0]['message']['content']}")
           else:
               print(f"❌ API 调用失败，状态码: {response.status_code}")
               print(f"错误信息: {response.text}")
               
       except Exception as e:
           print(f"❌ API 测试错误: {e}")
   
   # 执行 API 测试
   test_api_call(public_url)
   ```

#### 第五步：Ngrok 管理和监控

1. **查看隧道状态**
   ```python
   # 获取所有活跃隧道
   tunnels = ngrok.get_tunnels()
   print(f"活跃隧道数量: {len(tunnels)}")
   
   for i, tunnel in enumerate(tunnels):
       print(f"\n隧道 {i+1}:")
       print(f"  名称: {tunnel.name}")
       print(f"  协议: {tunnel.proto}")
       print(f"  本地地址: {tunnel.config['addr']}")
       print(f"  公网地址: {tunnel.public_url}")
   ```

2. **访问 Ngrok Web 界面**
   ```python
   # Ngrok 提供本地 Web 界面用于监控
   print("🖥️  Ngrok Web 界面: http://127.0.0.1:4040")
   print("📊 在此界面可以查看:")
   print("   - 实时请求日志")
   print("   - 隧道状态和配置")
   print("   - 请求/响应详情")
   print("   - 性能统计信息")
   ```

3. **关闭隧道**
   ```python
   # 关闭特定隧道
   ngrok.disconnect(public_url)
   
   # 关闭所有隧道
   ngrok.kill()
   
   print("🔒 所有 Ngrok 隧道已关闭")
   ```

### 🔧 Ngrok 高级配置

#### 自定义域名（付费功能）

```python
# 使用自定义子域名（需要付费账户）
public_url = ngrok.connect(8000, subdomain="my-llm-api")
print(f"🌐 自定义域名: {public_url}")
```

#### 基本认证保护

```python
# 添加基本认证保护 API
public_url = ngrok.connect(8000, auth="username:password")
print(f"🔐 受保护的 API: {public_url}")
```

#### 区域选择

```python
# 选择 Ngrok 服务器区域（减少延迟）
public_url = ngrok.connect(8000, region="ap")  # 亚太地区
# 可选区域: us, eu, ap, au, sa, jp, in
```

### 💡 Ngrok 使用技巧和注意事项

#### ✅ 最佳实践

1. **安全性考虑**
   
   ```python
   # 使用环境变量存储敏感信息
   import os
   from google.colab import userdata
   
   # 在 Colab 中使用 Secrets 功能
   try:
       ngrok_token = userdata.get('NGROK_TOKEN')
       ngrok.set_auth_token(ngrok_token)
   except:
       print("请在 Colab Secrets 中设置 NGROK_TOKEN")
   ```
   
2. **错误处理**
   ```python
   def create_secure_tunnel(port, retries=3):
       for attempt in range(retries):
           try:
               public_url = ngrok.connect(port)
               print(f"✅ 隧道创建成功 (尝试 {attempt + 1}): {public_url}")
               return public_url
           except Exception as e:
               print(f"❌ 隧道创建失败 (尝试 {attempt + 1}): {e}")
               if attempt < retries - 1:
                   time.sleep(2)
               else:
                   raise e
   ```

3. **资源清理**
   ```python
   import atexit
   
   def cleanup_ngrok():
       """程序退出时自动清理 Ngrok 隧道"""
       try:
           ngrok.kill()
           print("🧹 Ngrok 隧道已清理")
       except:
           pass
   
   # 注册退出处理函数
   atexit.register(cleanup_ngrok)
   ```

#### ⚠️ 限制和注意事项

1. **免费账户限制**
   ```
   - 同时最多 1 个隧道
   - 每分钟最多 20 个连接
   - 隧道会在 8 小时后自动关闭
   - 随机生成的子域名
   ```

2. **付费升级选项**
   ```
   Personal Plan ($8/月):
   - 同时最多 3 个隧道
   - 自定义子域名
   - 更高的连接限制
   
   Pro Plan ($20/月):
   - 同时最多 10 个隧道
   - 自定义域名
   - IP 白名单
   - 密码保护
   ```

3. **性能考虑**
   ```
   - Ngrok 会增加一定的网络延迟
   - 大文件传输可能较慢
   - 建议仅用于开发和演示
   - 生产环境建议使用专业的云服务
   ```

### 📱 完整的 Ngrok 使用示例

```python
# 完整的 Ngrok 集成示例
import os
import time
import requests
from pyngrok import ngrok

class NgrokManager:
    def __init__(self, authtoken):
        self.authtoken = authtoken
        self.public_url = None
        self.setup_ngrok()
    
    def setup_ngrok(self):
        """设置 Ngrok 认证"""
        try:
            ngrok.set_auth_token(self.authtoken)
            print("✅ Ngrok 认证设置成功")
        except Exception as e:
            print(f"❌ Ngrok 认证失败: {e}")
            raise
    
    def create_tunnel(self, port, subdomain=None):
        """创建安全隧道"""
        try:
            if subdomain:
                self.public_url = ngrok.connect(port, subdomain=subdomain)
            else:
                self.public_url = ngrok.connect(port)
            
            print(f"🌐 隧道创建成功: {self.public_url}")
            return self.public_url
        except Exception as e:
            print(f"❌ 隧道创建失败: {e}")
            raise
    
    def wait_for_service(self, max_wait=60):
        """等待服务启动"""
        print("⏳ 等待服务启动...")
        
        for i in range(max_wait):
            try:
                response = requests.get(f"{self.public_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ 服务已启动！用时 {i+1} 秒")
                    return True
            except:
                time.sleep(1)
        
        print(f"❌ 服务启动超时（{max_wait} 秒）")
        return False
    
    def get_api_info(self):
        """获取 API 信息"""
        if not self.public_url:
            return None
        
        return {
            "base_url": self.public_url,
            "health_check": f"{self.public_url}/health",
            "api_docs": f"{self.public_url}/docs",
            "chat_endpoint": f"{self.public_url}/v1/chat/completions"
        }
    
    def cleanup(self):
        """清理隧道"""
        try:
            ngrok.kill()
            print("🧹 Ngrok 隧道已清理")
        except:
            pass

# 使用示例
if __name__ == "__main__":
    # 替换为您的实际 authtoken
    NGROK_TOKEN = "your_authtoken_here"
    
    # 创建 Ngrok 管理器
    ngrok_manager = NgrokManager(NGROK_TOKEN)
    
    # 创建隧道
    public_url = ngrok_manager.create_tunnel(8000)
    
    # 等待服务启动
    if ngrok_manager.wait_for_service():
        # 显示 API 信息
        api_info = ngrok_manager.get_api_info()
        print("\n🚀 API 服务信息:")
        for key, value in api_info.items():
            print(f"  {key}: {value}")
    
    # 程序结束时清理
    # ngrok_manager.cleanup()
```

