from __future__ import annotations

from pydantic import BaseModel, Field


class AnimeCardResponse(BaseModel):
    anime_id: int = Field(..., description="动漫原始 ID。")
    name: str = Field(..., description="动漫名称。")
    genre: str | None = Field(None, description="动漫题材标签。")
    type: str | None = Field(None, description="动漫类型，例如 TV、Movie。")
    rating: float | None = Field(None, description="平均评分。")


class AnimeGenreResponse(BaseModel):
    name: str = Field(..., description="题材名称。")
    count: int = Field(..., description="包含该题材的动漫数量。")


class AnimeGenreListResponse(BaseModel):
    items: list[AnimeGenreResponse] = Field(..., description="可用题材筛选列表。")


class AnimeListResponse(BaseModel):
    items: list[AnimeCardResponse] = Field(..., description="当前页动漫列表。")
    total: int = Field(..., description="符合条件的动漫总数。")
    page: int = Field(..., description="当前页码，从 1 开始。")
    page_size: int = Field(..., description="每页条数。")


class AnimeDetailResponse(BaseModel):
    anime_id: int = Field(..., description="动漫原始 ID。")
    name: str = Field(..., description="动漫名称。")
    genre: str | None = Field(None, description="动漫题材标签。")
    type: str | None = Field(None, description="动漫类型，例如 TV、Movie。")
    episodes: int | None = Field(None, description="总集数。")
    rating: float | None = Field(None, description="平均评分。")
    members: int | None = Field(None, description="收藏或成员人数。")
