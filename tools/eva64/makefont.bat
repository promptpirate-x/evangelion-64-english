@echo off
rem Draws the English font for Evangelion 64 into games\eva64\work\font.
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
"%HERE%.venv\Scripts\python.exe" "%HERE%makefont.py" %*
exit /b %ERRORLEVEL%
