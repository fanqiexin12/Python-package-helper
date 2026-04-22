# Python离线包管理工具

为离线环境下载和管理Python包的Web工具，特别适用于无法访问外网的办公环境。

## 功能特点

- 🌐 **跨平台支持**: Windows、Linux、macOS
- 🐍 **多Python版本**: 支持 Python 3.8 - 3.12
- 📦 **包管理**: 搜索和添加任意PyPI包
- ⚡ **快速添加**: 内置常用科学计算包快捷按钮
- 📥 **命令生成**: 自动生成pip下载和安装命令
- 🔗 **链接生成**: 直接生成PyPI下载链接

## 使用方法

### 方式一：直接使用（推荐）

1. 双击打开 `Python离线包管理工具.html` 文件
2. 在浏览器中完成所有操作

### 方式二：Flask服务器运行

```bash
# 安装依赖
pip install flask requests

# 启动服务器
python app.py

# 访问 http://localhost:5000
```

## 操作步骤

### 第一步：选择目标环境

在界面中选择你的离线电脑的：
- **操作系统**: Windows / Linux / macOS
- **Python版本**: 3.8 / 3.9 / 3.10 / 3.11 / 3.12

### 第二步：添加需要下载的包

- 在搜索框中输入包名进行搜索
- 或点击"快速添加"按钮添加常用包

常用包推荐：
- NumPy - 数值计算
- Pandas - 数据分析
- SciPy - 科学计算
- Scikit-learn - 机器学习
- Matplotlib - 数据可视化
- Requests - HTTP请求
- Flask / Django - Web框架

### 第三步：获取下载命令

点击"生成命令"按钮获取：

**下载命令**（在联网电脑执行）：
```bash
pip download numpy pandas --platform win_amd64 --python-version 311 --only-binary=:all:
```

**离线安装命令**（在离线电脑执行，确保终端已进入whl文件所在目录）：
```bash
pip install --no-index --find-links=. numpy pandas
```

或点击"生成下载链接"获取PyPI直链，直接下载.whl文件。

## 完整工作流

### 1. 在联网电脑上

```bash
# 创建下载目录
mkdir wheels && cd wheels

# 下载所有需要的包（单个命令）
pip download numpy pandas matplotlib scikit-learn scipy --platform win_amd64 --python-version 311 --only-binary=:all:

# 或者复制生成命令直接执行
```

### 2. 传输文件

将下载好的所有 `.whl` 文件复制到U盘中，带到离线电脑上。

### 3. 在离线电脑上

```bash
# 打开终端（cmd 或 PowerShell），进入你存放 .whl 文件的目录
# 比如你把文件放在了桌面的 pyp\11 文件夹下：
cd C:\Users\ASUS\Desktop\pyp\11

# 安装所有包（注意 find-links 后面的 . 代表当前目录）
pip install --no-index --find-links=. numpy pandas matplotlib scikit-learn scipy
```

## 文件说明

```
Python package helper/
├── Python离线包管理工具.html  # 独立HTML版本，直接打开即可使用
├── app.py                      # Flask Web应用（需要网络）
├── templates/
│   └── index.html             # Flask模板
└── README.md                  # 本文档
```

## 注意事项

1. **依赖包**: 某些包（如scikit-learn）依赖其他包，下载时要确保所有依赖都被下载
2. **平台匹配**: 确保选择的操作系统和Python版本与目标离线环境完全匹配
3. **架构匹配**: 注意区分x86_64和ARM64架构
4. **离线使用**: HTML文件本身可以在离线环境打开使用，但生成下载链接需要网络

## 技术栈

- 前端: HTML5 + CSS3 + JavaScript（原生，无依赖）
- 后端: Flask + Python（可选）
- API: PyPI JSON API

## License

MIT License
