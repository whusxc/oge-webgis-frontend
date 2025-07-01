@echo off
echo ============================================
echo 测试服务运行状态
echo ============================================

echo 检查8000端口(MCP服务器)...
netstat -ano | findstr :8000
if %errorlevel% equ 0 (
    echo ✅ MCP服务器正在运行
) else (
    echo ❌ MCP服务器未运行
)

echo.
echo 检查3000端口(前端服务器)...
netstat -ano | findstr :3000
if %errorlevel% equ 0 (
    echo ✅ 前端服务器正在运行
) else (
    echo ❌ 前端服务器未运行
)

echo.
echo 检查Python进程...
tasklist | findstr python.exe
if %errorlevel% equ 0 (
    echo ✅ Python进程正在运行
) else (
    echo ❌ 没有Python进程
)

echo.
echo 检查Node进程...
tasklist | findstr node.exe
if %errorlevel% equ 0 (
    echo ✅ Node进程正在运行
) else (
    echo ❌ 没有Node进程
)

echo.
echo ============================================
echo 如果服务都在运行，请访问:
echo MCP服务器: http://localhost:8000/health
echo 前端页面: http://localhost:3000
echo ============================================

fix-powershell.bat

.\start-real-mcp.bat 