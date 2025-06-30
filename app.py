import streamlit as st
import os
import uuid
import json
import asyncio
from typing import Dict, Any
from google import genai
from google.genai import types

from google.cloud import storage
from google.api_core.exceptions import GoogleAPICallError
import vertexai
from vertexai.generative_models import GenerativeModel

from utils.config_loader import load_config_options
from adk_logic.prompts.auto_compose_prompt import get_auto_compose_prompt
from adk_logic.main_runner import run_review_process

from dotenv import load_dotenv
load_dotenv()

# --- Streamlit ページ設定 ---
st.set_page_config(page_title="Presenta-AI", page_icon="🤖", layout="wide")

# --- 定数と設定 ---
# NOTE: Cloud Runで実行する場合、これらの値は環境変数から取得するのが望ましい
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")

# --- 状態管理の初期化 ---
if 'page' not in st.session_state:
    st.session_state.page = 'input'
if 'gcs_file_path' not in st.session_state:
    st.session_state.gcs_file_path = None
if 'review_result' not in st.session_state:
    st.session_state.review_result = None
if 'selected_configs' not in st.session_state:
    st.session_state.selected_configs = {}
if 'error_message' not in st.session_state:
    st.session_state.error_message = None

print("dbg1")

# --- ヘルパー関数 ---
# def init_vertexai():
#     """Vertex AIを初期化"""
#     try:
#         print("dbg2")
#         if GCP_PROJECT_ID and GCS_BUCKET_NAME:
#             print("dbg3")
#             client = genai.Client(vertexai=True,
#                     project=GCP_PROJECT_ID, location=GCP_LOCATION,
#                     http_options=HttpOptions(api_version='v1'))
#             return True
#     except Exception as e:
#         st.session_state.error_message = f"Vertex AIの初期化に失敗しました: {e}"
#     return False



def upload_to_gcs(uploaded_file) -> str:
    """アップロードされたファイルをGCSに保存し、GCSパスを返す"""
    if not GCS_BUCKET_NAME:
        st.error("GCSバケット名が設定されていません。環境変数 GCS_BUCKET_NAME を設定してください。")
        return ""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        file_name = f"uploads/{uuid.uuid4()}-{uploaded_file.name}"
        blob = bucket.blob(file_name)
        
        blob.upload_from_file(uploaded_file)
        gcs_path = f"gs://{GCS_BUCKET_NAME}/{file_name}"
        return gcs_path
    except GoogleAPICallError as e:
        st.error(f"GCSへのアップロードに失敗しました: {e}。GCSバケットが存在し、サービスアカウントに書き込み権限があるか確認してください。")
        return ""
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")
        return ""

@st.cache_data
def get_config():
    """設定ファイルをキャッシュして読み込む"""
    return load_config_options()

async def get_auto_composed_config(goal, audience, config_yaml_str):
    """LLMに最適なチーム編成を問い合わせる"""

    prompt = get_auto_compose_prompt(goal, audience, config_yaml_str)
    response = await client.aio.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            response_mime_type='application/json'
            # response_schema=response_schema,
        )
    )
    
    try:
        # LLMの出力からJSON部分を抽出
        json_str = response.text.strip().lstrip("```json").rstrip("```")
        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError) as e:
        st.error(f"AIによる編成案の解析に失敗しました: {e}\nLLMからの応答: {response.text}")
        return None

# --- UI描画関数 ---

