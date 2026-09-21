"""過去レポートを根拠に回答するRAGチャットAPI。"""

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
from backend.src.schemas.chat_schema import (
    RagChatRequest,
    RagChatResponse,
    RagChatSourceResponse,
)
from backend.src.services.azure_openai_service import (
    AzureOpenAIServiceError,
)
from backend.src.services.rag_search_service import (
    RagSearchEmbeddingError,
    RagSearchQueryError,
    RagSearchServiceError,
)
from backend.src.workflows.graphs.rag_chat_graph import (
    build_rag_chat_graph,
)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post(
    "",
    response_model=RagChatResponse,
    status_code=status.HTTP_200_OK,
)
def chat_with_reports(
    request: RagChatRequest,
    session: Session = Depends(
        get_db_session
    ),
):
    """過去レポートを検索し、根拠付き回答を返す。"""

    graph = build_rag_chat_graph(
        session=session
    )

    graph_input = {
        "query": request.query,
        "limit": request.limit,
        "equipment_id": request.equipment_id,
        "measurement_date_from": (
            request.measurement_date_from
        ),
        "measurement_date_to": (
            request.measurement_date_to
        ),
        "chunk_types": request.chunk_types,
    }

    try:
        graph_result = graph.invoke(
            graph_input
        )

    except RagSearchQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except (
        RagSearchEmbeddingError,
        AzureOpenAIServiceError,
    ) as exc:
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

    sources = [
        RagChatSourceResponse(
            report_chunk_id=source["report_chunk_id"],
            report_id=source["report_id"],
            chunk_type=source["chunk_type"],
            equipment_id=source["equipment_id"],
            measurement_date=source["measurement_date"],
            similarity=source["similarity"],
        )
        for source in graph_result["sources"]
    ]

    return RagChatResponse(
        query=graph_result["query"],
        answer=graph_result["answer"],
        source_count=len(sources),
        sources=sources,
    )
