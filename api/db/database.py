from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def get_db_connection(database_path: Path) -> Iterator[sqlite3.Connection]:
    """统一管理 SQLite 连接，避免后续路由里重复样板代码。"""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def check_database(database_path: Path) -> bool:
    """做最基础的数据库连通性检查，供健康检查接口使用。"""
    with get_db_connection(database_path) as connection:
        connection.execute("SELECT 1")
    return True


def initialize_database(database_path: Path) -> None:
    """初始化业务表，为后续用户系统接口做准备。"""
    with get_db_connection(database_path) as connection:
        # 这里先补齐用户、历史和收藏三张表，动漫主表继续复用现有数据。
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                watched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (anime_id) REFERENCES anime(anime_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (anime_id) REFERENCES anime(anime_id) ON DELETE CASCADE,
                UNIQUE (user_id, anime_id)
            );

            CREATE INDEX IF NOT EXISTS idx_user_history_user_id
            ON user_history(user_id);

            CREATE INDEX IF NOT EXISTS idx_user_history_anime_id
            ON user_history(anime_id);

            CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id
            ON user_favorites(user_id);
            """
        )
        connection.commit()
