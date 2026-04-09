from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.schemas.anime import (
    AnimeCardResponse,
    AnimeDetailResponse,
    AnimeGenreListResponse,
    AnimeGenreResponse,
    AnimeListResponse,
)
from api.services.anime import AnimeService


def build_anime_router(anime_service: AnimeService) -> APIRouter:
    router = APIRouter(tags=["anime"])

    @router.get(
        "/anime/genres",
        response_model=AnimeGenreListResponse,
        summary="获取动漫题材筛选列表",
        description="返回站内常见动漫题材及数量，供前端做可点击的类型栏。",
    )
    def list_anime_genres(
        limit: int = Query(24, ge=1, le=60, description="最多返回多少个题材标签。"),
    ) -> AnimeGenreListResponse:
        items = anime_service.list_genres(limit=limit)
        return AnimeGenreListResponse(items=[AnimeGenreResponse(**item) for item in items])

    @router.get(
        "/anime",
        response_model=AnimeListResponse,
        summary="获取动漫列表",
        description="分页获取全部动漫信息，支持按名称关键字和题材筛选。",
    )
    def list_anime(
        page: int = Query(1, ge=1, description="页码，从 1 开始。"),
        page_size: int = Query(24, ge=1, le=60, description="每页返回数量。"),
        keyword: str = Query('', description="名称关键字，可选。"),
        genre: str = Query('', description="题材筛选，可选。"),
    ) -> AnimeListResponse:
        payload = anime_service.list_anime(page=page, page_size=page_size, keyword=keyword, genre=genre)
        return AnimeListResponse(
            items=[AnimeCardResponse(**item) for item in payload['items']],
            total=payload['total'],
            page=payload['page'],
            page_size=payload['page_size'],
        )

    @router.get(
        "/anime/{anime_id}",
        response_model=AnimeDetailResponse,
        summary="获取动漫详情",
        description="根据动漫原始 ID 查询名称、题材、类型、评分等基础信息。",
    )
    def get_anime_detail(anime_id: int) -> AnimeDetailResponse:
        anime = anime_service.get_anime_detail(anime_id)
        if anime is None:
            raise HTTPException(status_code=404, detail="Anime not found.")

        return AnimeDetailResponse(**anime)

    return router
