@echo off
rem Checks a built Evangelion 64 ROM: verify.bat <name> [en]
setlocal
set "HERE=%~dp0"
if not exist "%HERE%.venv\Scripts\python.exe" (
    echo Creating local Python environment...
    py -3.11 -m venv "%HERE%.venv" || exit /b 1
)
set PYTHONIOENCODING=utf-8
"%HERE%.venv\Scripts\python.exe" "%HERE%verify.py" %*
exit /b %ERRORLEVEL%
