@echo off
chcp 65001 >nul
echo ===============================================
echo 🚀 OGE WebGIS 自动化检查和启动
echo ===============================================

echo 🔍 步骤1: 检查前端服务状态...
echo.
netstat -ano | findstr ":3000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 前端服务已在端口 3000 运行
    echo 🌐 访问地址: http://localhost:3000
) else (
    netstat -ano | findstr ":5173" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ 前端服务已在端口 5173 运行 
        echo 🌐 访问地址: http://localhost:5173
    ) else (
        echo ❌ 前端服务未运行，正在启动...
        echo.
        cd /d "%~dp0oge-webgis-frontend"
        start /min cmd /c "npm run dev"
        timeout /t 5 /nobreak >nul
        echo ✅ 前端启动命令已执行
        cd /d "%~dp0"
    )
)

echo.
echo 🔍 步骤2: 检查 MCP 服务器状态...
echo.
netstat -ano | findstr ":8000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MCP 服务器已在端口 8000 运行
) else (
    echo ❌ MCP 服务器未运行，正在启动...
    if exist "simple-mcp-server.py" (
        start /min cmd /c "python simple-mcp-server.py"
        timeout /t 3 /nobreak >nul
        echo ✅ MCP 服务器启动命令已执行
    ) else (
        echo ⚠️  找不到 MCP 服务器文件
    )
)

echo.
echo 🔍 步骤3: 检查 Node.js 和 Python 环境...
echo.
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Node.js 已安装
    node --version
) else (
    echo ❌ Node.js 未安装或未加入PATH
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python 已安装
    python --version
) else (
    echo ❌ Python 未安装或未加入PATH
)

echo.
echo 🔍 步骤4: 最终服务状态检查...
echo.
timeout /t 3 /nobreak >nul

echo 📊 当前运行的服务:
netstat -ano | findstr ":3000 :5173 :8000" | findstr "LISTENING"
if %errorlevel% neq 0 (
    echo 未检测到预期的服务端口
)

echo.
echo ===============================================
echo 🎉 自动化检查完成！
echo ===============================================
echo.
echo 📝 服务访问信息:
echo    - 前端: http://localhost:3000 或 http://localhost:5173
echo    - MCP: http://localhost:8000 (如果启动)
echo.
echo 💡 如果服务未正常启动，请检查控制台输出的错误信息
echo.

pause 