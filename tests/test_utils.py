"""utils 模块基础测试（不依赖网络与安装器）。"""

import os
import sys
import unittest
from pathlib import Path

from harness import utils
from harness.errors import CommandError


class FindExecutableTest(unittest.TestCase):
    def test_cmd_found_on_path(self):
        self.assertIsNotNone(utils.find_executable("cmd"))

    def test_extra_dir_found(self):
        system32 = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32"
        exe = utils.find_executable("cmd", [str(system32)])
        self.assertIsNotNone(exe)

    def test_missing_returns_none(self):
        self.assertIsNone(utils.find_executable("harness_no_such_tool_xyz"))


class RunCmdTest(unittest.TestCase):
    def test_success_returns_zero(self):
        rc = utils.run_cmd([sys.executable, "-c", "print('hello')"], check=False)
        self.assertEqual(rc, 0)

    def test_nonzero_raises_command_error(self):
        with self.assertRaises(CommandError):
            utils.run_cmd([sys.executable, "-c", "import sys; sys.exit(3)"], check=True)

    def test_check_false_returns_code(self):
        rc = utils.run_cmd([sys.executable, "-c", "import sys; sys.exit(3)"], check=False)
        self.assertEqual(rc, 3)


class PathHelpersTest(unittest.TestCase):
    def test_add_to_path_prepends(self):
        old = os.environ.get("PATH", "")
        try:
            utils.add_to_path(Path(r"C:\fake\harness\dir"))
            self.assertTrue(
                os.environ["PATH"].startswith(r"C:\fake\harness\dir" + os.pathsep)
            )
        finally:
            os.environ["PATH"] = old

    def test_desktop_path_exists_dir(self):
        desktop = utils.get_desktop_path()
        self.assertTrue(desktop.is_dir(), f"桌面目录不存在: {desktop}")


if __name__ == "__main__":
    unittest.main()
