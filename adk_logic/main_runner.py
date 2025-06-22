from typing import Callable, Dict, Any, Optional
import logging
from google import genai
from google.genai import types


from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from adk_logic.root_agent_factory import create_root_agent
from adk_logic.callbacks import create_progress_notifier_callback
from adk_logic.state_models import PresentaAiState, FinalReport, AudienceProfile

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# RunnerとSessionServiceはシングルトンとして管理
_runner_instance: Optional[Runner] = None

def get_runner() -> Runner:
    """Runnerのシングルトンインスタンスを取得する"""
    global _runner_instance
    if _runner_instance is None:
        _runner_instance = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            session_service=InMemorySessionService(),
        )
    return _runner_instance

async def run_review_process(
    gcs_file_path: str,
    presentation_goal: str,
    audience_profile: Dict[str, str],
    selected_configs: Dict[str, str],
    progress_callback: Callable[[str], None],
) -> Dict[str, Any]:
    """
    プレゼンレビューの全プロセスを実行する。

    Args:
        gcs_file_path: GCS上のファイルパス。
        presentation_goal: プレゼンの目的。
        audience_profile: 聴衆のプロファイル。
        selected_configs: ユーザーが選択したチーム編成設定。
        progress_callback: UIに進捗を伝えるコールバック関数。

    Returns:
        レビュー結果を含む辞書。
    """
    app_name = "presenta-ai"
    user_id = "default-user"
    
     # ハッカソン向けに固定

    # 1. UIの進捗通知コールバックをADKコールバックにラップ
    progress_notifier = create_progress_notifier_callback(progress_callback)
    
    # 2. 実行ごとに特化したRootAgentを動的に生成
    root_agent = create_root_agent(selected_configs, progress_notifier=progress_notifier)
    runner = Runner(
        app_name=app_name, 
        session_service=InMemorySessionService(),
        agent=root_agent)
    runner.agent = root_agent # Runnerに今回のワークフローを設定

    # 3. セッションを開始し、初期Stateを設定
    # (参照: docs/sessions/state.md)
    initial_state = PresentaAiState(
        gcs_file_path=gcs_file_path,
        presentation_goal=presentation_goal,
        audience_profile=AudienceProfile(**audience_profile),
        selected_configs=selected_configs
    ).model_dump()
    
    try:
        session = await runner.session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            state=initial_state,
        )
        logging.info(f"セッション開始: {session.id}, チーム編成: {selected_configs}")
        progress_callback("レビューチームの編成が完了しました。レビューを開始します！")

        content = types.Content(role='user', parts=[types.Part(text="プレゼン資料のレビューをお願いします。")])

        # 4. ADK Runnerでエージェントを実行
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content

        ):
            # イベントごとのロギング（デバッグ用）
            if event.content and event.content.parts:
                logging.info(f"Event from {event.author}: {event.content.parts[0].text[:100]}...")
            elif event.get_function_calls():
                 logging.info(f"Event from {event.author}: FunctionCall {event.get_function_calls()[0].name}")


        # 5. 最終的なStateから結果を取得
        final_session = await runner.session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session.id
        )
        final_report_data = final_session.state.get("final_report")

        if not final_report_data:
            logging.error("最終レポートが生成されませんでした。")
            raise RuntimeError("レビュープロセスの最終結果を生成できませんでした。")

        final_report = FinalReport.model_validate(final_report_data)
        logging.info("レビュープロセス正常終了。")
        progress_callback("レビューが完了しました！🎉")
        
        return final_report.model_dump()

    except Exception as e:
        logging.exception("レビュープロセス中に予期せぬエラーが発生しました。")
        progress_callback(f"エラーが発生しました: {e}")
        # UIに返すためのエラー構造
        return {"error": str(e)}
    