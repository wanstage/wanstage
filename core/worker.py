import time, os, sys

print("[wan-py-worker] start pid=", os.getpid(), flush=True)
try:
    while True:
        print("[wan-py-worker] heartbeat", flush=True)
        time.sleep(10)
except KeyboardInterrupt:
    print("[wan-py-worker] stop", flush=True)
