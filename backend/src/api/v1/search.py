"""過去レポートのベクトル類似検索API。"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from backend.src.db.dependencies import (
    get_db_session,
)
from backend.src.schemas.search_schema import (
    RagSearchRequest,
    RagSearchResponse,
    RagSearchResultResponse,
)
from backend.src.services.rag_search_service import (
    RagSearchEmbeddingError,
    RagSearchQueryError,
    RagSearchService,
    RagSearchServiceError,
)

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


@router.post(
    "",
    response_model=RagSearchResponse,
    status_code=status.HTTP_200_OK,
)
def search_reports(
    request: RagSearchRequest,
    session: Session = Depends(
        get_db_session
    ),
):
    """検索文に類似する過去レポートチャンクを返す。"""

    service = RagSearchService(
        session
    )

    try:
        search_results = service.search(
            query=request.query,
            limit=request.limit,
            equipment_id=request.equipment_id,
            measurement_date_from=(
                request.measurement_date_from
            ),
            measurement_date_to=(
                request.measurement_date_to
            ),
            chunk_types=request.chunk_types,
        )

    except RagSearchQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RagSearchEmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except RagSearchServiceError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        ) from exc

    results = []

    for result in search_results:
        chunk = result.report_chunk

        results.append(
            RagSearchResultResponse(
                report_chunk_id=chunk.id,
                report_id=chunk.report_id,
                chunk_index=chunk.chunk_index,
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                equipment_id=chunk.equipment_id,
                measurement_date=(
                    chunk.measurement_date
                ),
                distance=result.distance,
                similarity=result.similarity,
                embedding_model=(
                    chunk.embedding_model
                ),
                metadata_json=(
                    chunk.metadata_json or {}
                ),
            )
        )

    return RagSearchResponse(
        query=request.query,
        result_count=len(results),
        results=results,
    )
