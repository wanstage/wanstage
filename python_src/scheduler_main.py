import logging

from account import get_user_plan
from agent_loop import run_agent  # ← 安定化済みのエージェントを呼ぶ
from free_quota import can_use_post
from input_module import safe_load_brand_config
from notify_utils import notify

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def job_post_cycle(user_id: str = "default_user"):
    cfg = safe_load_brand_config()
    brand = cfg.get("brand_name", "default_brand")
    log.debug("brand=%s cfg_keys=%s", brand, list(cfg.keys()))

    # --- 無料枠チェック ---
    if not can_use_post(user_id):
        msg = f"🚫 無料枠到達: user={user_id} plan={get_user_plan(user_id)}"
        notify(msg, "WANSTAGE quota")
        log.warning(msg)
        return {"ok": False, "reason": "quota"}

    # --- エージェント実行（内部で429/503/非JSONに強化済み）---
    try:
        result = run_agent(user_id=user_id)
    except Exception as e:
        msg = f"❌ Agent 実行失敗: {e}"
        notify(msg, "WANSTAGE agent error")
        log.exception("run_agent failed")
        return {"ok": False, "reason": "agent_error"}

    # run_agent は {"ok": True/False, ...} を返す想定
    if isinstance(result, dict) and result.get("ok") is True:
        log.info("Agent succeeded: %s", result)
    else:
        warn = f"⚠️ Agent 応答異常: {result}"
        notify(warn, "WANSTAGE agent warning")
        log.warning(warn)

    return result


if __name__ == "__main__":
    print("job_post_cycle ->", job_post_cycle())
