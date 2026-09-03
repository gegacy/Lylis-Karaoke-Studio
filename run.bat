@echo off
chcp 65001 > nul
title Lylis Karaoke Studio
cd /d "%~dp0"
echo ========================================================
echo     Starting Lylis Karaoke Studio (Python + PyQt5)
echo ========================================================
echo.
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python main.py
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        py main.py
    ) else (
        where uv >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            set "UV_CACHE_DIR=%~dp0.runtime\uv-cache"
            set "UV_PYTHON_INSTALL_DIR=%~dp0.runtime\python"
            uv run --python 3.12 --with-requirements requirements.txt python main.py
        ) else (
            echo [ERROR] Python 3.10+ was not found.
            echo Install Python from https://www.python.org/downloads/ or install uv.
            pause
            exit /b 1
        )
    )
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with an error code.
    pause
)
