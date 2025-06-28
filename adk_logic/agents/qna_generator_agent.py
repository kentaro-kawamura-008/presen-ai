from google.adk.agents import LlmAgent
from adk_logic.prompts.base_prompts import QNA_GENERATOR_BASE_PROMPT
from adk_logic.state_models import PresentaAiState, QnAPair, FinalReport
from typing import List
from adk_logic.callbacks import before_agent_callback

def create_qna_generator_agent() -> LlmAgent:
    """最終レポートから想定問答集を生成するエージェント"""
    
    # # このエージェントは最終レポートにQ&Aリストを追記する
    # async def update_final_report_with_qna(ctx, qna_list: List[QnAPair]):
    #     final_report_dict = ctx.session.state.get("final_report")
    #     if final_report_dict:
    #         final_report = FinalReport.model_validate(final_report_dict)
    #         final_report.qna_list = qna_list
    #         ctx.session.state["final_report"] = final_report.model_dump()
    
    return LlmAgent(
        name="QnaGeneratorAgent",
        model="gemini-2.5-pro",
        instruction=QNA_GENERATOR_BASE_PROMPT,
        input_schema=PresentaAiState,
        output_schema=QnAPair,
        # output_keyを使わず、カスタム関数でStateを更新する
        before_agent_callback=before_agent_callback,
    )