def draw_input_page():
    """入力画面を描画する"""
    st.header("1. プレゼン情報を入力")
    
    with st.form("input_form"):
        st.session_state.uploaded_file = st.file_uploader(
            "レビューしてほしいプレゼン資料をアップロードしてください",
            type=['pptx', 'pdf']
        )
        st.session_state.presentation_goal = st.text_area(
            "このプレゼンの目的は何ですか？",
            placeholder="例：新規事業「Project X」の予算承認を得て、開発キックオフに繋げること。",
            height=100
        )
        # st.session_state.presentation_goal = "上手なプレゼンテーションのためのコツの紹介"
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.audience_role = st.text_input(
                "主な聴衆の役職や立場は？",
                placeholder="例：部長クラスの意思決定者、技術部門のマネージャー"
            )
            #  st.session_state.audience_role = "プレゼンテーションを控える若者"
        with col2:
            st.session_state.audience_interests = st.text_input(
                "聴衆の主な関心事や知識レベルは？",
                placeholder="例：事業のROIと市場性。技術的な詳細にはあまり詳しくない。"
            )
            # st.session_state.audience_interests = "プレゼンテーション初心者"
            
        print("dbg2")
        
        submitted = st.form_submit_button("レビューチームを編成する →", type="primary")

        print("dbg3")

        if submitted:
            if not st.session_state.uploaded_file:
                st.error("資料ファイルをアップロードしてください。")
            elif not st.session_state.presentation_goal:
                st.error("プレゼンの目的を入力してください。")
            elif not st.session_state.audience_role or not st.session_state.audience_interests:
                st.error("聴衆の情報を入力してください。")
            else:
                with st.spinner("資料を安全にアップロード中..."):
                    gcs_path = upload_to_gcs(st.session_state.uploaded_file)
                    if gcs_path:
                        st.session_state.gcs_file_path = gcs_path
                        st.session_state.page = 'compose'
                        st.rerun()
        print("dbg4")

def draw_compose_page():
    """AIレビューチーム編成画面を描画する"""
    st.header("2. AIレビューチームを編成")

    # ユーザー入力をサイドバーに表示
    with st.sidebar:
        st.subheader("プレゼン概要")
        st.info(f"**目的:**\n{st.session_state.presentation_goal}")
        st.info(f"**聴衆:**\n{st.session_state.audience_role} ({st.session_state.audience_interests})")
        st.button("← 入力に戻る", on_click=lambda: st.session_state.update(page='input'))

    config = get_config()

    if st.button("🤖 AIにおまかせ編成"):
        with st.spinner("あなたに最適なチームをAIが編成中..."):
            goal = st.session_state.presentation_goal
            audience = {"role": st.session_state.audience_role, "interests": st.session_state.audience_interests}
            config_str = json.dumps(config, ensure_ascii=False)
            
            # 非同期関数を実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            recommended_configs = loop.run_until_complete(get_auto_composed_config(goal, audience, config_str))
            loop.close()

            if recommended_configs:
                st.session_state.selected_configs = recommended_configs
                st.success("AIによるチーム編成が完了しました！")
                st.rerun()
            else:
                st.error("AIによる編成に失敗しました。手動で選択してください。")


    st.markdown("---")
    
    cols = st.columns(len(config['agent_options']))
    
    for i, (agent_type, details) in enumerate(config['agent_options'].items()):
        with cols[i]:
            st.subheader(details['name'])
            st.caption(details['description'])
            
            options_labels = [opt['label'] for opt in details['options']]
            options_ids = [opt['id'] for opt in details['options']]
            
            # 現在の選択を取得
            current_selection_id = st.session_state.selected_configs.get(agent_type)
            try:
                current_index = options_ids.index(current_selection_id) if current_selection_id in options_ids else 0
            except ValueError:
                current_index = 0

            # ラジオボタンで選択
            selected_label = st.radio(
                "レビュー方針を選択",
                options_labels,
                index=current_index,
                key=f"radio_{agent_type}",
                label_visibility="collapsed"
            )
            
            # 選択されたIDを保存
            selected_id = options_ids[options_labels.index(selected_label)]
            st.session_state.selected_configs[agent_type] = selected_id
            
            # 選択肢の説明を表示
            for opt in details['options']:
                if opt['label'] == selected_label:
                    st.info(opt['description'])
                    break
    
    st.markdown("---")
    if st.button("🚀 このチームでレビュー開始", type="primary", use_container_width=True):
        st.session_state.page = 'running'
        st.rerun()


