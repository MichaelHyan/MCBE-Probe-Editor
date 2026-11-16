@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [ERROR] 未找到 Python，请安装 Python 3.9+ 并加入 PATH。
    pause
    exit /b 1
)

echo 正在启动 MCBE Probe Editor ...（浏览器将自动打开，关闭本窗口即停止服务）
%PY% "%~dp0run.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] 启动失败。
    pause
)
endlocal