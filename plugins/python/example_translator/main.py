"""
AetherLyric 範例 Python 歌詞翻譯外掛 (Example Translator Plugin)
授權條款：MIT License
"""
from typing import List, Dict, Any, Optional


class ExampleTranslator:
    """
    標準歌詞翻譯器外掛範例類別。
    提供 translate() 與 translate_lines() 方法，接收歌詞並回傳雙語翻譯結果。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.target_lang = self.config.get("target_lang", "zh-TW")

    def translate(self, text: str, target_lang: Optional[str] = None) -> str:
        """
        翻譯單行純文字歌詞。
        """
        lang = target_lang or self.target_lang
        if not text or not text.strip():
            return ""
        # 示範性翻譯前綴標記，實際外掛可在此調用合法對應的翻譯 API
        return f"[{lang}] {text}"

    def translate_lines(
        self, lines: List[Dict[str, Any]], target_lang: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批次翻譯時間軸歌詞段落清單。
        lines 格式範例：[{"time": "00:12.34", "text": "Hello world"}]
        """
        lang = target_lang or self.target_lang
        translated_lines = []
        for item in lines:
            original_text = item.get("text", "")
            trans_text = self.translate(original_text, lang)
            translated_lines.append(
                {
                    "time": item.get("time", ""),
                    "original": original_text,
                    "translation": trans_text,
                }
            )
        return translated_lines
