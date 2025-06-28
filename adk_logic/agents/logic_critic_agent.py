from google.adk.agents import LlmAgent
from utils.config_loader import get_prompt_fragment
from adk_logic.prompts.base_prompts import LOGIC_CRITIC_BASE_PROMPT
from adk_logic.state_models import PresentaAiState
from adk_logic.callbacks import before_agent_callback

def create_logic_critic_agent(selection_id: str) -> LlmAgent:
    """ユーザーの選択に基づいてLogicCriticAgentを生成する"""
    prompt_fragment = get_prompt_fragment('logic_critic', selection_id)
    final_instruction = f"{LOGIC_CRITIC_BASE_PROMPT}\n\n# あなたの今回のレビュー方針\n{prompt_fragment}"

    return LlmAgent(
        name="LogicCriticAgent",
        model="gemini-2.5-pro",
        instruction=final_instruction,
        input_schema=PresentaAiState, # Stateから値を取得するためのスキーマ
        output_key="logic_critic_review_text",
        before_agent_callback=before_agent_callback
    )
