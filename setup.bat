@echo off
setlocal
title Landscape Agent Pack Setup
echo ============================================================
echo   Landscape Agent Pack Setup
echo   Args passed to installer: %*
echo ============================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1" %*
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" ( echo Result: INSTALL CHECK COMPLETED - read Summary warnings and manual client reload requirements ) else ( echo Result: FAILED  exit=%RC% )
echo Logs and runs: see the Summary block above (Runs/logs line).
echo.
pause
endlocal & exit /b %RC%
