import os, subprocess, sys
BASE = os.path.dirname(os.path.dirname(__file__))
print(f"[DEBUG] BASE={BASE}")
cont1 = os.path.join(BASE, 'externals', 'continue')
CONT = cont1 if os.path.isdir(cont1) else os.path.join(BASE,'continue')
print(f"[DEBUG] CONT={CONT}")
if not os.path.isdir(CONT):
    print('[ERROR] NG: continue not found')
    sys.exit(1)
cmd = [sys.executable, os.path.join(CONT,'main.py'), *sys.argv[1:]]
print(f"[DEBUG] CMD={cmd}")
rc = subprocess.call(cmd)
print(f"[DEBUG] RC={rc}")
sys.exit(rc)
