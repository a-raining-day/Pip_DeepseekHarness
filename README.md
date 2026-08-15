# HarnessPiP

deepseek-harness Windows 一键安装器：自动准备 Git / Node.js 环境，克隆仓库，安装 pnpm 依赖并构建，最后在桌面生成 `Harness.bat` 启动器。

## 项目结构

```
HarnessPiP/
├── Harness.py          # 薄入口（PyInstaller 打包入口）
├── Harness.spec        # PyInstaller 打包配置
├── requirements.txt    # 打包依赖
├── harness/            # 核心包
│   ├── config.py       # 集中配置：版本、URL、超时、重试
│   ├── errors.py       # 异常体系：HarnessError 及子类
│   ├── console.py      # 统一控制台输出（级别/步骤/进度条）
│   ├── utils.py        # 权限、PATH 管理、命令探测与流式执行、带重试下载、桌面路径
│   ├── environment.py  # Git / Node.js 检测与静默安装
│   ├── installer.py    # 安装流程：克隆 -> pnpm -> 依赖 -> 构建 -> 启动器
│   ├── launcher.py     # Harness.bat 模板生成与落盘
│   └── cli.py          # 流程编排与异常兜底
└── tests/              # 单元测试（unittest）
```

## 开发与构建

```powershell
# 创建虚拟环境并安装依赖
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# 直接运行
.\.venv\Scripts\python Harness.py

# 单元测试
.\.venv\Scripts\python -m unittest discover -s tests -v

# 打包（产物在 dist/Harness.exe）
.\.venv\Scripts\pyinstaller --noconfirm --clean Harness.spec
```

## 行为说明

- Git / Node.js 缺失时自动静默安装（需要管理员权限，会触发 UAC 提权并重启本程序）。
- pnpm 已存在则跳过全局安装，否则通过 npm 全局安装（使用淘宝镜像源）。
- 依赖安装与构建均通过 `pnpm_config_registry` 环境变量指定淘宝镜像源。
- 启动器 `Harness.bat` 从 `goal_address.txt` 读取目标地址（默认 `http://127.0.0.1:3080`），等待服务就绪最多 120 秒后自动打开浏览器，超时则报错退出。
- 构建产物（`build/`、`dist/`、`*.zip`）与虚拟环境已加入 `.gitignore`，不再纳入版本控制。
