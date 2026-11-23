@echo off
title RemoteDevBridge
cd /d "%~dp0"
echo ========================================================
echo         Starting RemoteDevBridge Telegram Bot...
echo ========================================================
call .venv\Scripts\activate
python main.py
pause
