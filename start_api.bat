@echo off
echo Starting JobSearch API server...
cd /d %~dp0
python start_api.py %*
pause
