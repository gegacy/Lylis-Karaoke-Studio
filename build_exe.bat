@echo off
chcp 65001 > nul
title Build Lylis Karaoke Studio Executable
cd /d "%~dp0"
echo ========================================================
echo     Building Lylis Karaoke Studio Standalone EXE
echo ========================================================
echo.

:: Ensure icon is ready
if not exist "assets\app_icon.ico" (
    echo [INFO] Generating app_icon.ico...
    python build_icon.py
)

echo [INFO] Running PyInstaller with custom application icon...
where pyinstaller >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    pyinstaller LylisKaraokeStudio.spec --noconfirm --clean
) else (
    python -m PyInstaller LylisKaraokeStudio.spec --noconfirm --clean
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo  [SUCCESS] Build finished!
    echo  Application executable location:
    echo  dist\LylisKaraokeStudio\LylisKaraokeStudio.exe
    echo ========================================================
) else (
    echo.
    echo [ERROR] Build failed. Check the error log above.
    pause
    exit /b 1
)

pause
