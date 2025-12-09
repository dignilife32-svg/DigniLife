@echo off
powershell -NoProfile -Command "Get-Content amount.txt | Set-Clipboard"
echo Copied amount. Press any key to copy reference...
pause >nul
powershell -NoProfile -Command "Get-Content reference.txt | Set-Clipboard"
echo Copied reference (WID). Done.
