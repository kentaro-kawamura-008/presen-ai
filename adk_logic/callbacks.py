# presenta_ai/adk_logic/callbacks.py (修正版)

from typing import Callable, Optional, Awaitable
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google import genai
from google.genai import types
from logging import getLogger
logger = getLogger(__name__)

# ADKが要求するコールバック関数の型エイリアスを定義
BeforeAgentCallback = Optional[Callable[[CallbackContext], Awaitable[None]]]

def before_agent_callback(callback_context: CallbackContext) -> None:
    """各エージェントの実行前にUIに進捗メッセージを送信する"""
    agent_name = callback_context.agent_name
    message = ""
    
    # 現在のStateからユーザーの選択情報を取得
    # (参照: docs/sessions/state.md)
    selected_configs = callback_context.state.get("selected_configs", {})

    if agent_name == "DocumentAnalyzerAgent":
        message = "プレゼン資料の解析を開始します... 📄"
    elif agent_name == "ReviewerParallelAgent":
        message = "各専門家による並行レビューを開始します... 👥"
    elif agent_name == "LogicCriticAgent":
        selection = selected_configs.get("logic_critic")
        mode = "辛口モード" if selection == "strict" else "寄り添いモード"
        message = f"ロジック批評家 ({mode}) がレビュー中です... 🤔"
    elif agent_name == "AudiencePersonaAgent":
        selection = selected_configs.get("audience_persona")
        mode = "懐疑的な聴衆" if selection == "skeptical" else "初心者な聴衆"
        message = f"聴衆ペルソナ ({mode}) がレビュー中です... 🧐"
    elif agent_name == "ReportSynthesizerAgent":
        message = "各レビューを統合し、最終レポートを作成しています... 📝"
    elif agent_name == "QnaGeneratorAgent":
        message = "想定問答集を生成しています... 💬"
    
    if message:
        # UIへの通知は同期待ち受けしない
        print(message)

    return None



def add_document_to_request_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    StateからGCSファイルパスを取得し、LLMリクエストにファイルパートとして追加する。
    このコールバックは before_model_callback として使用される。
    戻り値としてNoneを返すと、変更が適用されたllm_requestで処理が続行される。
    """
    logger.info("Executing add_document_to_request_callback...")
    gcs_file_path = callback_context.state.get("gcs_file_path")

    if not gcs_file_path or not isinstance(gcs_file_path, str):
        logger.warning(
            "gcs_file_path not found or invalid in state. Skipping file attachment. "
            f"State: {callback_context.state}"
        )
        return None  # 何もせず処理を続行

    logger.info(f"Found gcs_file_path: {gcs_file_path}")

    try:
        # GCS URIからファイルパートを作成
        file_part = types.Part.from_uri(file_uri=gcs_file_path, mime_type="application/pdf")

        # LlmRequestのpartsリストにファイルパートを追加
        # 既存のプロンプトにファイルを追加
        llm_request.contents[0].parts.append(file_part)
        logger.info("Successfully appended file part to LLM request.")

    except Exception as e:
        logger.error(f"Error creating or appending file part: {e}", exc_info=True)
        # エラー発生時は何もしない（あるいはエラーをStateに記録する）

    # `None`を返すことで、変更された`llm_request`で処理が続行される
    return None