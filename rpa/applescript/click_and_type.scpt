-- 使い方: osascript click_and_type.scpt "Google Chrome" 400 180 "おはようございます！"
on run argv
  set appName to item 1 of argv
  set px to (item 2 of argv) as integer
  set py to (item 3 of argv) as integer
  set msg to item 4 of argv

  tell application appName to activate
  delay 0.5

  -- 座標クリック（cliclickを利用）
  do shell script "/opt/homebrew/bin/cliclick c:" & px & "," & py
  delay 0.2

  -- クリップボード経由で貼り付け（IME影響を回避）
  set the clipboard to msg
  tell application "System Events" to keystroke "v" using {command down}
end run
