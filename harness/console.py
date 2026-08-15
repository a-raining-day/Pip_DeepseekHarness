"""统一的控制台输出（级别标记 + 步骤 + 进度条）。"""

import sys

_BAR_WIDTH = 24


def info(message: str) -> None:
    print(f"[INFO] {message}", flush=True)


def warn(message: str) -> None:
    print(f"[WARN] {message}", flush=True)


def error(message: str) -> None:
    print(f"[ERROR] {message}", flush=True)


def ok(message: str) -> None:
    print(f"[OK] {message}", flush=True)


def step(message: str) -> None:
    print(f"\n[步骤] {message}", flush=True)


def blank() -> None:
    print(flush=True)


def newline() -> None:
    sys.stdout.write("\n")
    sys.stdout.flush()


def heading(title: str) -> None:
    blank()
    print("=" * 56)
    print(title)
    print("=" * 56)


def progress(done: int, total: int) -> None:
    """单行进度条；total <= 0（无法获知大小）时不显示。"""
    if total <= 0:
        return
    percent = min(100, int(done * 100 / total))
    filled = int(_BAR_WIDTH * percent / 100)
    bar = "#" * filled + "-" * (_BAR_WIDTH - filled)
    sys.stdout.write(f"\r  [{bar}] {percent:3d}%  {done:,} / {total:,} 字节")
    sys.stdout.flush()
