from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.schemas.anime import AnimeCardResponse, AnimeDetailResponse, AnimeListResponse
from api.services.anime import AnimeService


def build_anime_router(anime_service: AnimeService) -> APIRouter:
    router = APIRouter(tags=["anime"])

    @router.get(
        "/anime",
        response_model=AnimeListResponse,
        summary="获取动漫列表",
        description="分页获取全部动漫信息，支持按名称或题材关键字搜索。",
    )
    def list_anime(
        page: int = Query(1, ge=1, description="页码，从 1 开始。"),
        page_size: int = Query(24, ge=1, le=60, description="每页返回数量。"),
        keyword: str = Query('', description="名称或题材关键字，可选。"),
    ) -> AnimeListResponse:
        payload = anime_service.list_anime(page=page, page_size=page_size, keyword=keyword)
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
