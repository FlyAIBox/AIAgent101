## Jupyter Lab 初学者指南

### 1. 简介

Jupyter Lab 是一个基于 Web 的交互式开发环境，适用于 Jupyter Notebook、代码和数据。它是 Jupyter Notebook 的下一代产品，提供了更强大、更灵活的用户界面，支持更多的工作流。

### 2. 安装与配置 Jupyter Lab

#### 2.1 安装 Jupyter Lab

建议使用 Miniconda 或 Anaconda 管理您的 Python 环境和 Jupyter Lab。

1. **安装 Miniconda/Anaconda**： 请根据您的操作系统从 Miniconda 或 Anaconda 官网下载并安装。

2. **使用 Conda 安装 Jupyter Lab**： 安装完 Miniconda 后，打开终端或 Anaconda Prompt，运行以下命令安装 Jupyter Lab：

   ```Bash
   conda install -c conda-forge jupyterlab 
   ```

   这条命令会从 `conda-forge` 频道安装最新版本的 Jupyter Lab。

#### 2.2 生成 Jupyter Lab 配置文件

为了更好地管理 Jupyter Lab，特别是当您需要在后台运行或进行特定配置时，生成配置文件是最佳实践 。

1. **生成默认配置文件**： 在终端中运行以下命令生成 Jupyter Lab 的默认配置文件：

   ```Bash
   jupyter lab --generate-config 
   ```

   成功执行后，您会看到类似如下的输出信息，其中包含了配置文件的路径：

   ```Bash
   Writing default config to: /root/.jupyter/jupyter_lab_config.py 
   ```

   这个文件通常位于您的用户主目录下的 `.jupyter` 文件夹中。

#### 2.3 修改 Jupyter Lab 配置文件

打开上一步生成的 `jupyter_lab_config.py` 文件（例如，`/root/.jupyter/jupyter_lab_config.py`），根据需求修改以下常用配置项：

- **允许 Root 用户启动**： 如果您需要在 `root` 用户下运行 Jupyter Lab（不推荐在生产环境中使用 `root` 用户运行服务），请将 `c.ServerApp.allow_root` 设置为 `True`。

  ```Python
  c.ServerApp.allow_root = True 
  ```

- **设置工作目录**： `c.ServerApp.root_dir` 用于指定 Jupyter Lab 启动后的默认工作目录。您可以将其设置为您存放 Notebook 和代码的目录。

  ```Python
  # 例如，设置为 /root/AI-Box/code
  c.ServerApp.root_dir = '/root/AI-Box/code' 
  ```

- **修改默认端口**： 默认情况下，Jupyter Lab 运行在 `8888` 端口。为了避免端口冲突或增强安全性，您可以修改默认端口。

  ```Python
  c.ServerApp.port = 8000 # 例如，修改为 8000 端口 
  ```

- **设置监听 IP 地址**： `c.ServerApp.ip` 设置 Jupyter Lab 监听的 IP 地址。设置为 `'0.0.0.0'` 允许从任何 IP 地址访问（慎用，确保网络安全）。

  ```Python
  c.ServerApp.ip = '0.0.0.0' # 允许从任何 IP 访问 
  ```

- **设置访问 Token**： `c.ServerApp.token` 用于设置访问 Jupyter Lab 的令牌（密码）。在生产环境中强烈建议设置一个强密码。如果您在本地且确保安全，也可以选择关闭密码（不推荐）。

  ```Python
  c.ServerApp.token = 'your_secure_token' # 替换为您的安全令牌
  # 如果要关闭密码（不推荐，仅限本地安全环境）
  # c.ServerApp.token = '' 
  ```

- **禁用浏览器自动打开**： `c.ServerApp.open_browser = False` 可以防止 Jupyter Lab 启动时自动打开浏览器，这在服务器环境中非常有用。

  ```Python
  c.ServerApp.open_browser = False 
  ```

### 3. 启动 Jupyter Lab

#### 3.1 后台启动 Jupyter Lab

在服务器或需要长时间运行 Jupyter Lab 的场景中，推荐使用 

`nohup` 命令使其在后台常驻运行 。

```Bash
nohup jupyter lab & 
```

这条命令会将 Jupyter Lab 的输出日志保存到当前目录的 `nohup.out` 文件中 。

#### 3.2 访问 Jupyter Lab

启动后，您可以通过浏览器访问 Jupyter Lab。如果您的 Jupyter Lab 运行在本地，通常地址是 `http://localhost:8888` (如果修改了端口，请使用您设置的端口，例如 `http://localhost:8000`)。如果运行在远程服务器上，请使用服务器的 IP 地址或域名。

