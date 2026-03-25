from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    # 先保持和原接口兼容，避免这一步重构影响已有调用方式。
    raw_anime_history: list[int] = Field(
        ...,
        description="用户看过的原始动漫 ID 列表，例如 [1, 5114, 9253]。",
    )
    top_k: Optional[int] = Field(
        None,
        description="希望返回的推荐数量，不传时使用系统默认值。",
    )


class RecommendItemResponse(BaseModel):
    anime_id: int = Field(..., description="推荐出的动漫原始 ID。")
    name: str = Field(..., description="动漫名称。")
    genre: str | None = Field(None, description="动漫题材标签。")
    type: str | None = Field(None, description="动漫类型，例如 TV、Movie。")
    rating: float | None = Field(None, description="平均评分。")


class RecommendResponse(BaseModel):
    items: list[RecommendItemResponse] = Field(
        ...,
        description="推荐结果列表，包含动漫 ID 和基础展示元数据。",
    )
