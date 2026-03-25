from __future__ import annotations

from pydantic import BaseModel, Field


class HistoryCreateRequest(BaseModel):
    anime_id: int = Field(..., description="要追加到观看历史中的动漫原始 ID。")


class HistoryItemResponse(BaseModel):
    anime_id: int = Field(..., description="动漫原始 ID。")
    name: str = Field(..., description="动漫名称。")
    genre: str | None = Field(None, description="动漫题材标签。")
    type: str | None = Field(None, description="动漫类型，例如 TV、Movie。")
    rating: float | None = Field(None, description="平均评分。")
    watched_at: str = Field(..., description="加入观看历史的时间。")


class FavoriteCreateRequest(BaseModel):
    anime_id: int = Field(..., description="要加入收藏夹的动漫原始 ID。")


class FavoriteItemResponse(BaseModel):
    anime_id: int = Field(..., description="动漫原始 ID。")
    name: str = Field(..., description="动漫名称。")
    genre: str | None = Field(None, description="动漫题材标签。")
    type: str | None = Field(None, description="动漫类型，例如 TV、Movie。")
    rating: float | None = Field(None, description="平均评分。")
    created_at: str = Field(..., description="加入收藏夹的时间。")
