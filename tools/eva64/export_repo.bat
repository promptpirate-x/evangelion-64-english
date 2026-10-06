@echo off
rem Copies the publishable parts of the Evangelion 64 project into the standalone git
rem repository folder next to this workspace (..\eva64-english-patch), keeping the same
rem folder layout so the tools work there unchanged. Nothing from original\ or work\ is copied.
setlocal
set "WS=%~dp0..\.."
set "DEST=%~dp0..\..\..\eva64-english-patch"
if not exist "%DEST%" mkdir "%DEST%"
robocopy "%WS%\tools\eva64" "%DEST%\tools\eva64" /MIR /XD .venv __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS >nul
robocopy "%WS%\tools\fonts" "%DEST%\tools\fonts" /MIR /NFL /NDL /NJH /NJS >nul
robocopy "%WS%\games\eva64\scripts" "%DEST%\games\eva64\scripts" /MIR /NFL /NDL /NJH /NJS >nul
robocopy "%WS%\games\eva64\patch" "%DEST%\games\eva64\patch" /MIR /NFL /NDL /NJH /NJS >nul
robocopy "%WS%\games\eva64" "%DEST%\games\eva64" GAME.md /NFL /NDL /NJH /NJS >nul
robocopy "%WS%\docs" "%DEST%\docs" /MIR /NFL /NDL /NJH /NJS >nul
copy /Y "%WS%\CLAUDE.md" "%DEST%\CLAUDE.md" >nul
copy /Y "%WS%\tools\README.md" "%DEST%\tools\README.md" >nul
echo Exported to %DEST%
