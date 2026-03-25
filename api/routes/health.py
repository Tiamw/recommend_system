from __future__ import annotations

from fastapi import APIRouter

from api.config.settings import AppSettings
from api.db.database import check_database
from api.services.recommendation import RecommendationService


def build_health_router(
    settings: AppSettings,
    recommendation_service: RecommendationService,
) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get(
        "/health",
        summary="检查服务健康状态",
        description="返回当前后端服务版本、SQLite 连通性、模型状态与基础运行配置。",
    )
    def health() -> dict[str, object]:
        # 这里返回联调和部署阶段最常看的状态信息，方便快速排查配置问题。
        return {
            "status": "ok",
            "version": settings.app_version,
            "database": {
                "status": "ok" if check_database(settings.database_path) else "error",
                "path": str(settings.database_path),
            },
            "model": {
                "loaded": recommendation_service.is_ready,
                "path": str(settings.onnx_path),
                "default_top_k": settings.default_top_k,
                "max_seq_len": settings.max_seq_len,
            },
            "cors_origins": settings.cors_origins,
        }

    return router
