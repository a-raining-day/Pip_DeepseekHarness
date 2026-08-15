"""生成 Windows 启动器 Harness.bat（模板填充 + 落盘）。"""

from pathlib import Path
from typing import Union

from . import config

# 使用 str.format 填充；raw 字符串防止 \n、\p 等被当作转义序列。
BAT_TEMPLATE = r"""@echo off
rem deepseek-harness 启动器（由 Harness 安装器自动生成，请勿直接编辑）
rem 目标地址记录在 {goal_file}，如需修改请编辑该文件。
chcp 936 >nul
setlocal enabledelayedexpansion

:: ---------- 1. 定位 pnpm ----------
set "PNPM_CMD="
where pnpm >nul 2>nul
if not errorlevel 1 set "PNPM_CMD=pnpm"
if not defined PNPM_CMD (
    echo [INFO] PATH 中未找到 pnpm，正在搜索常见安装位置...
    for %%D in ("%LOCALAPPDATA%\pnpm" "%APPDATA%\npm" "%ProgramFiles%\nodejs" "%ProgramFiles(x86)%\nodejs") do (
        if exist "%%~D\pnpm.cmd" set "PNPM_CMD=%%~D\pnpm.cmd"
        if exist "%%~D\pnpm.exe" set "PNPM_CMD=%%~D\pnpm.exe"
    )
)
if not defined PNPM_CMD (
    echo [ERROR] 未找到 pnpm。请先执行: npm install -g pnpm
    pause
    exit /b 1
)
echo [INFO] 使用 pnpm: %PNPM_CMD%

:: ---------- 2. 读取目标地址 ----------
set "GOAL_URL={default_url}"
if exist "{goal_file}" set /p GOAL_URL=<"{goal_file}"
echo [INFO] 目标地址: %GOAL_URL%

:: ---------- 3. 进入项目目录 ----------
cd /d "{harness_dir}" || (
    echo [ERROR] 无法进入目录: {harness_dir}
    pause
    exit /b 1
)

:: ---------- 4. 后台启动服务 ----------
echo [INFO] 正在启动 pnpm dsh web ...
if exist output.txt del output.txt
start /b cmd /c ""%PNPM_CMD%" dsh web > output.txt 2>&1"

:: ---------- 5. 等待服务就绪 ----------
echo [INFO] 等待服务就绪（最多 {wait_timeout} 秒）...
set /a WAIT_TRIES=0
:wait_loop
set /p "=." <nul
timeout /t 1 /nobreak >nul
findstr /C:"dsh web: %GOAL_URL%" output.txt >nul 2>nul
if not errorlevel 1 goto service_ready
set /a WAIT_TRIES+=1
if !WAIT_TRIES! lss {wait_timeout} goto wait_loop

echo.
echo [ERROR] 等待超时（{wait_timeout} 秒），服务可能未启动成功，请查看 output.txt。
del output.txt 2>nul
pause
exit /b 1

:service_ready
echo.
echo [OK] 服务已就绪，正在打开浏览器...
start "" "%GOAL_URL%"

:: ---------- 6. 手动退出 ----------
echo.
echo 服务正在运行。关闭本窗口即可停止服务。
pause >nul

del output.txt 2>nul
exit /b 0
"""


def build_bat_content(
    harness_dir: Union[str, Path],
    goal_file: Union[str, Path],
    default_url: str = config.GOAL_URL,
    wait_timeout: int = config.SERVICE_WAIT_TIMEOUT,
) -> str:
    """按模板生成 Harness.bat 内容。"""
    return BAT_TEMPLATE.format(
        harness_dir=str(harness_dir),
        goal_file=str(goal_file),
        default_url=default_url,
        wait_timeout=wait_timeout,
    )


def write_launcher(path: Union[str, Path], content: str) -> Path:
    """以 ANSI(mbcs) 编码写启动器，配合 chcp 936 避免中文乱码。"""
    path = Path(path)
    try:
        path.write_text(content, encoding="mbcs")
    except LookupError:  # 非 Windows 平台无 mbcs 编码
        path.write_text(content, encoding="utf-8")
    return path
