from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | Path) -> dict[str, Any]:
    """读取 YAML 配置，作为后端统一配置入口。"""
    with Path(config_path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@dataclass(frozen=True)
class AppSettings:
    """封装项目运行时需要的核心路径与认证参数。"""

    config_path: Path
    project_root: Path
    raw_config: dict[str, Any]

    @property
    def app_name(self) -> str:
        return "Mini-Anime-Rec API"

    @property
    def app_version(self) -> str:
        return "0.2.0"

    @property
    def database_path(self) -> Path:
        # 当前阶段继续沿用已有动漫库，后续用户表也落在同一个 SQLite 文件里。
        return self.project_root / "data" / "anime.db"

    @property
    def mappings_dir(self) -> Path:
        return self.project_root / Path(self.raw_config["paths"]["mappings_dir"])

    @property
    def onnx_path(self) -> Path:
        onnx_dir = self.project_root / Path(self.raw_config["paths"]["onnx_dir"])
        return onnx_dir / self.raw_config["export"]["onnx_name"]

    @property
    def max_seq_len(self) -> int:
        return int(self.raw_config["data"]["max_seq_len"])

    @property
    def default_top_k(self) -> int:
        return int(self.raw_config["export"]["top_k"])

    @property
    def jwt_secret(self) -> str:
        return os.getenv("JWT_SECRET", "dev-secret-change-me")

    @property
    def jwt_expire_minutes(self) -> int:
        return int(os.getenv("JWT_EXPIRE_MINUTES", "120"))

    @property
    def cors_origins(self) -> list[str]:
        raw_value = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        return [item.strip() for item in raw_value.split(",") if item.strip()]


def get_settings() -> AppSettings:
    """根据环境变量和默认路径构造配置对象。"""
    config_path = Path(os.getenv("CONFIG_PATH", "training/configs/default.yaml")).resolve()
    project_root = config_path.parents[2]
    return AppSettings(
        config_path=config_path,
        project_root=project_root,
        raw_config=load_config(config_path),
    )
