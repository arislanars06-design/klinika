@echo off
rem NURMED: status (sichqoncha bilan ikki marta bosing)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0nurmed.ps1" -Action status
