from typing import Dict, List
from google.adk.agents import BaseAgent, SequentialAgent, ParallelAgent
from adk_logic.agents.document_analyzer_agent import create_document_analyzer_agent
from adk_logic.agents.logic_critic_agent import create_logic_critic_agent
from adk_logic.agents.audience_persona_agent import create_audience_persona_agent
from adk_logic.agents.report_synthesizer_agent import create_report_synthesizer_agent
from adk_logic.agents.qna_generator_agent import create_qna_generator_agent
from adk_logic.callbacks import BeforeAgentCallback

def create_root_agent(selected_configs: Dict[str, str], progress_notifier: BeforeAgentCallback) -> SequentialAgent:
    """
    ユーザーの選択設定に基づき、ワークフロー全体を制御するRootSequentialAgentを動的に生成する。
    """
    sub_agents: List[BaseAgent] = []

    # 1. 資料解析エージェントは常に実行
    sub_agents.append(create_document_analyzer_agent(before_agent_callback=progress_notifier))

    # 2. 2つのレビューエージェントを並列実行
    # (参照: docs/agents/workflow-agents/parallel-agents.md)
    reviewer_agents = [
        create_logic_critic_agent(selected_configs.get("logic_critic", "supportive"), before_agent_callback=progress_notifier),
        create_audience_persona_agent(selected_configs.get("audience_persona", "newbie"), before_agent_callback=progress_notifier)
    ]
    parallel_reviewer = ParallelAgent(
        name="ReviewerParallelAgent",
        sub_agents=reviewer_agents,
        before_agent_callback=progress_notifier
    )
    sub_agents.append(parallel_reviewer)

    # 3. レポート統合エージェントを実行
    sub_agents.append(create_report_synthesizer_agent(before_agent_callback=progress_notifier))
    
    # 4. Q&A生成が有効な場合のみ、Q&A生成エージェントを実行
    if selected_configs.get("qna_generator") == "enabled":
        sub_agents.append(create_qna_generator_agent(before_agent_callback=progress_notifier))

    # 最終的なワークフローをSequentialAgentとして構築
    # (参照: docs/agents/workflow-agents/sequential-agents.md)
    root_agent = SequentialAgent(
        name="PresentaAiRootAgent",
        sub_agents=sub_agents
    )
    
    return root_agent