-- 使い方: osascript capture_dashboard.scpt "https://example.com" "WANSTAGE ダッシュ"
on run argv
  set theURL to item 1 of argv
  set theTitle to item 2 of argv
  tell application "Google Chrome"
    if (count of windows) = 0 then make new window
    tell window 1
      set URL of active tab to theURL
      delay 3
      set bounds of it to {0, 24, 1440, 900}
    end tell
    activate
  end tell
  delay 2
  set ts to do shell script "date +%Y%m%d-%H%M%S"
  set out to (POSIX path of (path to home folder)) & "WANSTAGE/logs/" & "dash-" & ts & ".png"
  do shell script "screencapture -x " & quoted form of out
  display notification "Saved: " & out with title theTitle
end run
