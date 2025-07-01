@echo off
echo =================================================
echo 修复PowerShell会话问题
echo =================================================

echo 1. 结束可能卡住的PowerShell进程...
taskkill /f /im powershell.exe 2>nul
taskkill /f /im pwsh.exe 2>nul

echo 2. 清理PowerShell配置缓存...
if exist "%USERPROFILE%\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1" (
    ren "%USERPROFILE%\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1" "Microsoft.PowerShell_profile.ps1.bak"
)

echo 3. 重置PowerShell执行策略...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"

echo 4. 测试PowerShell...
powershell -Command "Write-Host 'PowerShell修复完成！'; Get-Location; Get-ChildItem | Select-Object -First 5"

echo.
echo =================================================
echo PowerShell修复完成！请重新打开命令行窗口
echo ================================================= 