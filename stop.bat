@echo off
echo Stopping SMC V17 Terminal and Scanner...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a 2>nul
echo Done! SMC V17 stopped.
pause
