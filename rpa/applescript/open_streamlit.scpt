tell application "Google Chrome"
  if (count of windows) = 0 then make new window
  set URL of active tab of window 1 to "http://localhost:8501"
  activate
end tell
