from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    # 健康检查是后续联调和部署排查的基础，因此这里验证关键运行信息是否存在。
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"]["status"] == "ok"
    assert payload["model"]["loaded"] is True
    assert payload["cors_origins"]


def test_recommend_endpoint_returns_candidates() -> None:
    # 这里验证推荐接口已经返回前端可直接展示的元数据结构。
    response = client.post(
        "/recommend",
        json={"raw_anime_history": [1, 5114, 9253], "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert len(payload["items"]) == 5
    assert payload["items"][0]["anime_id"]
    assert payload["items"][0]["name"]


def test_anime_detail_endpoint_returns_anime_data() -> None:
    # 这里直接读取已存在的 anime 表数据，验证数据库查询接口已经联通。
    response = client.get("/anime/1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["anime_id"] == 1
    assert payload["name"]


def test_auth_history_and_favorites_flow() -> None:
    # 这里使用时间戳用户名，避免重复执行测试时撞上唯一约束。
    import time

    username = f"test_user_{int(time.time())}"
    password = "secret123"

    register_response = client.post(
        "/auth/register",
        json={"username": username, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    add_history_response = client.post(
        "/me/history",
        json={"anime_id": 1},
        headers=headers,
    )
    assert add_history_response.status_code == 201
    assert add_history_response.json()["anime_id"] == 1

    list_history_response = client.get("/me/history", headers=headers)
    assert list_history_response.status_code == 200
    history_payload = list_history_response.json()
    assert history_payload
    assert history_payload[0]["anime_id"] == 1

    add_favorite_response = client.post(
        "/me/favorites",
        json={"anime_id": 5},
        headers=headers,
    )
    assert add_favorite_response.status_code == 201
    assert add_favorite_response.json()["anime_id"] == 5

    list_favorites_response = client.get("/me/favorites", headers=headers)
    assert list_favorites_response.status_code == 200
    favorites_payload = list_favorites_response.json()
    assert favorites_payload
    assert favorites_payload[0]["anime_id"] == 5

    delete_favorite_response = client.delete("/me/favorites/5", headers=headers)
    assert delete_favorite_response.status_code == 204
