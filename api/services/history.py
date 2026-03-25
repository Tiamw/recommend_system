from __future__ import annotations

import sqlite3

from api.config.settings import AppSettings
from api.db.database import get_db_connection


class HistoryService:
    """负责当前用户观看历史与收藏夹的查询和写入。"""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def list_history(self, user_id: int) -> list[dict[str, object]]:
        with get_db_connection(self.settings.database_path) as connection:
            rows = connection.execute(
                """
                SELECT h.anime_id, a.name, a.genre, a.type, a.rating, h.watched_at
                FROM user_history AS h
                INNER JOIN anime AS a ON a.anime_id = h.anime_id
                WHERE h.user_id = ?
                ORDER BY h.watched_at DESC, h.id DESC
                """,
                (user_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def add_history(self, user_id: int, anime_id: int) -> dict[str, object]:
        with get_db_connection(self.settings.database_path) as connection:
            anime = connection.execute(
                "SELECT anime_id, name, genre, type, rating FROM anime WHERE anime_id = ?",
                (anime_id,),
            ).fetchone()
            if anime is None:
                raise ValueError("Anime not found.")

            cursor = connection.execute(
                """
                INSERT INTO user_history (user_id, anime_id)
                VALUES (?, ?)
                """,
                (user_id, anime_id),
            )
            connection.commit()

            history_item = connection.execute(
                """
                SELECT h.anime_id, a.name, a.genre, a.type, a.rating, h.watched_at
                FROM user_history AS h
                INNER JOIN anime AS a ON a.anime_id = h.anime_id
                WHERE h.id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

        return dict(history_item)

    def list_favorites(self, user_id: int) -> list[dict[str, object]]:
        with get_db_connection(self.settings.database_path) as connection:
            rows = connection.execute(
                """
                SELECT f.anime_id, a.name, a.genre, a.type, a.rating, f.created_at
                FROM user_favorites AS f
                INNER JOIN anime AS a ON a.anime_id = f.anime_id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC, f.id DESC
                """,
                (user_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def add_favorite(self, user_id: int, anime_id: int) -> dict[str, object]:
        with get_db_connection(self.settings.database_path) as connection:
            anime = connection.execute(
                "SELECT anime_id FROM anime WHERE anime_id = ?",
                (anime_id,),
            ).fetchone()
            if anime is None:
                raise ValueError("Anime not found.")

            try:
                cursor = connection.execute(
                    """
                    INSERT INTO user_favorites (user_id, anime_id)
                    VALUES (?, ?)
                    """,
                    (user_id, anime_id),
                )
                connection.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("Anime already in favorites.") from exc

            favorite_item = connection.execute(
                """
                SELECT f.anime_id, a.name, a.genre, a.type, a.rating, f.created_at
                FROM user_favorites AS f
                INNER JOIN anime AS a ON a.anime_id = f.anime_id
                WHERE f.id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()

        return dict(favorite_item)

    def delete_favorite(self, user_id: int, anime_id: int) -> None:
        with get_db_connection(self.settings.database_path) as connection:
            cursor = connection.execute(
                """
                DELETE FROM user_favorites
                WHERE user_id = ? AND anime_id = ?
                """,
                (user_id, anime_id),
            )
            connection.commit()

        if cursor.rowcount == 0:
            raise ValueError("Favorite not found.")
