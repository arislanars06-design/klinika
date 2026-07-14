@echo off
REM ============================================================================
REM  Klinika — LAN (local network) launcher
REM
REM  Same as ``start.bat`` but binds uvicorn to 0.0.0.0 so other computers
REM  and phones on the same Wi-Fi / LAN can open the app in their browsers.
REM
REM  The script prints every LAN IPv4 address it finds so the operator knows
REM  which URL to type into the phone / laptop browser.
REM
REM  Stop the server with Ctrl+C.
REM ============================================================================

setlocal enabledelayedexpansion
title Klinika (LAN access) - http://<LAN-IP>:8000

REM ---- Activate the project virtualenv --------------------------------------
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo [!] .venv topilmadi. Avval: python -m venv .venv ^&^& .\.venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

REM ---- Bind to every network interface --------------------------------------
set CLINIC_WEB_HOST=0.0.0.0
if not defined CLINIC_WEB_PORT set CLINIC_WEB_PORT=8000

REM ---- Print the URLs a phone / other PC should use -------------------------
echo.
echo ================================================================
echo   KLINIKA WEB - tarmoqqa ochilgan (LAN access)
echo ================================================================
echo.
echo   Bu kompyuterda ochish uchun:
echo     http://localhost:!CLINIC_WEB_PORT!
echo.
echo   Bir xil Wi-Fi'dagi telefon / boshqa kompyuterdan ochish uchun
echo   quyidagi manzillardan BIRINI brauzerga kiriting:
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    set "ip=%%a"
    set "ip=!ip: =!"
    if not "!ip!"=="127.0.0.1" (
        echo     http://!ip!:!CLINIC_WEB_PORT!
    )
)

echo.
echo ----------------------------------------------------------------
echo   Windows Firewall birinchi marta so'raganda "Allow access" bosing.
echo   To'xtatish: Ctrl+C
echo ================================================================
echo.

REM ---- Launch uvicorn -------------------------------------------------------
python -m clinic.web.main

endlocal
