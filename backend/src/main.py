from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.api.v1.router import (
    api_v1_router,
)

app = FastAPI(
    title="振動AI日報生成API",
    description=(
        "振動データの分析と"
        "日報生成を行うAPI"
    ),
    version="0.1.0",
)


allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


app.include_router(
    api_v1_router,
)


@app.get(
    "/",
    tags=["health"],
)
def root():
    """APIの基本情報を返す。"""

    return {
        "message": "振動AI日報生成API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    tags=["health"],
)
def health_check():
    """APIの稼働状態を確認する。"""

    return {
        "status": "ok",
    }