"""過去レポートを検索して回答するRAGチャットGraph。"""

from langgraph.graph import END, START, StateGraph

from backend.src.workflows.nodes.rag_nodes import (
    RagNodes,
    route_after_search,
)
from backend.src.workflows.states.chat_state import (
    ChatInputState,
    ChatOutputState,
    ChatState,
)


def build_rag_chat_graph(
    session,
    *,
    rag_search_service=None,
    azure_openai_service=None,
):
    """依存関係を注入し、RAGチャットGraphを構築する。"""

    rag_nodes = RagNodes(
        session=session,
        rag_search_service=rag_search_service,
        azure_openai_service=azure_openai_service,
    )

    graph = StateGraph(
        ChatState,
        input_schema=ChatInputState,
        output_schema=ChatOutputState,
    )

    graph.add_node(
        "search_report_chunks",
        rag_nodes.search_report_chunks,
    )
    graph.add_node(
        "build_context",
        rag_nodes.build_context,
    )
    graph.add_node(
        "generate_answer",
        rag_nodes.generate_answer,
    )
    graph.add_node(
        "build_sources",
        rag_nodes.build_sources,
    )
    graph.add_node(
        "build_no_results_answer",
        rag_nodes.build_no_results_answer,
    )

    graph.add_edge(
        START,
        "search_report_chunks",
    )

    graph.add_conditional_edges(
        "search_report_chunks",
        route_after_search,
        {
            "build_context": "build_context",
            "build_no_results_answer": (
                "build_no_results_answer"
            ),
        },
    )

    graph.add_edge(
        "build_context",
        "generate_answer",
    )
    graph.add_edge(
        "generate_answer",
        "build_sources",
    )
    graph.add_edge(
        "build_sources",
        END,
    )
    graph.add_edge(
        "build_no_results_answer",
        END,
    )

    return graph.compile()
