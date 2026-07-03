@echo off
setlocal
set "APP_DIR=%~dp0"

py -3 "%APP_DIR%sqt_tool.py"
if errorlevel 1 (
  python "%APP_DIR%sqt_tool.py"
)
