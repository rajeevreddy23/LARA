@echo off
title 🌌 LARA AI OS — Background Voice & Orchestrator Daemon
color 0b

echo =======================================================
echo          🌌 LARA PERSONAL AI OPERATING SYSTEM
echo   Background Listener • Voice Control • System File Hub
echo =======================================================
echo.
echo [*] Initializing LARA Orchestrator on http://localhost:8000 ...
start "LARA Backend Orchestrator" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --port 8000"

echo [*] Initializing LARA Continuous Background Voice Daemon ...
echo [*] Say "Hey LARA" at any time to activate LARA across Windows.
start "LARA Background Voice Daemon" cmd /k "cd /d %~dp0backend && python background_lara.py"

echo.
echo [OK] LARA is now active in the background!
echo     Say 'Hey LARA' to issue voice directives or open files.
echo =======================================================
