@echo off
rem Extracts text, font and images from the Evangelion 64 ROM into games\eva64\work\extract.
setlocal
set "HERE=%~dp0"
if not exist "%HERE%.venv\Scripts\python.exe" (
    echo Creating local Python environment...
    py -3.11 -m venv "%HERE%.venv" || exit /b 1
)
set PYTHONIOENCODING=utf-8
"%HERE%.venv\Scripts\python.exe" "%HERE%extract.py" %*
exit /b %ERRORLEVEL%
