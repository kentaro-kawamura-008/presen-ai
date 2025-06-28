from google.adk.agents import LlmAgent
from adk_logic.prompts.base_prompts import REPORT_SYNTHESIZER_BASE_PROMPT
from adk_logic.state_models import PresentaAiState, FinalReport
from adk_logic.callbacks import before_agent_callback

def create_report_synthesizer_agent() -> LlmAgent:
    """2つのレビューを統合して最終レポートを生成するエージェント"""
    return LlmAgent(
        name="ReportSynthesizerAgent",
        model="gemini-2.5-pro",
        instruction=REPORT_SYNTHESIZER_BASE_PROMPT,
        input_schema=PresentaAiState,
        output_schema=FinalReport,
        before_agent_callback=before_agent_callback,
        output_key="final_report"
    )