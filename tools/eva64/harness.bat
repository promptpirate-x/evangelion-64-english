@echo off
rem Runs a built ROM in BizHawk under a script and saves screenshots: harness.bat <name> <plan>
setlocal
set "HERE=%~dp0"
if not exist "%HERE%.venv\Scripts\python.exe" (
    echo Creating local Python environment...
    py -3.11 -m venv "%HERE%.venv" || exit /b 1
)
set PYTHONIOENCODING=utf-8
"%HERE%.venv\Scripts\python.exe" "%HERE%harness.py" %*
exit /b %ERRORLEVEL%
