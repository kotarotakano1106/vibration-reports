"""検索・コンテキスト作成・回答生成を担当するRAG Node。"""

from backend.src.prompts.rag_chat_prompt import (
    NO_SEARCH_RESULTS_ANSWER,
    RAG_CHAT_INSTRUCTIONS,
    build_rag_chat_input,
)
from backend.src.services.azure_openai_service import (
    AzureOpenAIService,
)
from backend.src.services.rag_search_service import (
    RagSearchService,
)
from backend.src.workflows.states.chat_state import (
    ChatSearchResult,
    ChatSource,
    ChatState,
)


class RagNodes:
    """RAGチャットワークフローで使用するNode群。"""

    def __init__(
        self,
        session,
        rag_search_service=None,
        azure_openai_service=None,
    ):
        self._azure_openai_service = (
            azure_openai_service
            if azure_openai_service is not None
            else AzureOpenAIService()
        )
        self._rag_search_service = (
            rag_search_service
            if rag_search_service is not None
            else RagSearchService(
                session,
                azure_openai_service=(
                    self._azure_openai_service
                ),
            )
        )

    def search_report_chunks(
        self,
        state: ChatState,
    ) -> dict:
        """質問に類似する過去レポートチャンクを検索する。"""

        results = self._rag_search_service.search(
            query=state["query"],
            limit=state["limit"],
            equipment_id=state["equipment_id"],
            measurement_date_from=(
                state["measurement_date_from"]
            ),
            measurement_date_to=(
                state["measurement_date_to"]
            ),
            chunk_types=state["chunk_types"],
        )

        search_results: list[ChatSearchResult] = []
        for result in results:
            chunk = result.report_chunk
            search_results.append(
                {
                    "report_chunk_id": chunk.id,
                    "report_id": chunk.report_id,
                    "chunk_index": chunk.chunk_index,
                    "chunk_type": chunk.chunk_type,
                    "content": chunk.content,
                    "equipment_id": chunk.equipment_id,
                    "measurement_date": chunk.measurement_date,
                    "distance": result.distance,
                    "similarity": result.similarity,
                    "metadata_json": chunk.metadata_json or {},
                }
            )

        return {
            "search_results": search_results,
            "has_search_results": bool(search_results),
        }

    def build_context(
        self,
        state: ChatState,
    ) -> dict:
        """検索結果を生成AIへ渡すコンテキストへ整形する。"""

        context_blocks = []
        for index, result in enumerate(
            state["search_results"],
            start=1,
        ):
            measurement_date = (
                str(result["measurement_date"])
                if result["measurement_date"] is not None
                else "未設定"
            )
            context_blocks.append(
                "\n".join(
                    [
                        f"[参照{index}]",
                        f"レポートID: {result['report_id']}",
                        f"チャンク種別: {result['chunk_type']}",
                        f"設備ID: {result['equipment_id']}",
                        f"測定日: {measurement_date}",
                        f"類似度: {result['similarity']:.6f}",
                        "内容:",
                        result["content"],
                    ]
                )
            )

        return {
            "context": "\n\n".join(context_blocks),
        }

    def generate_answer(
        self,
        state: ChatState,
    ) -> dict:
        """検索結果を根拠に回答文を生成する。"""

        input_text = build_rag_chat_input(
            query=state["query"],
            context=state["context"],
        )
        answer = self._azure_openai_service.generate_text(
            instructions=RAG_CHAT_INSTRUCTIONS,
            input_text=input_text,
            max_output_tokens=1000,
        )

        return {"answer": answer}

    def build_no_results_answer(
        self,
        state: ChatState,
    ) -> dict:
        """検索結果がない場合の固定回答を返す。"""

        return {
            "answer": NO_SEARCH_RESULTS_ANSWER,
            "sources": [],
        }

    def build_sources(
        self,
        state: ChatState,
    ) -> dict:
        """検索結果から回答の参照元一覧を作成する。"""

        sources: list[ChatSource] = []
        seen_chunk_ids = set()

        for result in state["search_results"]:
            chunk_id = result["report_chunk_id"]
            if chunk_id in seen_chunk_ids:
                continue

            seen_chunk_ids.add(chunk_id)
            sources.append(
                {
                    "report_chunk_id": chunk_id,
                    "report_id": result["report_id"],
                    "chunk_type": result["chunk_type"],
                    "equipment_id": result["equipment_id"],
                    "measurement_date": result[
                        "measurement_date"
                    ],
                    "similarity": result["similarity"],
                }
            )

        return {"sources": sources}


def route_after_search(state: ChatState) -> str:
    """検索結果の有無に応じて次のNode名を返す。"""

    if state.get("has_search_results", False):
        return "build_context"

    return "build_no_results_answer"
