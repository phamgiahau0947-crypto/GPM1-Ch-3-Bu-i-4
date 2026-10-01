@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"
title De an 03 - Dashboard VaR ES

set "VPY=.venv\Scripts\python.exe"
if exist "%VPY%" goto CHECK_ENV

echo Python 3.11-3.13 is required for the first setup.
set "PY="
for %%V in (3.12 3.13 3.11) do (
    if not defined PY (
        py -%%V -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PY=py -%%V"
    )
)
if not defined PY (
    python -c "import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo [ERROR] Install Python 3.11, 3.12, or 3.13 and enable Add python.exe to PATH.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

echo Creating the project virtual environment...
%PY% -m venv .venv
if errorlevel 1 goto INSTALL_ERROR

:CHECK_ENV
if exist ".venv\cai_dat_xong.txt" (
    "%VPY%" -c "import streamlit, pandas, numpy, scipy, statsmodels, arch, plotly, yaml, pyarrow, joblib" >nul 2>&1
    if not errorlevel 1 goto RUN_DASHBOARD
)

echo Installing project packages. This is needed only on first launch.
"%VPY%" -m pip install --upgrade pip --disable-pip-version-check -q
if errorlevel 1 goto INSTALL_ERROR
"%VPY%" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 (
    echo Retrying with compatible package versions...
    "%VPY%" -m pip install -r requirements-linh-hoat.txt --disable-pip-version-check
    if errorlevel 1 goto INSTALL_ERROR
)
"%VPY%" -c "import streamlit, pandas, numpy, scipy, statsmodels, arch, plotly, yaml, pyarrow, joblib"
if errorlevel 1 goto INSTALL_ERROR
echo ready> ".venv\cai_dat_xong.txt"

:RUN_DASHBOARD
echo Checking whether the dashboard is already running...
"%VPY%" -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health',timeout=2); raise SystemExit(0 if r.read()==b'ok' else 1)" >nul 2>&1
if not errorlevel 1 goto EXISTING_DASHBOARD

echo.
echo Dashboard starting at http://localhost:8501
echo Keep this window open while using the dashboard.
echo In the dashboard, select Van hanh -^> Chay phan tich -^> Bat dau chay toan bo.
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 5; Start-Process 'http://localhost:8501'"
"%VPY%" -m streamlit run dashboard\app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
if errorlevel 1 (
    echo.
    echo [ERROR] Dashboard did not start. Check whether port 8501 is already in use.
    pause
)
exit /b

:EXISTING_DASHBOARD
echo Dashboard is already running. Opening http://localhost:8501
start "" "http://localhost:8501"
exit /b

:INSTALL_ERROR
echo.
echo [ERROR] Setup failed. Check your Internet connection and Python version.
pause
exit /b 1
