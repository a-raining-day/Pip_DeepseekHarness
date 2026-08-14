import os
import sys
import subprocess
from pathlib import Path

# 配置信息
DEFAULT_DIR = r"C:/Deepseek-Harness"
GIT_REPO = "https://github.com/deepseek-ai/deepseek-harness.git"
GOAL_URL = "http://127.0.0.1:3080"
BAT_FILENAME = "Harness.bat"
DESKTOP_PATH = Path(os.path.expanduser("~/Desktop"))

# 提示信息
PREREQUISITES = """
请确保已实现以下要求：
  - Node.js (下载: https://nodejs.org/zh-cn/download)
  - Git可访问 (https://github.com/deepseek-ai/deepseek-harness)
  - 网络梯子（推荐 Steam++，下载: https://steampp.net/）
按任意键继续...
"""

def print_step(msg):
    print(f"\n[步骤] {msg}")

def run_cmd(cmd, cwd=None, env=None, check=True):
    """执行命令并实时打印输出（stdout 和 stderr 同时显示）"""
    print(f"> {cmd}")
    # 使用 Popen，将 stdout 和 stderr 合并到管道，逐行输出
    process = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # 合并错误到标准输出
        text=True,
        bufsize=1,                 # 行缓冲
        universal_newlines=True,
        errors="replace",
        encoding="utf-8",
    )
    # 逐行读取并打印
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if check and process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)
    return process

def main():
    # 0. 前置依赖提示
    input(PREREQUISITES + "按 Enter 继续...")

    # 1. 询问存放目录
    user_dir = input(f"请输入安装目录（默认 {DEFAULT_DIR}，直接回车使用默认）: ").strip()
    if not user_dir:
        user_dir = DEFAULT_DIR
    base_path = Path(user_dir)
    harness_path = Path(os.path.join(base_path, "deepseek-harness"))

    # 2. 创建文件夹
    base_path.mkdir(parents=True, exist_ok=True)

    # 3. 进入目录并执行 git clone
    os.chdir(base_path)
    if harness_path.exists():
        print(f"目录 {harness_path} 已存在，跳过克隆，直接进入。")
    else:
        print_step("克隆 deepseek-harness 仓库")
        run_cmd(f"git clone {GIT_REPO}")

    # 切换到项目目录
    os.chdir(harness_path)

    # 4. 安装 pnpm（全局）
    print_step("安装 pnpm（全局）")
    run_cmd("npm install -g pnpm")

    # 5. 设置淘宝镜像源（通过环境变量）
    print_step("设置 pnpm 使用淘宝镜像源")
    env = os.environ.copy()
    env["pnpm_config_registry"] = "https://registry.npmmirror.com/"

    # 6. pnpm install
    print_step("安装项目依赖（pnpm install）")
    run_cmd("pnpm install", env=env)

    # 7. pnpm run build
    print_step("构建项目（pnpm run build）")
    run_cmd("pnpm run build", env=env)

    # 8. 创建 goal_address.txt
    print_step("创建目标网址记录文件")
    goal_file = base_path / "goal_address.txt"
    goal_file.write_text(GOAL_URL, encoding="utf-8")
    print(f"已创建 {goal_file}，内容：{GOAL_URL}")

    # 9. 在桌面创建 Harness.bat
    print_step("在桌面生成启动批处理文件")
    bat_content = f"""@echo off
rem 默认地址记录在 {goal_file}，若需修改请在 deepseek-harness 内部调整后同步修改该文件。
chcp 936 >nul
setlocal enabledelayedexpansion

:: ---------- 1. Ensure pnpm is available ----------
where pnpm >nul 2>nul
if errorlevel 1 (
    echo pnpm not found, trying common locations...
    if exist "%LOCALAPPDATA%\\pnpm\\pnpm.exe" (
        set "PATH=%LOCALAPPDATA%\\pnpm;%PATH%"
        echo Added %LOCALAPPDATA%\\pnpm
    ) else if exist "%ProgramFiles%\\nodejs\\pnpm.cmd" (
        set "PATH=%ProgramFiles%\\nodejs;%PATH%"
        echo Added %ProgramFiles%\\nodejs
    ) else (
        echo ERROR: pnpm not found. Please install with "npm install -g pnpm".
        pause
        exit /b 1
    )
)

where pnpm >nul 2>nul
if errorlevel 1 (
    echo ERROR: Still cannot find pnpm. Check installation.
    pause
    exit /b 1
)

:: ---------- 2. Change to target directory ----------
cd /d "{harness_path}" || (
    echo ERROR: Cannot enter directory {harness_path}
    pause
    exit /b 1
)

:: ---------- 3. Start service in background ----------
echo Starting pnpm dsh web ...
start /b pnpm dsh web > output.txt 2>&1

:: ---------- 4. Wait for target URL in output ----------
echo Waiting for service to be ready...
:loop
set /p "=." <nul
timeout /t 1 /nobreak >nul
type output.txt | findstr /C:"dsh web: {GOAL_URL}" >nul
if errorlevel 1 goto loop

echo.
echo Service is ready. Opening browser...
start "" "{GOAL_URL}"

:: ---------- 5. Manual exit ----------
echo.
echo Press any key to exit after you close the browser tab.
echo (To stop the service, just close this command window.)
pause >nul

del output.txt 2>nul
exit
"""
    bat_path = DESKTOP_PATH / BAT_FILENAME
    bat_path.write_text(bat_content, encoding="ansi")  # 使用 ANSI 编码避免中文乱码
    print(f"已创建 {bat_path}")

    # 10. 完成提示
    print("\n" + "="*50)
    print("安装完成！")
    print(f"启动文件已放置在桌面：{bat_path}")
    print("双击即可启动 deepseek-harness 服务并自动打开浏览器。")
    print("若需修改监听地址，请编辑 deepseek-harness 相关配置并同步更新 goal_address.txt。")
    print("="*50)
    input("按任意键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n发生错误：{e}")
        input("按任意键退出...")
        sys.exit(1)
