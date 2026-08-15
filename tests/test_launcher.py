"""Harness.bat 模板生成测试。"""

import unittest
from pathlib import Path

from harness import config
from harness.launcher import build_bat_content


class LauncherTemplateTest(unittest.TestCase):
    def setUp(self):
        self.content = build_bat_content(
            harness_dir=Path(r"C:/Deepseek-Harness/deepseek-harness"),
            goal_file=Path(r"C:/Deepseek-Harness/goal_address.txt"),
            default_url=config.GOAL_URL,
            wait_timeout=15,
        )

    def test_no_unfilled_placeholders(self):
        for placeholder in ("{harness_dir}", "{goal_file}", "{default_url}", "{wait_timeout}"):
            self.assertNotIn(placeholder, self.content)

    def test_harness_dir_embedded(self):
        self.assertIn(r'cd /d "C:\Deepseek-Harness\deepseek-harness"', self.content)

    def test_goal_file_embedded(self):
        self.assertIn(
            r'if exist "C:\Deepseek-Harness\goal_address.txt" set /p GOAL_URL=<"C:\Deepseek-Harness\goal_address.txt"',
            self.content,
        )

    def test_default_url_embedded(self):
        self.assertIn(f'set "GOAL_URL={config.GOAL_URL}"', self.content)
        self.assertIn('start "" "%GOAL_URL%"', self.content)

    def test_wait_timeout_embedded(self):
        self.assertIn("lss 15 goto wait_loop", self.content)

    def test_pnpm_search_locations(self):
        self.assertIn(r"%LOCALAPPDATA%\pnpm", self.content)
        self.assertIn(r"%ProgramFiles%\nodejs", self.content)

    def test_cleanup_of_output_file(self):
        self.assertIn("del output.txt 2>nul", self.content)


if __name__ == "__main__":
    unittest.main()
