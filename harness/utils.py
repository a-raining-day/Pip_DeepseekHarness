"""系统级工具：管理员权限、PATH 管理、命令探测与执行、带重试下载、桌面路径。"""

import ctypes
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Iterable, List, Optional, Union

from . import config
from .console import info, newline, ok, progress, warn
from .errors import CommandError, DownloadError, PrerequisiteError

Command = Union[str, List[str]]

_CSIDL_DESKTOPDIRECTORY = 0x0010


# ---------- 管理员权限 ----------

def is_admin() -> bool:
    """当前进程是否具有管理员权限。"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    """通过 UAC 以管理员权限重启本程序；成功后退出当前进程。"""
    args = [os.path.abspath(sys.argv[0]), *sys.argv[1:]]
    params = subprocess.list2cmdline(args)
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    if result <= 32:
        raise PrerequisiteError(
            f"请求管理员权限失败（错误码 {result}）。\n"
            "请右键本程序，选择“以管理员身份运行”后重试。"
        )
    raise SystemExit(0)


# ---------- PATH 管理 ----------

def _read_registry_path(hive) -> str:
    """读取注册表中某 hive 下的 PATH 环境变量。"""
    import winreg
    try:
        sub_key = (
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
            if hive == winreg.HKEY_LOCAL_MACHINE
            else "Environment"
        )
        with winreg.OpenKey(hive, sub_key) as key:
            value, _ = winreg.QueryValueEx(key, "Path")
        return str(value) if value else ""
    except OSError:
        return ""


def refresh_path_from_registry() -> None:
    """从注册表重新读取系统/用户 PATH 并更新当前进程，避免新装软件不可见。"""
    import winreg
    machine = _read_registry_path(winreg.HKEY_LOCAL_MACHINE)
    user = _read_registry_path(winreg.HKEY_CURRENT_USER)
    current = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join(filter(None, [machine, user, current]))


def add_to_path(directory: Path) -> None:
    """将目录插入当前进程 PATH 头部（仅本次会话，不持久化）。"""
    entry = str(directory)
    current = os.environ.get("PATH", "")
    if not any(os.path.normcase(p) == os.path.normcase(entry)
               for p in current.split(os.pathsep)):
        os.environ["PATH"] = entry + os.pathsep + current


# ---------- 命令探测与执行 ----------

def find_executable(name: str, extra_dirs: Iterable[str] = ()) -> Optional[Path]:
    """在 PATH 与附加目录中查找可执行文件（支持 .exe/.cmd/.bat）。"""
    found = shutil.which(name)
    if found:
        return Path(found)
    for directory in extra_dirs:
        directory = os.path.expandvars(str(directory))
        for ext in ("", ".exe", ".cmd", ".bat"):
            candidate = Path(directory) / f"{name}{ext}"
            if candidate.is_file():
                return candidate
    return None


def check_command(name: str, timeout: int = config.COMMAND_VERSION_TIMEOUT) -> bool:
    """命令是否可执行（仅在 PATH 中查找），通过 --version 探测。"""
    exe = shutil.which(name)
    if exe is None:
        return False
    try:
        result = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def run_cmd(
    cmd: Command,
    cwd=None,
    env=None,
    timeout: Optional[int] = None,
    check: bool = True,
) -> int:
    """执行命令并实时输出（stdout/stderr 合并），返回退出码。

    - 字符串形式走 shell（兼容原有行为）；列表形式不经过 shell，更安全。
    - check=True 且退出码非零时抛 CommandError。
    """
    if isinstance(cmd, str):
        argv: Union[str, List[str]] = cmd
        shell = True
    else:
        argv = list(cmd)
        shell = False
    display = argv if isinstance(argv, str) else subprocess.list2cmdline(argv)
    info(f"> {display}")

    process = subprocess.Popen(
        argv,
        shell=shell,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    stream = process.stdout
    assert stream is not None  # stdout=PIPE 时恒为真
    output: List[str] = []
    try:
        for line in stream:
            sys.stdout.write(line)
            sys.stdout.flush()
            output.append(line)
        stream.close()
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise CommandError(display, -1, f"命令执行超时（{timeout} 秒），已强制终止")
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        raise

    if check and returncode != 0:
        tail = "".join(output[-40:]).strip()
        raise CommandError(display, returncode, tail)
    return returncode


# ---------- 下载 ----------

def download(
    url: str,
    dest_dir: Path,
    retries: int = config.DOWNLOAD_RETRIES,
    timeout: int = config.DOWNLOAD_TIMEOUT,
) -> Path:
    """带重试与进度显示的下载；先写 .part 临时文件，成功后原子替换。"""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = url.rstrip("/").rsplit("/", 1)[-1]
    dest = dest_dir / filename
    part = dest.with_name(dest.name + ".part")
    part.unlink(missing_ok=True)

    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            info(f"正在下载 {url} （第 {attempt}/{retries} 次尝试）...")
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                with open(part, "wb") as handle:
                    while True:
                        chunk = response.read(config.DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        progress(downloaded, total)
                newline()
            if downloaded == 0:
                raise DownloadError("服务器返回空内容")
            if total > 0 and downloaded != total:
                raise DownloadError(f"文件大小不匹配：预期 {total:,} 字节，实际 {downloaded:,} 字节")
            part.replace(dest)
            ok(f"下载完成：{dest}（{downloaded:,} 字节）")
            return dest
        except Exception as exc:  # 含 DownloadError，统一走重试
            part.unlink(missing_ok=True)
            last_error = exc
            if attempt < retries:
                warn(f"下载失败：{exc}；{config.DOWNLOAD_RETRY_DELAY} 秒后重试...")
                time.sleep(config.DOWNLOAD_RETRY_DELAY)
    raise DownloadError(f"下载失败（已重试 {retries} 次）：{url} -> {last_error}") from last_error


# ---------- 桌面路径 ----------

def get_desktop_path() -> Path:
    """返回桌面目录（支持 OneDrive 重定向）。"""
    try:
        buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        if ctypes.windll.shell32.SHGetFolderPathW(
            None, _CSIDL_DESKTOPDIRECTORY, None, 0, buffer
        ) == 0:
            return Path(buffer.value)
    except Exception:
        pass
    return Path(os.path.expanduser("~/Desktop"))
