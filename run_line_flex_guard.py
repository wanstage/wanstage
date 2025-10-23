#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import csv
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
LOGDIR = ROOT / "logs"
LOGDIR.mkdir(parents=True, exist_ok=True)
HISTCSV = LOGDIR / "lineflex_history.csv"


def ensure_csv_header(p: pathlib.Path):
    if not p.exists():
        p.write_text("timestamp,date,slot,title,status,message_id,error\n", encoding="utf-8")


def post_slack(text: str):
    url = os.environ.get("SLACK_WEBHOOK", "")
    if not url:
        return
    data = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            res.read()
    except Exception:
        pass  # 通知失敗は致命的でない


def already_sent_ok(date_str: str, slot: int) -> bool:
    if not HISTCSV.exists():
        return False
    try:
        with HISTCSV.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if (
                    r.get("date") == date_str
                    and int(r.get("slot", 0)) == slot
                    and r.get("status", "").startswith("OK")
                ):
                    return True
    except Exception:
        pass
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD")
    ap.add_argument("--slot", type=int, default=1)
    ap.add_argument("--force", action="store_true")
    args, rest = ap.parse_known_args()

    date_str = args.date or datetime.date.today().isoformat()

    # 送信済みガード
    if not args.force and already_sent_ok(date_str, args.slot):
        msg = f"[SKIP] {date_str} slot#{args.slot} は既にOK送信済みです（--force で強制可）。"
        print(msg)
        post_slack(f"LINE Flex送信 SKIP | {date_str} #{args.slot}")
        return 0

    ensure_csv_header(HISTCSV)

    # send_line_flex.py を実行
    cmd = [sys.executable, str(ROOT / "send_line_flex.py"), "--slot", str(args.slot)]
    if args.date:
        cmd += ["--date", date_str]
    # （send_line_flex.py は --force を受け取っても動作変わらないが将来拡張に備えて透過）
    if args.force:
        cmd += ["--force"]

    print("[RUN]", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out, _ = proc.communicate()

    # 標準出力をそのまま表示（STATUS 200 ... が出る想定）
    if out:
        sys.stdout.write(out)

    # 解析：STATUS 行から HTTP ステータスとメッセージID（あれば）を抽出
    status_code = None
    message_id = ""
    title_for_log = f"WANSTAGE トピック {date_str[5:].replace('-', '/')} #{args.slot}"

    # STATUS 200 {"sentMessages":[{"id":"12345", ...}]}
    m = re.search(r"STATUS\s+(\d{3})\s+(.*)", out or "", re.S)
    if m:
        status_code = int(m.group(1))
        body = m.group(2)
        # JSONを頑張って拾う
        try:
            j = json.loads(body)
            # push API の応答形式に合わせて掘る
            message_id = ((j.get("sentMessages") or [{}])[0]).get("id", "")
        except Exception:
            message_id = ""

    ok = (proc.returncode == 0) or (status_code is not None and 200 <= status_code < 300)
    status = "OK" if ok else f"NG({status_code if status_code is not None else proc.returncode})"

    # エラー本文を少しだけ（CSVに収まるよう切り詰め）
    err = ""
    if not ok:
        err = (out or "").strip()
        if len(err) > 400:
            err = err[:400]

    # CSV追記
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    with HISTCSV.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([ts, date_str, args.slot, title_for_log, status, message_id, err])

    # Slack通知
    post_slack(f"LINE Flex送信 {status} | {date_str} #{args.slot} | {title_for_log}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
