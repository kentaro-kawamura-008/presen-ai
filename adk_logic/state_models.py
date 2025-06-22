from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AudienceProfile(BaseModel):
    """聴衆のプロファイル"""
    role: str = Field(description="聴衆の役職や立場")
    interests: str = Field(description="聴衆の主な関心事や知識レベル")

class SlideContent(BaseModel):
    """スライド1枚の内容"""
    slide_number: int
    text: str
    title: Optional[str] = None
    notes: Optional[str] = None

class DocumentAnalysisResult(BaseModel):
    """資料解析ツールの出力結果"""
    file_name: str
    total_slides: int
    slides: List[SlideContent]
    error: Optional[str] = None

class SlideReview(BaseModel):
    """スライド1枚ごとのレビュー結果"""
    slide_number: int
    evaluation: str
    suggestion: str

class QnAPair(BaseModel):
    """質疑応答のペア"""
    question: str
    answer: str

class FinalReport(BaseModel):
    """最終的なレビューレポート"""
    summary_review: str = Field(description="プレゼン全体に対する総評。")
    storyline_review: str = Field(description="構成やストーリーラインに対する詳細なレビュー。")
    slide_by_slide_reviews: List[SlideReview] = Field(description="各スライドに対する具体的な評価と改善案。")
    qna_list: Optional[List[QnAPair]] = Field(default=None, description="想定される質疑応答のリスト。")

class PresentaAiState(BaseModel):
    """ADKセッション全体で共有されるStateの構造"""
    # --- 初期入力 ---
    gcs_file_path: str = Field(description="GCS上のプレゼン資料のパス。")
    presentation_goal: str = Field(description="プレゼンテーションの目的。")
    audience_profile: AudienceProfile = Field(description="対象となる聴衆のプロファイル。")
    selected_configs: Dict[str, str] = Field(description="ユーザーが選択したAIレビューチームの編成設定。")

    # --- 中間生成物 ---
    document_analysis: Optional[DocumentAnalysisResult] = Field(default=None, description="資料解析エージェントによる解析結果。")
    logic_critic_review_text: Optional[str] = Field(default=None, description="ロジック批評家エージェントによる生レビューテキスト。")
    audience_persona_review_text: Optional[str] = Field(default=None, description="聴衆ペルソナエージェントによる生レビューテキスト。")

    # --- 最終成果物 ---
    final_report: Optional[FinalReport] = Field(default=None, description="最終的に生成されたレビューレポート。")
    
    # PydanticモデルをADKのStateとして利用可能にするための設定
    class Config:
        arbitrary_types_allowed = True