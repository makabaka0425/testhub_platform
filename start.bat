@echo off
chcp 65001 >nul 2>&1
title 灵测 - 一键启动

:: ============================================
::  灵测 一键启动脚本
::  前端: localhost:3000  后端: localhost:8000
:: ============================================

echo.
echo  ========================================
echo   灵测 一键启动
echo  ========================================
echo.

:: ---- 切换到项目根目录 ----
cd /d "%~dp0"

:: ---- 检查端口占用 ----
echo  [1/4] 检查端口...

netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo  [!] 8000 端口已被占用，后端可能已在运行
    echo      如需重启，请先关闭占用进程，或按 Ctrl+C 取消
    choice /c YN /m "  是否继续启动（可能冲突）"
    if %errorlevel%==2 exit /b 1
)

netstat -ano | findstr ":3000 " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo  [!] 3000 端口已被占用，前端可能已在运行
    choice /c YN /m "  是否继续启动（可能冲突）"
    if %errorlevel%==2 exit /b 1
)

:: ---- 启动后端 Django ----
echo  [2/4] 启动后端 (Django :8000)...
start "灵测-Backend" cmd /k "cd /d "%~dp0" && venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"
echo  [OK] 后端已在新窗口启动

:: 等 3 秒让后端先起来
echo  [3/4] 等待后端就绪...
timeout /t 3 /nobreak >nul

:: ---- 启动前端 Vite ----
echo  [4/4] 启动前端 (Vite :3000)...
start "灵测-Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo  [OK] 前端已在新窗口启动

:: ---- 打开浏览器 ----
echo.
echo  正在打开浏览器...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo  ========================================
echo   启动完成！
echo   前端: http://localhost:3000
echo   后端: http://localhost:8000
echo   API文档: http://localhost:8000/api/docs/
echo.
echo   关闭方式: 关闭对应命令行窗口即可
echo  ========================================
echo.
echo  (此窗口可安全关闭)
pause