def draw_running_page():
    """実行中画面を描画する"""
    st.header("3. AIレビュー実行中...")
    st.info("AIチームがあなたのプレゼン資料を多角的にレビューしています。完了まで数分かかることがあります。")
    
    progress_bar = st.progress(0, text="レビューを開始しています...")
    progress_text = st.empty()

    def update_progress(message: str):
        # この関数は別スレッドから呼ばれる可能性があるため、UI更新は慎重に
        # 簡単な実装としてテキストを更新する
        progress_text.info(message)
        # NOTE: より洗練された進捗更新は、エージェントの数に基づいてバーを動かす
        # ここでは単純化のため、テキスト更新のみ
    
    # ADKロジックを非同期で実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    audience_profile = {
        "role": st.session_state.audience_role,
        "interests": st.session_state.audience_interests
    }

    try:
        result = loop.run_until_complete(run_review_process(
            gcs_file_path=st.session_state.gcs_file_path,
            presentation_goal=st.session_state.presentation_goal,
            audience_profile=audience_profile,
            selected_configs=st.session_state.selected_configs,
            progress_callback=update_progress
        ))
        st.session_state.review_result = result
        st.session_state.page = 'result'
    except Exception as e:
        st.session_state.error_message = f"レビュープロセスでエラーが発生しました: {e}"
        st.session_state.page = 'error'
    finally:
        loop.close()
        st.rerun()


def draw_result_page():
    """結果表示画面を描画する"""
    st.header("4. レビュー結果")
    
    result = st.session_state.review_result
    if not result or result.get("error"):
        st.error(f"レビュー結果の取得に失敗しました: {result.get('error', '不明なエラー')}")
        if st.button("最初からやり直す"):
            st.session_state.clear()
            st.rerun()
        return

    # タブで結果を表示
    tab1, tab2, tab3 = st.tabs(["📊 総合評価", "📄 スライドごと評価", "❓ 想定問答"])

    with tab1:
        st.subheader("全体サマリー")
        st.success(result.get('summary_review', 'N/A'))
        st.subheader("構成・ストーリーライン")
        st.write(result.get('storyline_review', 'N/A'))

    with tab2:
        st.subheader("スライドごとの詳細レビュー")
        reviews = result.get('slide_by_slide_reviews', [])
        if not reviews:
            st.info("スライドごとのレビューはありません。")
        for review in reviews:
            with st.expander(f"**スライド {review.get('slide_number')}**"):
                st.markdown("##### 評価")
                st.write(review.get('evaluation', 'N/A'))
                st.markdown("##### 改善提案")
                st.warning(review.get('suggestion', 'N/A'))

    with tab3:
        st.subheader("想定される質疑応答 (Q&A)")
        qna_list = result.get('qna_list', [])
        if not qna_list:
            st.info("想定問答は生成されていません。（設定で無効になっている可能性があります）")
        for i, qna in enumerate(qna_list):
            st.markdown(f"**Q{i+1}: {qna.get('question', 'N/A')}**")
            st.info(f"A: {qna.get('answer', 'N/A')}")
            st.markdown("---")

    if st.button("別のプレゼンをレビューする", type="primary"):
        # 状態をクリアして最初のページに戻る
        st.session_state.clear()
        st.rerun()

def draw_error_page():
    """エラー画面"""
    st.error(f"エラーが発生しました: {st.session_state.error_message}")
    if st.button("最初からやり直す"):
        st.session_state.clear()
        st.rerun()

# --- メインロジック ---
st.title("🤖 AIプレゼンレビューアプリ「Presenta-AI」")

# GCP/Vertex AIの初期化チェック
# if not init_vertexai():
#     st.error("GCPプロジェクトまたはGCSバケットが設定されていません。環境変数を確認してください。")
#     st.stop()
client = genai.Client(vertexai=True,
                    project=GCP_PROJECT_ID, location=GCP_LOCATION)

# ページルーター
if st.session_state.page == 'input':
    draw_input_page()
elif st.session_state.page == 'compose':
    draw_compose_page()
elif st.session_state.page == 'running':
    draw_running_page()
elif st.session_state.page == 'result':
    draw_result_page()
elif st.session_state.page == 'error':
    draw_error_page()