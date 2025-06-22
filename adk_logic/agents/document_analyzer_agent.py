from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from adk_logic.prompts.base_prompts import DOCUMENT_ANALYZER_INSTRUCTION
from adk_logic.tools.document_parser_tool import parse_presentation_document
from adk_logic.state_models import DocumentAnalysisResult
from adk_logic.callbacks import BeforeAgentCallback, add_document_to_request_callback


def create_document_analyzer_agent() -> LlmAgent:
    """資料解析ツールを実行し、結果をStateに保存するエージェントを生成"""
    return LlmAgent(
        name="DocumentAnalyzerAgent",
        model="gemini-2.5-pro", # ツール利用に適したモデル
        instruction=DOCUMENT_ANALYZER_INSTRUCTION,
        # tools=[FunctionTool(parse_presentation_document)],
        output_key="document_analysis", # 結果をStateの 'document_analysis' に保存
        before_agent_callback=add_document_to_request_callback,
        output_schema=DocumentAnalysisResult,
    )