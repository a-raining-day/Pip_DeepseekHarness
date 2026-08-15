"""全局配置常量：版本、URL、超时、重试等集中管理。"""

# ---------- 仓库与安装目录 ----------
GIT_REPO_URL = "https://github.com/deepseek-ai/deepseek-harness.git"
REPO_DIR_NAME = "deepseek-harness"
DEFAULT_INSTALL_DIR = r"C:/Deepseek-Harness"

# ---------- 目标地址与启动器 ----------
GOAL_URL = "http://127.0.0.1:3080"
GOAL_FILENAME = "goal_address.txt"
BAT_FILENAME = "Harness.bat"
SERVICE_WAIT_TIMEOUT = 120  # Harness.bat 等待服务就绪的秒数

# ---------- Git ----------
GIT_VERSION = "2.46.0"
GIT_INSTALLER_FILENAME = f"Git-{GIT_VERSION}-64-bit.exe"
GIT_INSTALLER_URL = (
    "https://github.com/git-for-windows/git/releases/download/"
    f"v{GIT_VERSION}.windows.1/{GIT_INSTALLER_FILENAME}"
)

# ---------- Node.js ----------
NODE_FALLBACK_VERSION = "22.17.0"  # 在线获取最新 LTS 失败时的兜底版本
NODE_LTS_INDEX_URL = "https://nodejs.org/dist/index.json"
NODE_MSI_URL_TEMPLATE = "https://nodejs.org/dist/v{version}/node-v{version}-x64.msi"

# ---------- npm 镜像 ----------
NPM_REGISTRY = "https://registry.npmmirror.com/"

# ---------- 下载与命令超时 ----------
DOWNLOAD_RETRIES = 3
DOWNLOAD_RETRY_DELAY = 3        # 秒
DOWNLOAD_TIMEOUT = 60           # 秒
DOWNLOAD_CHUNK_SIZE = 64 * 1024
INSTALLER_TIMEOUT = 300         # 秒（静默安装器）
COMMAND_VERSION_TIMEOUT = 10    # 秒（--version 探测）
NODE_INDEX_TIMEOUT = 20         # 秒（LTS 索引查询）
