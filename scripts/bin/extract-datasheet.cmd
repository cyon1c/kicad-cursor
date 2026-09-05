@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0extract-datasheet.ps1" %*
exit /b %ERRORLEVEL%
