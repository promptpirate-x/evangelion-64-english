@echo off
rem Draws English text images for Evangelion 64 into games\eva64\work\images_en.
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
"%HERE%.venv\Scripts\python.exe" "%HERE%makeimages.py" %*
exit /b %ERRORLEVEL%
