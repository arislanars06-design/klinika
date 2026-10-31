@echo off
rem NURMED serverini fonda ishga tushirish.
rem Bu faylni Task Scheduler ("NURMED" vazifasi) chaqiradi, qo'lda ishga tushirish shart emas.
rem 1-parametr: node.exe ning to'liq yo'li (install.bat o'zi yozib qo'yadi).

cd /d "%~dp0.."
if not exist "data\logs" mkdir "data\logs"

set "NODE=node"
if exist "%ProgramFiles%\nodejs\node.exe" set "NODE=%ProgramFiles%\nodejs\node.exe"
if not "%~1"=="" set "NODE=%~1"

rem Jurnal 10 MB dan oshsa, eski nusxaga o'tkaziladi
for %%F in ("data\logs\server.log") do if %%~zF GTR 10485760 move /y "data\logs\server.log" "data\logs\server.old.log" >nul

echo.>> "data\logs\server.log"
echo ===== %DATE% %TIME% NURMED ishga tushirilmoqda =====>> "data\logs\server.log"
"%NODE%" --disable-warning=ExperimentalWarning server\server.js >> "data\logs\server.log" 2>&1
exit /b %ERRORLEVEL%
