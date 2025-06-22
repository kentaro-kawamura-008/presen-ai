def get_auto_compose_prompt(
    presentation_goal: str,
    audience_profile: dict,
    config_options_yaml_str: str
) -> str:
    """「AIにおまかせ編成」のためのプロンプトを生成する。"""
    return f"""
あなたは賢明なプロジェクトマネージャーです。
以下のプレゼン目的と聴衆情報に最も適したAIレビューチームの編成を提案してください。
各エージェントについて、提示された選択肢の中から最も効果的だと思われるものの`id`を1つだけ選んでください。
例えば、経営層向けの重要な意思決定プレゼンなら「辛口批評モード」や「懐疑的な聴衆」が適しているかもしれません。
逆に、社内の中間報告であれば「寄り添いモード」や「初心者な聴衆」が適切かもしれません。
目的と聴衆の特性をよく考慮して、最適な組み合わせを選択してください。

回答は必ずJSON形式で、キーはエージェントの種別(YAMLのトップレベルキー)、バリューは選択したoptionの`id`としてください。
説明や前置きは一切不要です。JSONオブジェクトのみを出力してください。

# プレゼン目的
{presentation_goal}

# 聴衆情報
{audience_profile}

# 設定可能な選択肢 (YAML形式)
```yaml
{config_options_yaml_str}
```

# 回答フォーマット (JSONのみを出力すること)
{{
  "logic_critic": "id_of_choice",
  "audience_persona": "id_of_choice",
  "qna_generator": "id_of_choice"
}}
"""