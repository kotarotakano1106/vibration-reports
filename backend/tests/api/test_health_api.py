from fastapi.testclient import TestClient


def test_root_returns_api_information(api_client: TestClient) -> None:
    """ルートAPIが基本情報を返す。"""
    response = api_client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "振動AI日報生成API",
        "docs": "/docs",
        "health": "/health",
    }


def test_health_returns_ok(api_client: TestClient) -> None:
    """Health APIが稼働状態を返す。"""
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_contains_api_v1_routes(api_client: TestClient) -> None:
    """OpenAPIに主要なv1 APIが登録されている。"""
    response = api_client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/files" in paths
    assert "/api/v1/files/{uploaded_file_id}/measurements" in paths
    assert "/api/v1/reports" in paths
    assert "/api/v1/reports/generate" in paths
    assert "/api/v1/reports/{report_id}/pdf" in paths
    assert "/api/v1/search" in paths
    assert "/api/v1/chat" in paths
