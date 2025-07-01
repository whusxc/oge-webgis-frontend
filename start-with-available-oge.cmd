@echo off
chcp 65001 >nul
echo ========================================
echo   OGE WebGIS + MCP 服务启动脚本
echo   连接外网穿透OGE服务器
echo ========================================
echo.

echo 🌟 检查环境...

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请安装Python 3.8+并添加到PATH
    pause
    exit /b 1
)

:: 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或未添加到PATH
    echo 请安装Node.js 16+并添加到PATH
    pause
    exit /b 1
)

echo ✅ Python和Node.js已安装

echo.
echo 🚀 正在启动MCP服务器...
echo 🔗 连接到: http://111.37.195.111:7002

:: 创建日志目录
if not exist logs mkdir logs

:: 启动MCP服务器（后台运行）
start "MCP Server" cmd /c "python shandong_mcp_server.py --mode http --host 0.0.0.0 --port 8000 & pause"

:: 等待MCP服务器启动
echo ⏳ 等待MCP服务器启动...
timeout /t 3 >nul

:: 测试MCP服务器连通性
echo 🔍 测试MCP服务器连通性...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  MCP服务器可能需要更多时间启动
) else (
    echo ✅ MCP服务器启动成功
)

echo.
echo 🌐 正在启动前端服务...

:: 进入前端目录
cd oge-webgis-frontend

:: 检查依赖
if not exist node_modules (
    echo 📦 安装前端依赖...
    call npm install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

:: 启动前端开发服务器
echo 🎯 启动前端开发服务器...
start "Frontend Server" cmd /c "npm run dev & pause"

:: 等待前端服务器启动
echo ⏳ 等待前端服务器启动...
timeout /t 5 >nul

echo.
echo ========================================
echo 🎉 服务启动完成！
echo.
echo 📍 访问地址:
echo    前端界面: http://localhost:3000
echo    MCP API:  http://localhost:8000
echo    OGE服务:  http://111.37.195.111:7002
echo.
echo 💡 使用说明:
echo    1. 在浏览器中打开 http://localhost:3000
echo    2. 使用右侧AI助手测试功能
echo    3. 尝试"检查环境状态"或"坡度分析"
echo.
echo 🔧 如果遇到问题:
echo    1. 确保网络连接正常
echo    2. 检查防火墙设置
echo    3. 联系志威哥确认服务器状态
echo ========================================

:: 自动打开浏览器
timeout /t 2 >nul
start http://localhost:3000

echo.
echo 按任意键退出...
pause >nul 