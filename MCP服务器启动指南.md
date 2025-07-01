# OGE MCP服务器启动指南

## 🎯 目标
启动MCP服务器以消除前端的"环境检查失败"错误，获得完整的地理分析功能。

## 🚀 自动安装方式（推荐）

### 方法1：使用批处理脚本
1. 双击运行 `setup-mcp-server.bat`
2. 脚本会自动：
   - 检查并安装Python 3.11
   - 安装所需依赖包
   - 创建日志目录
   - 启动MCP服务器

### 方法2：使用PowerShell脚本
1. 右键点击 `setup-mcp-server.ps1` → "使用PowerShell运行"
2. 如果遇到执行策略错误，请先运行：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## 🛠️ 手动安装方式

### 步骤1：安装Python
1. 访问 https://www.python.org/downloads/
2. 下载Python 3.11.x版本
3. 安装时勾选"Add Python to PATH"

### 步骤2：安装依赖包
打开命令提示符或PowerShell，运行：
```bash
# 升级pip
python -m pip install --upgrade pip

# 安装MCP服务器依赖
python -m pip install fastmcp starlette uvicorn httpx pydantic
```

### 步骤3：启动MCP服务器
```bash
# 创建日志目录
mkdir logs

# 启动服务器
python "shandong_mcp_server_enhanced-遥感大楼适配版.py"
```

## ✅ 验证安装

### 1. 检查服务器状态
MCP服务器启动后，你应该看到类似信息：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. 测试健康检查
在浏览器中访问：http://localhost:8000/health

应该返回：
```json
{
  "status": "healthy",
  "server": "yaogan-building-cultivated-analysis"
}
```

### 3. 刷新前端页面
刷新 http://localhost:3000，错误提示应该消失。

## 🔧 功能测试

MCP服务器启动后，你可以在前端测试：

1. **环境检查工具** - 应该显示各项服务状态
2. **智能助手** - 可以正常对话
3. **分析工具** - 坡度分析、缓冲区分析等
4. **任务监控** - 查看分析任务进度

## 🚨 常见问题

### 问题1：Python命令不识别
**解决方案**：
- 重新安装Python，确保勾选"Add Python to PATH"
- 或手动添加Python到系统PATH环境变量

### 问题2：pip安装失败
**解决方案**：
```bash
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastmcp starlette uvicorn httpx pydantic
```

### 问题3：端口8000被占用
**解决方案**：
- 检查是否有其他程序占用端口8000
- 或修改MCP服务器代码中的端口号

### 问题4：权限不足
**解决方案**：
- 以管理员身份运行命令提示符
- 或使用虚拟环境：
```bash
python -m venv venv
venv\Scripts\activate
pip install fastmcp starlette uvicorn httpx pydantic
```

## 📝 服务管理

### 停止服务器
在MCP服务器窗口按 `Ctrl+C`

### 查看日志
```bash
# 服务日志
type logs\yaogan_mcp.log

# API调用日志
type logs\api_calls.log
```

### 重启服务器
```bash
# 停止服务器 (Ctrl+C)
# 然后重新运行
python "shandong_mcp_server_enhanced-遥感大楼适配版.py"
```

---

**🎉 完成后，你的OGE WebGIS平台将拥有完整的地理分析功能！** 