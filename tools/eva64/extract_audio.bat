@echo off
rem Extracts voices and sound effects as WAV files into games\eva64\work\audio.
setlocal
set "HERE=%~dp0"
if not exist "%HERE%.venv\Scripts\python.exe" (
    echo Creating local Python environment...
    py -3.11 -m venv "%HERE%.venv" || exit /b 1
)
set PYTHONIOENCODING=utf-8
"%HERE%.venv\Scripts\python.exe" "%HERE%extract_audio.py" %*
exit /b %ERRORLEVEL%
