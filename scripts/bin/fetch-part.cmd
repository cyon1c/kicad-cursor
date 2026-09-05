@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fetch-part.ps1" %*
exit /b %ERRORLEVEL%
