# === 0) 変数 ===========================================================
$WAN = "$env:USERPROFILE\WANSTAGE"
$PORT_UI  = 8502
$PORT_API = 8000

# Macの.envと同じ値を入れてOK
$SLACK      = "https://hooks.slack.com/services/xxx/yyy/zzz"
$LINE_TOKEN = "PASTE_YOUR_LONG_CHANNEL_ACCESS_TOKEN"
$LINE_USER  = "U888583921108495c5a07027c4bed2524"

# 見やすいログ
$VerbosePreference = 'Continue'
Start-Transcript -Path "$env:USERPROFILE\WANSTAGE\setup.transcript.log" -Append -ErrorAction SilentlyContinue | Out-Null

# === 1) 必要ツール（winget） =========================================
winget install -e --id Python.Python.3.11            --source winget -h 2>$null | Out-Null
winget install -e --id Git.Git                       --source winget -h 2>$null | Out-Null
winget install -e --id Gyan.FFmpeg                   --source winget -h 2>$null | Out-Null
winget install -e --id ImageMagick.ImageMagick       --source winget -h 2>$null | Out-Null

# === 2) フォルダ & .env ===============================================
if (!(Test-Path $WAN)) { New-Item -Force -ItemType Directory $WAN | Out-Null }
New-Item -Force -ItemType Directory -Path "$WAN\logs","$WAN\data\outputs" | Out-Null

@"
# ASCII only
SLACK_WEBHOOK=$SLACK
LINE_CHANNEL_ACCESS_TOKEN=$LINE_TOKEN
LINE_USER_ID=$LINE_USER
"@ | Set-Content -Encoding ASCII "$WAN\.env"

# === 3) venv & 依存 ====================================================
Set-Location $WAN
py -3.11 -m venv .venv
. "$WAN\.venv\Scripts\Activate.ps1"
python -V
python -m pip install -U pip
if (Test-Path "$WAN\requirements.txt") {
  pip install -r requirements.txt
} else {
  pip install streamlit fastapi uvicorn requests python-dotenv pillow
}

# === 4) UI/API を別窓で起動 ===========================================
$cmdDir = "$WAN\binwin"; New-Item -Force -ItemType Directory $cmdDir | Out-Null
@"
@echo off
cd /d $WAN
call .venv\Scripts\activate.bat
streamlit run ui_main.py --server.port $PORT_UI --server.address 0.0.0.0
"@ | Set-Content -Encoding ASCII "$cmdDir\run_ui.cmd"
@"
@echo off
cd /d $WAN
call .venv\Scripts\activate.bat
uvicorn api.wanstage_api:app --host 0.0.0.0 --port $PORT_API --log-level info
"@ | Set-Content -Encoding ASCII "$cmdDir\run_api.cmd"

# 自動起動タスク
$taskUI  = "WANSTAGE-UI"
$taskAPI = "WANSTAGE-API"
schtasks /Delete /TN $taskUI  /F 2>$null
schtasks /Delete /TN $taskAPI /F 2>$null
schtasks /Create /RL LIMITED /SC ONLOGON /TN $taskUI  /TR "`"$cmdDir\run_ui.cmd`""
schtasks /Create /RL LIMITED /SC ONLOGON /TN $taskAPI /TR "`"$cmdDir\run_api.cmd`""

# Firewall
netsh advfirewall firewall add rule name="WANSTAGE UI $PORT_UI"  dir=in action=allow protocol=TCP localport=$PORT_UI | Out-Null
netsh advfirewall firewall add rule name="WANSTAGE API $PORT_API" dir=in action=allow protocol=TCP localport=$PORT_API | Out-Null

# 起動 & ヘルスチェック
Start-Process "$cmdDir\run_ui.cmd"
Start-Process "$cmdDir\run_api.cmd"
Start-Sleep -Seconds 5
try { (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$PORT_UI")  | Out-Null; Write-Host "UI:OK" } catch { Write-Host "UI:NG" }
try { (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$PORT_API/docs") | Out-Null; Write-Host "API:OK" } catch { Write-Host "API:NG" }

Stop-Transcript | Out-Null
Write-Host "[DONE] Windows サーバ化 完了。UI:$PORT_UI / API:$PORT_API"
