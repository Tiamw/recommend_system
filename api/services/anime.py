from __future__ import annotations

from collections import Counter

from api.config.settings import AppSettings
from api.db.database import get_db_connection


class AnimeService:
    """负责动漫数据查询，统一屏蔽 SQLite 访问细节。"""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def get_anime_detail(self, anime_id: int) -> dict[str, object] | None:
        with get_db_connection(self.settings.database_path) as connection:
            row = connection.execute(
                """
                SELECT anime_id, name, genre, type, episodes, rating, members
                FROM anime
                WHERE anime_id = ?
                """,
                (anime_id,),
            ).fetchone()

        if row is None:
            return None

        # sqlite3.Row 可以直接转成 dict，返回给 Pydantic 做结构校验。
        return dict(row)

    def list_genres(self, limit: int = 24) -> list[dict[str, object]]:
        with get_db_connection(self.settings.database_path) as connection:
            rows = connection.execute(
                """
                SELECT genre
                FROM anime
                WHERE genre IS NOT NULL AND TRIM(genre) != ''
                """
            ).fetchall()

        counter: Counter[str] = Counter()
        for row in rows:
            for item in str(row['genre']).split(','):
                genre_name = item.strip()
                if genre_name:
                    counter[genre_name] += 1

        return [
            {'name': name, 'count': count}
            for name, count in counter.most_common(limit)
        ]

    def list_anime(
        self,
        page: int = 1,
        page_size: int = 24,
        keyword: str = '',
        genre: str = '',
    ) -> dict[str, object]:
        offset = (page - 1) * page_size
        conditions: list[str] = []
        params: list[object] = []

        if keyword.strip():
            conditions.append('(name LIKE ? OR genre LIKE ?)')
            keyword_value = f'%{keyword.strip()}%'
            params.extend([keyword_value, keyword_value])

        if genre.strip():
            # 动漫题材是逗号分隔文本，这里用模糊匹配支持前端点击题材筛选。
            conditions.append('genre LIKE ?')
            params.append(f'%{genre.strip()}%')

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ''

        with get_db_connection(self.settings.database_path) as connection:
            total = connection.execute(
                f'''
                SELECT COUNT(*) AS total
                FROM anime
                {where_clause}
                ''',
                params,
            ).fetchone()['total']

            rows = connection.execute(
                f'''
                SELECT anime_id, name, genre, type, rating
                FROM anime
                {where_clause}
                ORDER BY rating DESC, members DESC, anime_id ASC
                LIMIT ? OFFSET ?
                ''',
                [*params, page_size, offset],
            ).fetchall()

        return {
            'items': [dict(row) for row in rows],
            'total': total,
            'page': page,
            'page_size': page_size,
        }

    def list_anime_cards(self, anime_ids: list[int]) -> list[dict[str, object]]:
        if not anime_ids:
            return []

        placeholders = ', '.join('?' for _ in anime_ids)
        with get_db_connection(self.settings.database_path) as connection:
            rows = connection.execute(
                f'''
                SELECT anime_id, name, genre, type, rating
                FROM anime
                WHERE anime_id IN ({placeholders})
                ''',
                anime_ids,
            ).fetchall()

        anime_map = {row['anime_id']: dict(row) for row in rows}
        # 按推荐分数顺序返回，避免 SQL IN 打乱模型输出顺序。
        return [anime_map[anime_id] for anime_id in anime_ids if anime_id in anime_map]
