"""核心安装流程：克隆仓库 -> 准备 pnpm -> 安装依赖 -> 构建 -> 生成启动器。"""

import os
from pathlib import Path
from typing import Dict, List

from . import config, utils
from .console import ok, step, warn
from .errors import PrerequisiteError
from .launcher import build_bat_content, write_launcher

PNPM_SEARCH_DIRS: List[str] = [
    r"%LOCALAPPDATA%\pnpm",
    r"%APPDATA%\npm",
    r"%ProgramFiles%\nodejs",
    r"%ProgramFiles(x86)%\nodejs",
]


class HarnessInstaller:
    """执行 deepseek-harness 的完整安装流程。"""

    def __init__(
        self,
        base_dir: Path,
        goal_url: str = config.GOAL_URL,
        repo_url: str = config.GIT_REPO_URL,
    ):
        self.base_dir = Path(base_dir)
        self.goal_url = goal_url
        self.repo_url = repo_url
        self.repo_dir = self.base_dir / config.REPO_DIR_NAME
        self.goal_file = self.base_dir / config.GOAL_FILENAME

    def run(self) -> Path:
        """执行安装，返回生成的启动器路径。"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._clone_repo()
        pnpm = self._ensure_pnpm()
        env = self._registry_env()
        self._install_dependencies(pnpm, env)
        self._build(pnpm, env)
        self._write_goal_file()
        return self._write_launcher()

    # ---------- 各步骤 ----------

    def _clone_repo(self) -> None:
        if self.repo_dir.exists():
            warn(f"目录 {self.repo_dir} 已存在，跳过克隆，直接使用。")
            return
        step("克隆 deepseek-harness 仓库")
        utils.run_cmd(["git", "clone", self.repo_url], cwd=self.base_dir)

    def _ensure_pnpm(self) -> str:
        """确保 pnpm 可用（已存在则跳过全局安装），返回可执行文件路径或命令名。"""
        step("检查 pnpm")
        pnpm = utils.find_executable("pnpm", PNPM_SEARCH_DIRS)
        if pnpm is not None:
            ok(f"pnpm 已可用（{pnpm}）")
            return str(pnpm)
        step("安装 pnpm（全局，使用淘宝镜像源）")
        utils.run_cmd(
            ["npm", "install", "-g", "pnpm",
             f"--registry={config.NPM_REGISTRY}", "--no-fund", "--no-audit"]
        )
        pnpm = utils.find_executable("pnpm", PNPM_SEARCH_DIRS)
        if pnpm is None:
            raise PrerequisiteError(
                "pnpm 安装后仍不可用。请检查 npm 全局目录（npm prefix -g）是否已加入 PATH 后重试。"
            )
        ok(f"pnpm 安装成功（{pnpm}）")
        return str(pnpm)

    def _registry_env(self) -> Dict[str, str]:
        """复制环境变量并指定 pnpm 使用淘宝镜像源。"""
        env = os.environ.copy()
        env["pnpm_config_registry"] = config.NPM_REGISTRY
        return env

    def _install_dependencies(self, pnpm: str, env: Dict[str, str]) -> None:
        step("安装项目依赖（pnpm install）")
        utils.run_cmd([pnpm, "install"], cwd=self.repo_dir, env=env)

    def _build(self, pnpm: str, env: Dict[str, str]) -> None:
        step("构建项目（pnpm run build）")
        utils.run_cmd([pnpm, "run", "build"], cwd=self.repo_dir, env=env)

    def _write_goal_file(self) -> None:
        step("写入目标地址记录文件")
        self.goal_file.write_text(self.goal_url, encoding="utf-8")
        ok(f"已创建 {self.goal_file}，内容：{self.goal_url}")

    def _write_launcher(self) -> Path:
        step("在桌面生成启动批处理文件")
        content = build_bat_content(
            harness_dir=self.repo_dir,
            goal_file=self.goal_file,
            default_url=self.goal_url,
        )
        path = write_launcher(utils.get_desktop_path() / config.BAT_FILENAME, content)
        ok(f"已创建 {path}")
        return path
