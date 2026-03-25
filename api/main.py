from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config.settings import get_settings
from api.db.database import initialize_database
from api.routes.anime import build_anime_router
from api.routes.auth import build_auth_router
from api.routes.health import build_health_router
from api.routes.me import build_me_router
from api.routes.recommend import build_recommend_router
from api.services.anime import AnimeService
from api.services.auth import AuthService
from api.services.dependencies import build_current_user_dependency
from api.services.history import HistoryService
from api.services.recommendation import RecommendationService


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    # 启动时先确保业务表存在，避免后续认证和个人中心接口缺表。
    initialize_database(settings.database_path)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    anime_service = AnimeService(settings)
    auth_service = AuthService(settings)
    history_service = HistoryService(settings)
    recommendation_service = RecommendationService(settings)
    current_user_dependency = build_current_user_dependency(auth_service)

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(build_anime_router(anime_service))
    app.include_router(build_auth_router(auth_service))
    app.include_router(build_me_router(history_service, current_user_dependency))
    app.include_router(build_recommend_router(recommendation_service, anime_service))
    app.include_router(build_health_router(settings, recommendation_service))
    return app


app = create_app()
