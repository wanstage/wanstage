import logging
import os
import time
from typing import Any, cast

from openai import OpenAI


def _get_first_text(resp: Any) -> str:
    try:
        # output[0].content[0].text を安全に取り出す
        return cast(Any, resp).output[0].content[0].text
    except Exception:
        return ""


log = logging.getLogger(__name__)


def gen_post_caption(prompt: str) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing")
    primary = os.environ.get("OPENAI_MODEL_PRIMARY", "gpt-5")
    fallback = os.environ.get("OPENAI_MODEL_FALLBACK", "gpt-4o-mini")
    client = OpenAI(api_key=key)

    models = [primary, fallback]
    last_err = None
    for m in models:
        try:
            r = client.responses.create(model=m, input=prompt)
            text = getattr(r, "output_text", None)
            if not text:
                # SDK差分の保険
                try:
                    text = r.output[0].content[0].text
                except Exception:
                    text = str(r)
            return text.strip()
        except Exception as e:
            last_err = e
            log.warning("model=%s failed: %s", m, e)
            # 429なら少し待って次へ
            if "429" in str(e) or "rate" in str(e).lower():
                time.sleep(1.2)
                continue
            # 401やその他でもフォールバック試行
            continue
    raise RuntimeError(f"OpenAI failed: {last_err}")
