### 在 Jupyter Notebook 中使用任何一个 Conda 环境

这个流程的核心是：**在 Conda 环境中安装 `ipykernel`，然后将其注册为 Jupyter 内核。**

#### 步骤一：创建或激活目标 Conda 环境

首先，您需要在终端中准备好您想要在 Notebook 中使用的环境。

1. **打开您的终端**。

2. **激活**您要使用的 Conda 环境。

   - 如果环境已存在（例如 `flyai_agent_in_action`）：

     ```Bash
     conda activate flyai_agent_in_action
     ```

   - **（可选）** 如果您需要创建一个全新的环境：

     ```Bash
     conda create -n flyai_agent_in_action python=3.12.11 -y
     conda activate flyai_agent_in_action
     ```

#### 步骤二：安装 Jupyter 内核桥梁 (`ipykernel`)

Jupyter Notebook 需要一个特殊的包来与您的 Conda 环境进行通信，这个包就是 `ipykernel`。

在您**已激活**的 Conda 环境（例如 `(flyai_agent_in_action)`）中执行以下命令：

```Bash
conda install ipykernel -y
# 或者使用 pip 安装：
# pip install ipykernel
# pip install ipykernel -i https://pypi.tuna.tsinghua.edu.cn/simple
```

*提示：使用 `conda` 安装通常更好，因为它能更好地管理环境依赖。*

#### 步骤三：将环境注册为 Jupyter 内核

现在，您需要告诉 Jupyter 应用程序：“嗨，我这里有一个新的 Python 环境，请把它添加到你的菜单里。”

在**已激活**的环境中执行注册命令：

```Bash
python -m ipykernel install --user --name=flyai_agent_in_action --display-name="Python (flyai_agent_in_action)"
```

| 参数              | 解释 (初学者友好)                                            | 建议值                   |
| ----------------- | ------------------------------------------------------------ | ------------------------ |
| `--user`          | 允许您在自己的用户权限下安装，不需要管理员权限。             | 保持不变                 |
| `--name=`         | 这是 Jupyter **系统内部**用来识别内核的名字，通常使用 Conda **环境名**。 | `flyai_agent_in_action`  |
| `--display-name=` | 这是您在 Jupyter **菜单上看到**的名字，设置为容易理解的名称。 | `"Python (FlyAI Agent)"` |

执行成功后，您会看到类似这样的提示：

```
Installed kernel 'flyai_agent_in_action' in C:\Users\YourUser\AppData\Roaming\jupyter\kernels\flyai_agent_in_action
```

#### 步骤四：在 Jupyter Notebook 中切换内核

最后一步，打开您的 Notebook，开始使用新环境。

1. **启动 Jupyter Notebook 或 JupyterLab**。
   - 如果您是从终端启动的，请先退出 Conda 环境（`conda deactivate`），然后用启动 Jupyter 的主环境来启动它：`jupyter notebook`。
2. **方法 A：创建新文件时**
   - 在 Jupyter 的主界面，点击右上角的 **New (新建)** 按钮。
   - 在下拉列表中，您将看到 **`Python (FlyAI Agent)`** 这个新的选项。点击它即可开始使用新环境的 Notebook。
3. **方法 B：更改现有文件的内核**
   - 打开一个已有的 `.ipynb` 文件。
   - 在顶部菜单栏，选择 **Kernel (内核)** → **Change kernel (更改内核)**。
   - 选择 **`Python (FlyAI Agent)`** 完成切换。

您现在已成功设置并切换到您的 Conda 环境！您可以随意在这个 Notebook 中安装或卸载软件包，而不会影响到其他环境或您的基础环境。

#### 步骤五：在 Jupyter Notebook 中切换内核

在 Jupyter Notebook 或 JupyterLab 的代码单元格顶部，使用以下命令：

```Python
%%script bash
# 初始化 conda
eval "$(conda shell.bash hook)"
```

## 总结



| 命令/结构                              | 为什么需要                                                   |
| -------------------------------------- | ------------------------------------------------------------ |
| `%%script bash`                        | 确保整个单元格作为一个**完整的 `bash` 脚本**运行，而不是多个独立的命令。 |
| `eval "$(conda shell.bash hook)"`      | 这是在非交互式 Shell 环境（如 Jupyter 单元格）中**启用 `conda activate` 命令**的官方且唯一的正确方法。它将 Conda 的功能加载到当前的 `bash` 会话中。 |
| `conda activate flyai_agent_in_action` | 只有在 Conda Hook 加载成功后，这条命令才能找到您的环境并进行切换。 |

**什么是 Hook？** `conda shell.bash hook` 是一个 Conda 脚本，它会输出一系列环境变量设置和函数定义（即所谓的 "hook" 代码），这些代码允许 `conda` 命令（尤其是 `conda activate`）在当前 Shell 中正常工作。

**`eval` 的作用：** `eval` 命令的作用是**在当前运行的 Shell 中执行**其后面的字符串（即 Conda Hook 代码）。

- 通过 `eval "$(conda shell.bash hook)"`，您实际上是在**单元格的 bash 环境中**加载了 Conda 的全部功能和路径配置。
- 一旦 Hook 加载成功，后续的 `conda activate flyai_agent_in_action` 命令就能找到并正确修改当前 `bash` 进程的环境变量，从而实现环境切换。

##### Magic 命令格式

Jupyter/IPython 只定义了两种 Magic 命令格式：

1. **`%` (单百分号)：** **行 Magic 命令** (Line Magic)，只对当前一行代码生效。
2. **`%%` (双百分号)：** **单元格 Magic 命令** (Cell Magic)，对整个代码单元格生效，且必须位于单元格的第一行。

------

例如：

- **`%run script.py`**: 运行一个外部 Python 脚本。
- **`%matplotlib inline`**: 在 Notebook 中显示 Matplotlib 图表。
- **`%%html`**: 将整个单元格内容渲染为 HTML 代码。
- **`%%bash` / `%%script bash`**: 将整个单元格内容作为 Bash 脚本执行。

```bash
1、准备环境我用的命令是：
conda create -n flyai_agent_in_action python=3.12.11 -y
conda activate flyai_agent_in_action
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

2 notebook右上角选择jupyter内核：
启动环境：请先激活预设的 Conda 环境。
配置 Jupyter 内核（首次使用）：
# 激活环境 
conda activate flyai_agent_in_action
# 安装内核
pip install ipykernel -i https://pypi.tuna.tsinghua.edu.cn/simple
# 注册内核
kernel_install --name flyai_agent_in_action --display-name "python(flyai_agent_in_action)"
运行实验：刷新 Jupyter Notebook 界面，选择 "python(flyai_agent_in_action)" 内核
您准备了一个新环境后，如果要在notebook里 使用，需要执行者这段，只需要执行一次就可以：先激活环境，然后安装ipykernel，最后注册内核。刷新页面后，右上角就有了。
```