### 4. 设置 Jupyter Lab 开机自启 (Systemd)

对于使用 `systemd` 作为 `init` 系统的 Linux 发行版（如 Ubuntu, Fedora, CentOS, Debian 等），可以通过创建 `systemd` 服务单元文件实现 Jupyter Lab 的开机自启 。

#### 4.1 步骤 1: 创建 Jupyter Lab 服务单元文件

使用文本编辑器（如 `nano` 或 `vim`）在 `/etc/systemd/system/` 目录下创建 `jupyterlab.service` 文件。您需要 `sudo` 权限 。

```Bash
sudo vim /etc/systemd/system/jupyterlab.service 
```

#### 4.2 步骤 2: 编辑服务单元文件

将以下内容粘贴到 `jupyterlab.service` 文件中，并根据您的实际情况修改配置项 ：

```Bash
[Unit]
Description=JupyterLab
After=network.target

[Service]
Type=simple
# 设置环境变量 (可选)
Environment=OPENAI_BASE_URL=https://vip.apiyi.com/v1
Environment=OPENAI_API_KEY=sk-paSHgQoVeKag1rou9d81Fa2f534940C1Ba394f02C45aF3D2

# 激活 conda 环境并启动 jupyterlab
ExecStart=/bin/ -c "source /root/miniconda3/bin/activate langchain && exec jupyter-lab --config=/root/.jupyter/jupyter_lab_config.py --no-browser"
User=root
Group=root
# Jupyter Lab 启动时的工作目录
WorkingDirectory=/root/AI-BOX/code
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**配置项说明 (重要)**:

- `Description=Jupyter Lab Server`: 服务的描述信息，可自定义 。
- `After=network.target`: 表示该服务在网络服务启动后启动 。
- `Type=simple`: 服务类型为简单服务 。
- `WorkingDirectory=/root/AI-BOX/code`: **工作目录**。Jupyter Lab 启动后的默认工作目录。请根据您的实际路径修改 。
- `ExecStart=/bin/ -c "source /root/miniconda3/bin/activate langchain && exec jupyter-lab --config=/root/.jupyter/jupyter_lab_config.py --no-browser"`: **Jupyter Lab 启动命令**。
  - `source /root/miniconda3/bin/activate langchain`: 激活您的 Conda 环境。请将 `/root/miniconda3/bin/activate` 替换为您 Miniconda 安装路径下的 `activate` 脚本路径，将 `langchain` 替换为您的 Conda 环境名称 。
  - `exec jupyter-lab --config=/root/.jupyter/jupyter_lab_config.py --no-browser`: 启动 Jupyter Lab。
    - `--config=/root/.jupyter/jupyter_lab_config.py`: 指定您自定义的配置文件路径。
    - `--no-browser`: 启动时不会自动打开浏览器 。
    - `--port=8888`: (此文档中未明确给出，但常见配置) 可以添加此参数来指定端口，例如 `--port=8000`。请确保端口未被占用 。
- `User=root` 和 `Group=root`: 指定运行服务的用户和组。如果您的 Jupyter Lab 不以 `root` 用户运行，请修改为实际用户和组。
- `Restart=on-failure`: 如果 Jupyter Lab 服务意外失败退出，`systemd` 会自动尝试重启服务 。
- `RestartSec=10`: 服务重启前等待 10 秒 。
- `[Install] WantedBy=multi-user.target`: 表示该服务在多用户模式下启动 。

#### 4.3 步骤 3: 保存并退出编辑器

- **Nano**: 按 `Ctrl + X`，输入 `y` 确认保存，按 `Enter` 键退出 。
- **Vim**: 按 `Esc` 键，输入 `:wq` 并按 `Enter` 键保存并退出 。

#### 4.4 步骤 4: 启用并启动 Jupyter Lab 服务

在终端中执行以下命令来启用并立即启动 Jupyter Lab 服务:

```Bash
sudo systemctl enable jupyterlab.service [cite: 42, 43]
sudo systemctl start jupyterlab.service [cite: 42, 44]
```

#### 4.5 步骤 5: 检查服务状态 (可选)

您可以通过以下命令检查 Jupyter Lab 服务的运行状态:

```Bash
sudo systemctl status jupyterlab.service 
```

如果服务成功启动，您应该看到类似 `active (running)` 的状态信息 。

### 5. 将 Conda 环境添加到 Jupyter Lab 内核列表

如果您的 Conda 环境没有出现在 Jupyter Lab 的内核列表中，您需要手动将其添加 。这通常涉及在您的 Conda 环境中安装 

`ipykernel` 包并将其注册为 Jupyter 内核 。

1. **激活您的 Conda 环境**：

   ```Bash
   conda activate <您的conda环境名称> 
   ```

   例如，如果您的 Conda 环境名称是 `myenv`，则命令为 `conda activate myenv` 。

   

2. **在激活的环境中安装 `ipykernel` 包**：

   ```Bash
   conda install ipykernel 
   ```

3. **将当前 Conda 环境注册为 Jupyter 内核**：

   ```Bash
   python -m ipykernel install --user --name=<内核显示名称> --display-name="<友好的内核显示名称>" 
   ```

   - `<内核显示名称>`: 这是内核的内部名称，用于 Jupyter 识别。例如，您可以设置为 `myenv-kernel` 。
   - `<友好的内核显示名称>`: 这是在 Jupyter Lab 内核列表中显示的名称，更易于理解。例如，您可以设置为 `"Python (myenv)"` 。

   **示例**：

   ```Bash
   python -m ipykernel install --user --name langchain --display-name "Python (langchain)" 
   ```

4. **重启 Jupyter Lab 并重新检查内核列表**：完成上述步骤后，重启 Jupyter Lab。再次打开 "Kernel" -> "Change Kernel" 菜单，您应该能看到新添加的内核 (例如 "Python (langchain)") 。

### 6. Jupyter Lab 常用快捷键与操作

Jupyter Lab 提供了丰富的快捷键和操作，可以大大提高您的工作效率。以下是一些常用的：

#### 6.1 通用快捷键

- **Ctrl/Cmd + Shift + C**: 打开命令面板 (Command Palette)，可以搜索和执行各种操作。
- **Ctrl/Cmd + Shift + P**: 与命令面板相同。
- **Ctrl/Cmd + S**: 保存当前文件。
- **Ctrl/Cmd + B**: 切换左侧文件浏览器面板的可见性。
- **Ctrl/Cmd + M**: 切换菜单栏可见性。
- **Ctrl/Cmd + J**: 打开/关闭底部面板（如终端、输出、Console）。

#### 6.2 Notebook 快捷键 (命令模式 - 按 `Esc` 进入)

在 Notebook 中，有两种模式：编辑模式 (绿色边框) 和命令模式 (蓝色边框)。

- **A**: 在当前单元格上方插入新单元格。
- **B**: 在当前单元格下方插入新单元格。
- **X**: 剪切当前单元格。
- **C**: 复制当前单元格。
- **V**: 粘贴单元格（在当前单元格下方）。
- **D, D (按两次 D)**: 删除当前单元格。
- **Z**: 撤销删除单元格。
- **Y**: 将当前单元格类型更改为代码 (Code)。
- **M**: 将当前单元格类型更改为 Markdown。
- **R**: 将当前单元格类型更改为 Raw NBConvert。
- **Enter**: 进入编辑模式。
- **Shift + Enter**: 运行当前单元格并选中下一个。
- **Ctrl/Cmd + Enter**: 运行当前单元格。
- **Alt + Enter**: 运行当前单元格并在下方插入新单元格。
- **L**: 切换当前单元格行号的显示。
- **K**: 向上移动当前单元格。
- **J**: 向下移动当前单元格。
- **Shift + K/J**: 选中多个单元格。
- **Shift + L**: 合并选中的单元格。
- **H**: 显示所有快捷键帮助。

#### 6.3 Notebook 快捷键 (编辑模式 - 按 `Enter` 进入)

- **Tab**: 代码自动补全。
- **Shift + Tab**: 显示函数或方法的文档字符串（Docstring）。
- **Ctrl/Cmd + ]**: 增加缩进。
- **Ctrl/Cmd + [**: 减少缩进。
- **Ctrl/Cmd + Z**: 撤销。
- **Ctrl/Cmd + Y**: 重做。
- **Ctrl/Cmd + D**: 删除当前行。
- **Ctrl/Cmd + Up/Down**: 移动到单元格的开头/结尾。

#### 6.4 其他常用操作

- **文件浏览器**：
  - 拖放文件或文件夹进行上传。
  - 右键点击文件或文件夹进行复制、剪切、删除、重命名等操作。
- **终端**：在 Jupyter Lab 中打开终端，可以直接运行 shell 命令，方便进行文件操作、环境管理等。
- **代码控制台 (Console)**：可以打开一个独立的 Python 控制台，进行即时代码测试和调试。
- **Markdown 编辑器**：Jupyter Lab 内置了强大的 Markdown 编辑器，支持实时预览。
- **拖放和多标签页**：您可以将文件选项卡拖放到不同的区域，实现分屏显示，方便同时查看和编辑多个文件