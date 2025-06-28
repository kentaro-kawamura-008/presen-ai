from google.adk.agents import LlmAgent
from utils.config_loader import get_prompt_fragment
from adk_logic.prompts.base_prompts import AUDIENCE_PERSONA_BASE_PROMPT
from adk_logic.state_models import PresentaAiState
from adk_logic.callbacks import before_agent_callback

def create_audience_persona_agent(selection_id: str) -> LlmAgent:
    """ユーザーの選択に基づいてAudiencePersonaAgentを生成する"""
    prompt_fragment = get_prompt_fragment('audience_persona', selection_id)
    final_instruction = f"{AUDIENCE_PERSONA_BASE_PROMPT}\n\n# あなたの今回のレビュー方針\n{prompt_fragment}"
    
    return LlmAgent(
        name="AudiencePersonaAgent",
        model="gemini-2.5-pro",
        instruction=final_instruction,
        input_schema=PresentaAiState,
        output_key="audience_persona_review_text",
        before_agent_callback=before_agent_callback
    )