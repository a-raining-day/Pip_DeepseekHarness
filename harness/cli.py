"""命令行入口：整体流程编排与异常兜底。"""

import os
import traceback
from pathlib import Path

from . import __version__, config
from .console import blank, error, heading, info
from .environment import ensure_environment
from .errors import HarnessError
from .installer import HarnessInstaller


def _ask_install_dir() -> Path:
    raw = input(
        f"请输入安装目录（默认 {config.DEFAULT_INSTALL_DIR}，直接回车使用默认）: "
    ).strip().strip('"')
    if not raw:
        raw = config.DEFAULT_INSTALL_DIR
    return Path(os.path.expanduser(raw))


def pause() -> None:
    """保持窗口开启，便于用户查看结果。"""
    try:
        input("\n按任意键退出...")
    except (EOFError, KeyboardInterrupt):
        pass


def main(argv=None) -> int:
    del argv  # 暂不支持命令行参数
    heading(f"deepseek-harness 一键安装器 v{__version__}")
    try:
        # 0. 检测并自动安装环境（Node.js 和 Git）
        ensure_environment()

        # 1. 询问存放目录并创建
        base_dir = _ask_install_dir()
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            error(f"无法创建安装目录 {base_dir}：{exc}")
            pause()
            return 1

        # 2. 执行安装流程
        installer = HarnessInstaller(base_dir)
        launcher = installer.run()

        # 3. 完成提示
        blank()
        heading("安装完成")
        info(f"安装目录：{installer.base_dir}")
        info(f"启动文件：{launcher}")
        info("双击桌面上的 Harness.bat 即可启动服务并自动打开浏览器。")
        info("若需修改监听地址，请编辑 deepseek-harness 相关配置，并同步更新 goal_address.txt。")
        pause()
        return 0
    except KeyboardInterrupt:
        info("用户中断，已取消安装。")
    except HarnessError as exc:
        error(str(exc))
    except Exception as exc:
        error(f"发生未预期错误：{exc}")
        if os.environ.get("HARNESS_DEBUG"):
            traceback.print_exc()
    pause()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
