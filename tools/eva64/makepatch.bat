@echo off
rem Builds the release patch: makepatch.bat <version>
setlocal
set "HERE=%~dp0"
if not exist "%HERE%.venv\Scripts\python.exe" (
    echo Creating local Python environment...
    py -3.11 -m venv "%HERE%.venv" || exit /b 1
)
"%HERE%.venv\Scripts\python.exe" -c "import PIL" 2>nul || (
    echo Installing Pillow into the local environment...
    "%HERE%.venv\Scripts\python.exe" -m pip install --quiet -r "%HERE%requirements.txt" || exit /b 1
)
set PYTHONIOENCODING=utf-8
"%HERE%.venv\Scripts\python.exe" "%HERE%makepatch.py" %*
exit /b %ERRORLEVEL%
