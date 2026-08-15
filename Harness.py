"""deepseek-harness 一键安装器入口。

PyInstaller 打包入口（打包配置见 Harness.spec），实际逻辑在 harness 包中。
"""

from harness.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
