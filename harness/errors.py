"""自定义异常类型，便于上层统一捕获与提示。"""


class HarnessError(Exception):
    """安装器基础异常：信息对用户可见，无需打印堆栈。"""


class PrerequisiteError(HarnessError):
    """前置环境（Git / Node.js / pnpm）缺失或安装失败。"""


class DownloadError(HarnessError):
    """下载失败（重试耗尽、文件不完整等）。"""


class CommandError(HarnessError):
    """外部命令执行失败。"""

    def __init__(self, command: str, returncode: int, tail: str = ""):
        self.command = command
        self.returncode = returncode
        self.tail = tail
        super().__init__(f"命令执行失败（退出码 {returncode}）：{command}")
