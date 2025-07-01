@echo off
echo ============================================
echo 检查开发环境状态
echo ============================================

echo 检查Node.js...
node --version
if %errorlevel% neq 0 (
    echo ❌ Node.js 未安装或路径有问题
) else (
    echo ✅ Node.js 正常
)

echo.
echo 检查npm...
npm --version
if %errorlevel% neq 0 (
    echo ❌ npm 未安装或路径有问题
) else (
    echo ✅ npm 正常
)

echo.
echo 检查前端目录...
cd oge-webgis-frontend
if not exist package.json (
    echo ❌ 找不到package.json文件
    echo 当前目录: %CD%
    dir
) else (
    echo ✅ 找到package.json文件
    echo 检查依赖是否安装...
    if not exist node_modules (
        echo ⚠️ node_modules目录不存在，需要安装依赖
        echo 正在安装依赖...
        npm install
    ) else (
        echo ✅ node_modules目录存在
    )
)

echo.
echo ============================================
echo 环境检查完成
echo ============================================

pause 