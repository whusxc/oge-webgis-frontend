@echo off
echo =================================================
echo 修复PowerShell执行策略问题
echo =================================================

echo 步骤1: 设置PowerShell 5.1执行策略...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"

echo 步骤2: 设置PowerShell 7执行策略...
"C:\Program Files\PowerShell\7\pwsh.exe" -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"

echo 步骤3: 测试PowerShell 7...
"C:\Program Files\PowerShell\7\pwsh.exe" -Command "Write-Host '✅ PowerShell 7 运行正常!' -ForegroundColor Green; $PSVersionTable.PSVersion"

echo.
echo =================================================
echo 执行策略修复完成！
echo =================================================
echo 现在可以运行PowerShell脚本了

pause 