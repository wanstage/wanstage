import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Tuple

from openai import OpenAI

log = logging.getLogger(__name__)


def safe_load_brand_config() -> Dict[str, Any]:
    # TODO: 本実装に置き換え
    return {}


def _fallback_plan(brand: str, channels: List[str]) -> Dict[str, Any]:
    return {"intent": "compose_post", "brand": brand, "channels": channels}


def tool_compose_and_post(plan: Dict[str, Any], user_id: str) -> str:
    return f"[compose_and_post simulated for {user_id}]"


def tool_research_stub(plan: Dict[str, Any]) -> str:
    return "[research simulated]"


def tool_analyze_metrics_stub(plan: Dict[str, Any]) -> str:
    return "[analyze_metrics simulated]"


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# -------------------- OpenAI クライアント --------------------
def _client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing")
    # SDK v1 系: OpenAI(api_key=...) でOK
    return OpenAI(api_key=key)


def _model_candidates() -> Tuple[str, str]:
    """
    優先: gpt-4o-mini（安定・低コスト）
    代替: gpt-4o     （互換）
    ※ .env があればそれを優先
    """
    primary = os.environ.get("OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
    fallback = os.environ.get("OPENAI_MODEL_FALLBACK", "gpt-4o")
    return primary, fallback


# -------------------- JSON 抽出ユーティリティ --------------------
def _extract_json(text: str) -> Dict[str, Any]:
    """
    返ってきたテキストから最初の { ... } ブロックを抜き出して JSON として読む。
    まるごと JSON の場合もそのまま読む。
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("empty text")

    # まずはストレートに
    try:
        return json.loads(text)
    except Exception:
        pass

    # テキスト内から最初の { と最後の } を拾う簡易抽出
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            return json.loads(snippet)
    except Exception:
        pass

    # よくあるコードフェンス ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if m:
        return json.loads(m.group(1))

    # ここまで失敗なら、デバッグ用に内容を見せて例外
    raise ValueError(f"non-JSON response: {repr(text[:240])}...")


def _read_text_from_response(r: Any) -> str:
    """
    SDKの shape 差分を吸収してテキストを取り出す。
    - r.output_text（新しめ）
    - r.output[0].content[0].text（旧互換）
    - どちらもなければ str(r)
    """
    t = getattr(r, "output_text", None)
    if t:
        return t
    try:
        return r.output[0].content[0].text
    except Exception:
        return str(r)


# -------------------- LLM 呼び出し（堅牢化） --------------------
def _ask_json(prompt: str) -> dict:
    import json
    import logging
    import re

    log = logging.getLogger(__name__)
    client = _client()
    models = [
        os.environ.get("OPENAI_MODEL_PRIMARY", "gpt-5"),
        os.environ.get("OPENAI_MODEL_FALLBACK", "gpt-4o-mini"),
    ]
    last_err = None
    for m in models:
        try:
            r = client.responses.create(model=m, input=prompt)
            text = getattr(r, "output_text", None)
            if text is None:
                try:
                    text = r.output[0].content[0].text
                except Exception:
                    text = ""
            text = (text or "").strip()
            # 1) 素直にJSONに見える？
            try:
                return json.loads(text)
            except Exception:
                pass
            # 2) ```json ... ``` から抽出
            mjson = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.I)
            if mjson:
                try:
                    return json.loads(mjson.group(1))
                except Exception:
                    pass
            # 3) 最後の手段：安全デフォルト（instagram/tiktokのどちらかでキャプション簡易生成）
            return {
                "intent": "compose_post",
                "post": {
                    "channel": "tiktok",
                    "caption": "✨新感覚の舞台体験、WanStageで心を揺さぶる瞬間を！ #WanStage",
                    "hashtags": ["wanstage"],
                },
            }
        except Exception as e:
            last_err = e
            log.warning("model=%s failed: %s", m, e)
            time.sleep(0.6)
            continue
    raise RuntimeError(f"OpenAI failed: {last_err}")


def run_agent(user_id: str = "default_user"):
    cfg = safe_load_brand_config()
    brand = cfg.get("brand_name", "WanStage")
    channels = cfg.get("channels", ["instagram", "tiktok"])

    # JSON-only を強制するプロンプト（説明文を出させない）
    prompt = (
        "あなたはSNS収益化エージェントです。以下の仕様で JSON だけを返答してください。\n"
        "- intent: 'compose_post' | 'research' | 'analyze_metrics'\n"
        "- compose_post の場合: post.caption, post.hashtags[], post.channel を必須\n"
        f"- brand: {brand}\n"
        f"- available_channels: {', '.join(channels)}\n"
        "- 日本語、宣伝臭を抑えて短く、新規フォロワー獲得志向\n"
        "返答は JSON のみ（コードブロックや説明文は禁止）。"
    )

    try:
        plan = _ask_json(prompt)
    except Exception as e:
        log.warning("LLM unstable -> local fallback used: %s", e)
        plan = _fallback_plan(brand, channels)

    intent = plan.get("intent", "")
    if intent == "compose_post":
        return tool_compose_and_post(plan, user_id)
    elif intent == "research":
        return tool_research_stub(plan)
    elif intent == "analyze_metrics":
        return tool_analyze_metrics_stub(plan)
    else:
        # 想定外でも compose に倒す
        plan = _fallback_plan(brand, channels)
        return tool_compose_and_post(plan, user_id)


if __name__ == "__main__":
    out = run_agent()
    print(out)
