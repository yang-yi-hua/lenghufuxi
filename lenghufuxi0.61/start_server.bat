@echo off
chcp 65001 >nul

REM 冷湖知识复习系统启动脚本
REM 自动启动前端和后端服务器

echo ======================================
echo       冷湖知识复习系统启动脚本
echo ======================================
echo.

REM 检查Python是否安装
echo 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python环境，请先安装Python
    pause
    exit /b 1
)
echo Python环境检查成功！
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"
echo 当前工作目录: %cd%
echo.

REM 启动前端服务器（Python内置HTTP服务器）
echo 启动前端服务器...
start "前端服务器" cmd /c "python -m http.server 8888 --bind 0.0.0.0"
echo 前端服务器已启动，运行在 http://0.0.0.0:8888
echo.

REM 启动后端API服务器
echo 启动后端API服务器...
start "后端API服务器" cmd /c "python server.py --port 9000"
echo 后端API服务器已启动，运行在 http://localhost:9000
echo.

REM 显示访问地址
echo ======================================
echo 服务器启动完成！
echo ======================================
echo 本地访问地址:
echo   前端: http://127.0.0.1:8888
echo   API: http://127.0.0.1:9000
echo.
echo 网络访问地址:
echo   前端: http://192.168.110.15:8888
echo   API: http://192.168.110.15:9000
echo ======================================
echo 其他终端可以通过网络访问地址进行访问
echo ======================================
echo.
echo 服务器已在后台启动，窗口将自动关闭...
echo.

REM 延迟2秒后退出
ping 127.0.0.1 -n 3 >nul
exit