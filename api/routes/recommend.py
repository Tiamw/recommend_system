from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.recommend import RecommendItemResponse, RecommendRequest, RecommendResponse
from api.services.anime import AnimeService
from api.services.recommendation import RecommendationService


def build_recommend_router(
    recommendation_service: RecommendationService,
    anime_service: AnimeService,
) -> APIRouter:
    router = APIRouter(tags=["recommend"])

    @router.post(
        "/recommend",
        response_model=RecommendResponse,
        summary="根据观看历史生成推荐结果",
        description="输入原始动漫 ID 列表和可选的 top_k，返回带元数据的推荐结果列表。",
    )
    def recommend(request: RecommendRequest) -> RecommendResponse:
        try:
            top_raw_ids = recommendation_service.recommend(
                raw_anime_history=request.raw_anime_history,
                top_k=request.top_k,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        items = anime_service.list_anime_cards(top_raw_ids)
        return RecommendResponse(items=[RecommendItemResponse(**item) for item in items])

    return router
