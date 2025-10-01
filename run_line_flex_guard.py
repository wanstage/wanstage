import sys, csv, pathlib, argparse, datetime, os, subprocess, json

hist = pathlib.Path("logs/lineflex_history.csv")
ap = argparse.ArgumentParser(); ap.add_argument("--date"); ap.add_argument("--slot", type=int, default=1); ap.add_argument("--force", action="store_true"); args,_ = ap.parse_known_args()

# date 未指定なら「今日」
date_str = args.date or datetime.date.today().isoformat()

sent_already = False
if hist.exists() and not args.force:
    with hist.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("date")==date_str and int(r.get("slot",0))==args.slot and r.get("status","").startswith("OK"):
                sent_already = True; break

if sent_already:
    print(f"[SKIP] {date_str} slot#{args.slot} は既にOK送信済みです。--force で強制可。")
    sys.exit(0)

# そのまま本体に同じ引数で引き渡し
cmd = [os.environ.get("PYTHON", "python3"), "send_line_flex.py"] + sys.argv[1:]
print("[RUN]", " ".join(cmd))
sys.exit(subprocess.call(cmd))
