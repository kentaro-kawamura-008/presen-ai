import yaml
from typing import Dict, Any, List
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config_options.yaml')

_config_cache: Dict[str, Any] = {}

def load_config_options() -> Dict[str, Any]:
    """
    agent_config_options.yamlを読み込み、内容を辞書として返す。
    一度読み込んだ内容はキャッシュする。
    """
    global _config_cache
    if not _config_cache:
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                _config_cache = yaml.safe_load(f)
        except FileNotFoundError:
            raise RuntimeError(f"設定ファイルが見つかりません: {CONFIG_PATH}")
        except yaml.YAMLError as e:
            raise RuntimeError(f"設定ファイルの解析に失敗しました: {e}")
    return _config_cache

def get_prompt_fragment(agent_type: str, selection_id: str) -> str:
    """
    指定されたエージェントタイプと選択IDに対応するプロンプト断片を取得する。
    
    Args:
        agent_type: エージェントの種類 (例: "logic_critic")。
        selection_id: ユーザーが選択した方針のID (例: "strict")。

    Returns:
        対応するプロンプト断片の文字列。
    """
    config = load_config_options()
    try:
        options: List[Dict[str, Any]] = config['agent_options'][agent_type]['options']
        for option in options:
            if option['id'] == selection_id:
                return option.get('prompt_fragment', '')
        return ""
    except KeyError:
        return ""
