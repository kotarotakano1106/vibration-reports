"""CSV分析・AIレポート生成ワークフローのLangGraph定義。"""

from itertools import pairwise

from langgraph.graph import END, START, StateGraph

from backend.src.workflows.nodes.analysis_nodes import AnalysisNodes
from backend.src.workflows.nodes.report_nodes import ReportNodes
from backend.src.workflows.states.analysis_state import (
    AnalysisInputState,
    AnalysisOutputState,
    AnalysisState,
)


def build_analysis_graph(
    session,
    *,
    csv_service=None,
    analysis_service=None,
    azure_openai_service=None,
):
    """依存関係を注入し、分析ワークフローを構築する。"""

    analysis_nodes = AnalysisNodes(
        session=session,
        csv_service=csv_service,
        analysis_service=analysis_service,
        azure_openai_service=azure_openai_service,
    )
    report_nodes = ReportNodes(
        session=session,
        azure_openai_service=azure_openai_service,
    )

    graph = StateGraph(
        AnalysisState,
        input_schema=AnalysisInputState,
        output_schema=AnalysisOutputState,
    )

    nodes = {
        "load_uploaded_file": analysis_nodes.load_uploaded_file,
        "check_existing_report": analysis_nodes.check_existing_report,
        "mark_processing": analysis_nodes.mark_processing,
        "load_and_validate_csv": analysis_nodes.load_and_validate_csv,
        "analyze_vibration": analysis_nodes.analyze_vibration,
        "generate_ai_analysis": analysis_nodes.generate_ai_analysis,
        "build_report_content": report_nodes.build_report_content,
        "save_report": report_nodes.save_report,
        "build_report_chunks": report_nodes.build_report_chunks,
        "generate_chunk_embeddings": (
            report_nodes.generate_chunk_embeddings
        ),
        "save_report_chunks": report_nodes.save_report_chunks,
        "mark_completed": report_nodes.mark_completed,
    }
    for name, node in nodes.items():
        graph.add_node(name, node)

    workflow = [
        "load_uploaded_file",
        "check_existing_report",
        "mark_processing",
        "load_and_validate_csv",
        "analyze_vibration",
        "generate_ai_analysis",
        "build_report_content",
        "save_report",
        "build_report_chunks",
        "generate_chunk_embeddings",
        "save_report_chunks",
        "mark_completed",
    ]

    graph.add_edge(START, workflow[0])
    for current, following in pairwise(workflow):
        graph.add_edge(current, following)
    graph.add_edge(workflow[-1], END)

    return graph.compile()
