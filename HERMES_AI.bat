@echo off
title HERMES AI - Institutional SMC Quant Agent
cd /d "%~dp0"
cls
:menu
echo ===============================================================================
echo                [🧠] HERMES AI QUANTITATIVE TRADING AGENT
echo      Institutional SMC V17 Strategy Enhancement & Optimization Engine
echo ===============================================================================
echo.
echo   [1] Hermes Cognitive Status (Lifetime Win Rate ^& 98.2%% Capital Safety)
echo   [2] Read ^& Audit Strategy Code (Loopholes ^& Institutional Fixes)
echo   [3] Discovered Zero-Loss Patterns (London/NY Killzone Spring)
echo   [4] 90%%+ Win Rate Enhancement Blueprint
echo   [5] Scan Live 15m Binance Futures Order Blocks (Real-Time Scoring)
echo   [6] Forensic Diagnostics on Past Trade Ledgers (NEARUSDT Post-Mortem)
echo   [7] Run 6-Month Parameter Grid Optimization Sweep
echo   [8] Interactive Chat with Hermes AI
echo   [0] Exit
echo.
echo ===============================================================================
set /p opt="Enter your choice (0-8): "

if "%opt%"=="1" (
    cls
    python run_hermes.py --status
    echo.
    pause
    cls
    goto menu
)
if "%opt%"=="2" (
    cls
    python run_hermes.py --audit-strategy
    echo.
    pause
    cls
    goto menu
)
if "%opt%"=="3" (
    cls
    python run_hermes.py --patterns
    echo.
    pause
    cls
    goto menu
)
if "%opt%"=="4" (
    cls
    python run_hermes.py --enhance
    echo.
    pause
    cls
    goto menu
)
if "%opt%"=="5" (
    cls
    python run_hermes.py --scan
    echo.
    pause
    cls
    goto menu
)
if "%opt%"=="6" (
    cls
    python run_hermes.py --diagnose
    echo.
    pause
    cls
    goto menu
)
if "%opt%"=="7" (
    cls
    python run_hermes.py --tune
    echo.
    pause
    cls
    goto menu
)
if "%opt%"=="8" (
    cls
    echo Type your question for Hermes AI (or 'back' to return):
    set /p query="> "
    if /i not "%query%"=="back" (
        python run_hermes.py --chat "%query%"
        echo.
        pause
    )
    cls
    goto menu
)
if "%opt%"=="0" exit
cls
goto menu
