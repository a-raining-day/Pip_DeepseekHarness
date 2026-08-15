"""前置环境准备：Git 与 Node.js 的检测、自动安装与验证。"""

import json
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from . import config, utils
from .console import heading, info, ok, warn
from .errors import PrerequisiteError

GIT_SEARCH_DIRS: List[str] = [
    r"%ProgramFiles%\Git\cmd",
    r"%ProgramFiles(x86)%\Git\cmd",
    r"%LOCALAPPDATA%\Programs\Git\cmd",
]
NODE_SEARCH_DIRS: List[str] = [
    r"%ProgramFiles%\nodejs",
    r"%ProgramFiles(x86)%\nodejs",
]


def _latest_lts_version() -> Optional[str]:
    """查询 nodejs.org 的最新 LTS 版本号；失败返回 None，由调用方回退。"""
    try:
        request = urllib.request.Request(
            config.NODE_LTS_INDEX_URL, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(request, timeout=config.NODE_INDEX_TIMEOUT) as response:
            releases = json.loads(response.read().decode("utf-8"))
        for release in releases:
            if release.get("lts"):
                return str(release["version"]).lstrip("v")
    except Exception as exc:
        warn(f"获取 Node.js 最新 LTS 版本失败（{exc}），改用固定版本 {config.NODE_FALLBACK_VERSION}")
    return None


def install_git() -> bool:
    """静默安装 Git for Windows，返回是否成功。"""
    installer = Path(tempfile.gettempdir()) / config.GIT_INSTALLER_FILENAME
    try:
        utils.download(config.GIT_INSTALLER_URL, installer.parent)
        info("正在静默安装 Git（请稍候，可能需要几分钟）...")
        returncode = utils.run_cmd(
            [str(installer), "/VERYSILENT", "/NORESTART", "/NOCANCEL",
             "/SP-", "/SUPPRESSMSGBOXES", "/ADDLOCAL=ALL"],
            timeout=config.INSTALLER_TIMEOUT,
            check=False,
        )
        if returncode != 0:
            warn(f"Git 安装器返回退出码 {returncode}")
            return False
        return True
    finally:
        installer.unlink(missing_ok=True)


def install_node(version: str) -> bool:
    """通过 MSI 静默安装 Node.js，返回是否成功。"""
    installer = Path(tempfile.gettempdir()) / f"node-v{version}-x64.msi"
    try:
        utils.download(
            config.NODE_MSI_URL_TEMPLATE.format(version=version), installer.parent
        )
        info("正在静默安装 Node.js（请稍候，可能需要几分钟）...")
        returncode = utils.run_cmd(
            ["msiexec", "/i", str(installer), "/qn", "ALLUSERS=1", "/norestart"],
            timeout=config.INSTALLER_TIMEOUT,
            check=False,
        )
        if returncode not in (0, 1641, 3010):  # 0 成功；1641/3010 成功但需重启
            warn(f"Node.js 安装器返回退出码 {returncode}")
            return False
        return True
    finally:
        installer.unlink(missing_ok=True)


def _make_available(
    name: str,
    search_dirs: Iterable[str],
    installer: Callable[[], bool],
) -> None:
    """确保命令可用：PATH 命中 -> 附加目录命中 -> 自动安装；失败抛 PrerequisiteError。"""
    if utils.check_command(name):
        ok(f"{name} 已可用")
        return
    exe = utils.find_executable(name, search_dirs)
    if exe is not None:
        utils.add_to_path(exe.parent)
        ok(f"{name} 可用（{exe}）")
        return
    info(f"未检测到 {name}，开始自动安装...")
    if not utils.is_admin():
        warn(f"安装 {name} 需要管理员权限，正在请求提权（请在 UAC 弹窗中点击“是”）...")
        utils.relaunch_as_admin()  # 成功时进程会重启，不会执行到下一行
    if not installer():
        raise PrerequisiteError(f"{name} 安装失败，请手动安装后重试。")
    utils.refresh_path_from_registry()
    exe = utils.find_executable(name, search_dirs)
    if exe is None:
        raise PrerequisiteError(
            f"{name} 安装完成，但未能在 PATH 中找到，请重启终端或手动添加 PATH 后重试。"
        )
    utils.add_to_path(exe.parent)
    ok(f"{name} 安装成功（{exe}）")


def ensure_environment() -> None:
    """确保 Node.js 与 Git 可用，否则尝试自动安装；失败抛 PrerequisiteError。"""
    heading("环境检查：Node.js 和 Git")
    _make_available("git", GIT_SEARCH_DIRS, install_git)
    _make_available(
        "node",
        NODE_SEARCH_DIRS,
        lambda: install_node(_latest_lts_version() or config.NODE_FALLBACK_VERSION),
    )
    ok("环境检查通过，继续执行 Harness 安装...")
