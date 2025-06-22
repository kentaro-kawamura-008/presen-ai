# presenta_ai/adk_logic/callbacks.py (修正版)

from typing import Callable, Optional, Awaitable
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest

# ADKが要求するコールバック関数の型エイリアスを定義
BeforeAgentCallback = Optional[Callable[[CallbackContext], Awaitable[None]]]

def create_progress_notifier_callback(progress_callback: Optional[Callable[[str], None]]) -> BeforeAgentCallback:
    """
    UIに進捗を通知するための `before_agent_callback` 関数を生成する。
    この関数は、エージェントの実行前に特定のメッセージをUIに送信します。
    (参照: docs/callbacks/types-of-callbacks.md)

    Args:
        progress_callback: UIのテキストを更新するための同期関数。

    Returns:
        ADKエージェントに渡すことができる非同期の`before_agent_callback`関数。
        progress_callbackがNoneの場合はNoneを返す。
    """
    if not progress_callback:
        return None

    async def before_agent_callback(ctx: CallbackContext) -> None:
        """各エージェントの実行前にUIに進捗メッセージを送信する"""
        agent_name = ctx.agent.name
        message = ""
        
        # 現在のStateからユーザーの選択情報を取得
        # (参照: docs/sessions/state.md)
        selected_configs = ctx.session.state.get("selected_configs", {})

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
            progress_callback(message)

    return before_agent_callback

def get_mime_type(file_path: str) -> str:
    """ファイルパスからMIMEタイプを推測する。PPTXにも対応。"""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        if file_path.lower().endswith('.pptx'):
            return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        # 不明な場合は汎用的なMIMEタイプを返す
        return 'application/octet-stream'
    return mime_type


async def add_document_to_request_callback(
    context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    StateからGCSファイルパスを取得し、LLMリクエストにファイルパートとして追加する。
    このコールバックは before_model_callback として使用される。
    戻り値としてNoneを返すと、変更が適用されたllm_requestで処理が続行される。
    """
    logger.info("Executing add_document_to_request_callback...")
    gcs_file_path = context.state.get("gcs_file_path")

    if not gcs_file_path or not isinstance(gcs_file_path, str):
        logger.warning(
            "gcs_file_path not found or invalid in state. Skipping file attachment. "
            f"State: {context.state}"
        )
        return None  # 何もせず処理を続行

    logger.info(f"Found gcs_file_path: {gcs_file_path}")

    try:
        # GCS URIからファイルパートを作成
        mime_type = get_mime_type(gcs_file_path)
        file_part = Part.from_uri(uri=gcs_file_path, mime_type=mime_type)

        # LlmRequestのpartsリストにファイルパートを追加
        if llm_request.contents and llm_request.contents[0].parts:
            # 既存のプロンプトにファイルを追加
            llm_request.contents[0].parts.append(file_part)
            logger.info("Successfully appended file part to LLM request.")
        else:
            # リクエストが空の場合のフォールバック
            logger.warning("llm_request.contents was empty. Reconstructing request.")
            text_part = Part.from_text(context.agent.instruction)
            llm_request.contents = [text_part, file_part]

    except Exception as e:
        logger.error(f"Error creating or appending file part: {e}", exc_info=True)
        # エラー発生時は何もしない（あるいはエラーをStateに記録する）

    # `None`を返すことで、変更された`llm_request`で処理が続行される
    return None