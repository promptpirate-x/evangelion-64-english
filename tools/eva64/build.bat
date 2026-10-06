@echo off
rem Rebuilds the Evangelion 64 ROM. No arguments: unchanged rebuild check.
rem build.bat <changes.tsv relative to games\eva64> <output name>
setlocal
set "HERE=%~dp0"
if not exist "%HERE%.venv\Scripts\python.exe" (
    echo Creating local Python environment...
    py -3.11 -m venv "%HERE%.venv" || exit /b 1
)
set PYTHONIOENCODING=utf-8
"%HERE%.venv\Scripts\python.exe" "%HERE%build.py" %*
exit /b %ERRORLEVEL%
