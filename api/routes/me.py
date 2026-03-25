from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.schemas.auth import CurrentUser
from api.schemas.history import (
    FavoriteCreateRequest,
    FavoriteItemResponse,
    HistoryCreateRequest,
    HistoryItemResponse,
)
from api.services.history import HistoryService


def build_me_router(
    history_service: HistoryService,
    current_user_dependency: Callable[..., CurrentUser],
) -> APIRouter:
    router = APIRouter(prefix="/me", tags=["me"])

    @router.get(
        "/history",
        response_model=list[HistoryItemResponse],
        summary="获取当前用户观看历史",
        description="读取当前登录用户已经记录的动漫观看历史，按最近时间倒序返回。",
    )
    def get_history(current_user: CurrentUser = Depends(current_user_dependency)) -> list[HistoryItemResponse]:
        items = history_service.list_history(current_user.id)
        return [HistoryItemResponse(**item) for item in items]

    @router.post(
        "/history",
        response_model=HistoryItemResponse,
        status_code=status.HTTP_201_CREATED,
        summary="追加观看历史",
        description="将一个动漫 ID 追加到当前登录用户的观看历史中。",
    )
    def add_history(
        request: HistoryCreateRequest,
        current_user: CurrentUser = Depends(current_user_dependency),
    ) -> HistoryItemResponse:
        try:
            item = history_service.add_history(current_user.id, request.anime_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return HistoryItemResponse(**item)

    @router.get(
        "/favorites",
        response_model=list[FavoriteItemResponse],
        summary="获取当前用户收藏夹",
        description="读取当前登录用户的收藏动漫列表，按最近收藏时间倒序返回。",
    )
    def get_favorites(
        current_user: CurrentUser = Depends(current_user_dependency),
    ) -> list[FavoriteItemResponse]:
        items = history_service.list_favorites(current_user.id)
        return [FavoriteItemResponse(**item) for item in items]

    @router.post(
        "/favorites",
        response_model=FavoriteItemResponse,
        status_code=status.HTTP_201_CREATED,
        summary="新增收藏",
        description="将一个动漫 ID 加入当前登录用户的收藏夹。",
    )
    def add_favorite(
        request: FavoriteCreateRequest,
        current_user: CurrentUser = Depends(current_user_dependency),
    ) -> FavoriteItemResponse:
        try:
            item = history_service.add_favorite(current_user.id, request.anime_id)
        except ValueError as exc:
            detail = str(exc)
            status_code = 400 if detail == "Anime already in favorites." else 404
            raise HTTPException(status_code=status_code, detail=detail) from exc
        return FavoriteItemResponse(**item)

    @router.delete(
        "/favorites/{anime_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="删除收藏",
        description="从当前登录用户的收藏夹中移除指定动漫 ID。",
    )
    def delete_favorite(
        anime_id: int,
        current_user: CurrentUser = Depends(current_user_dependency),
    ) -> Response:
        try:
            history_service.delete_favorite(current_user.id, anime_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
