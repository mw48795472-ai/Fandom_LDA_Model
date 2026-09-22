@echo off
rem START.bat - one-click run: SETUP_DATA.R (fill data/ from raw archive) then RUN_ALL.R
rem Usage: double-click, or drag the raw archive folder (or zip) onto this file.
chcp 65001 >nul
cd /d "%~dp0"
set "RS="
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\R-core\R" /v InstallPath 2^>nul') do set "RH=%%b"
if defined RH if exist "%RH%\bin\Rscript.exe" set "RS=%RH%\bin\Rscript.exe"
if not defined RS for /d %%d in ("%ProgramFiles%\R\R-*") do if exist "%%d\bin\Rscript.exe" set "RS=%%d\bin\Rscript.exe"
if not defined RS for /d %%d in ("%LocalAppData%\Programs\R\R-*") do if exist "%%d\bin\Rscript.exe" set "RS=%%d\bin\Rscript.exe"
if not defined RS (
  echo [START] R not found. Install R from https://cran.r-project.org and run again.
  pause
  exit /b 1
)
echo [START] Rscript: %RS%
"%RS%" SETUP_DATA.R %1
if errorlevel 1 (
  echo [START] SETUP_DATA failed - see message above.
  pause
  exit /b 1
)
"%RS%" RUN_ALL.R
echo.
echo [START] done - results in outputs\ , figures in outputs\plots\
pause
