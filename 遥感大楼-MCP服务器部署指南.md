# 遥感大楼MCP服务器部署指南

## 概述

本指南将帮助您在遥感大楼环境中部署山东耕地流出分析MCP服务器。该服务器已适配遥感大楼的网络环境（10.101.240.x 网段）和大数据组件。

## 环境要求

### 硬件环境
- **网络**: 遥感大楼内网（10.101.240.x 网段）
- **服务器**: 建议部署在能访问所有服务节点的机器上

### 软件环境
- **Python**: 3.9+
- **Conda**: 用于环境管理
- **系统**: Linux (推荐 Ubuntu/CentOS)

## 环境架构

### 核心节点
| 节点 | 用途 | 访问地址 |
|------|------|----------|
| oge0 | 前端 | http://10.101.240.20/ |
| oge1 | 后端 | http://10.101.240.20/ |
| ogecal0 | 计算集群主节点 | http://10.101.240.10 |
| ogeMiniO | MinIO存储 | http://10.101.240.23:9007 |

### 大数据组件
| 组件 | Web UI | API端口 |
|------|--------|---------|
| Spark Master | http://10.101.240.10:9091 | - |
| Hadoop | http://10.101.240.10:8088 | - |
| HBase | http://10.101.240.10:16010 | - |
| Livy | http://10.101.240.10:8998 | 8998 |

## 部署步骤

### 1. 环境准备

#### 1.1 创建部署目录
```bash
sudo mkdir -p /opt/yaogan-mcp
cd /opt/yaogan-mcp
```

#### 1.2 创建Conda环境
```bash
# 创建专用环境
conda create -n mcpserver python=3.9 -y

# 激活环境
conda activate mcpserver

# 安装依赖
pip install fastmcp starlette uvicorn httpx pydantic
```

### 2. 部署文件

#### 2.1 上传文件
将以下文件上传到 `/opt/yaogan-mcp/` 目录：

1. `shandong_mcp_server_enhanced-整体流程-提示词完善版.py` - 主服务器文件（已适配）
2. `yaogan_environment_config.py` - 环境配置文件
3. `yaogan-mcp-server-run.sh` - 启动脚本

#### 2.2 设置权限
```bash
# 设置文件权限
chmod +x /opt/yaogan-mcp/yaogan-mcp-server-run.sh

# 创建日志目录
mkdir -p /opt/yaogan-mcp/logs
```

### 3. 环境检查

#### 3.1 检查网络连通性
```bash
# 使用启动脚本检查环境
./yaogan-mcp-server-run.sh check
```

#### 3.2 手动检查核心服务
```bash
# 检查前端
curl -I http://10.101.240.20

# 检查计算集群
curl -I http://10.101.240.10:9091

# 检查MinIO
curl -I http://10.101.240.23:9007
```

### 4. 启动服务

#### 4.1 首次启动
```bash
# 使用默认端口8000启动
./yaogan-mcp-server-run.sh start

# 或指定其他端口
./yaogan-mcp-server-run.sh start 8001
```

#### 4.2 验证启动
```bash
# 检查服务状态
./yaogan-mcp-server-run.sh status

# 检查健康状态
curl http://localhost:8000/health

# 查看服务信息
curl http://localhost:8000/info
```

### 5. 配置验证

#### 5.1 环境连通性测试
访问服务信息端点，验证环境配置：
```bash
curl -s http://localhost:8000/info | python -m json.tool
```

#### 5.2 服务功能测试
使用MCP客户端测试 `check_yaogan_environment` 工具：
```json
{
  "method": "tools/call",
  "params": {
    "name": "check_yaogan_environment",
    "arguments": {}
  }
}
```

## 配置说明

### 关键配置项

#### API端点配置
```python
# 前端和后端
OGE_FRONTEND_URL = "http://10.101.240.20"
OGE_BACKEND_URL = "http://10.101.240.20"

# 计算集群
COMPUTE_CLUSTER_MASTER = "http://10.101.240.10"
DAG_API_BASE_URL = "http://10.101.240.10:8998/api/oge-dag"

# MinIO存储
MINIO_ENDPOINT = "http://10.101.240.23:9007"
MINIO_ACCESS_KEY = "oge"
MINIO_SECRET_KEY = "ypfamily608"
```

#### 认证配置
```python
DEFAULT_USERNAME = "oge_admin"
DEFAULT_USER_ID = "yaogan-building-user"
```

### 启动脚本配置

编辑 `yaogan-mcp-server-run.sh` 中的路径：
```bash
# 根据实际部署位置调整
SCRIPT_PATH="/opt/yaogan-mcp/shandong_mcp_server_enhanced-整体流程-提示词完善版.py"
CONDA_ENV_NAME="mcpserver"
```

## 管理操作

### 服务管理
```bash
# 启动服务
./yaogan-mcp-server-run.sh start [port]

# 停止服务
./yaogan-mcp-server-run.sh stop [port]

# 重启服务
./yaogan-mcp-server-run.sh restart [port]

# 查看状态
./yaogan-mcp-server-run.sh status [port]

# 检查环境
./yaogan-mcp-server-run.sh check

# 安装依赖
./yaogan-mcp-server-run.sh install
```

### 日志查看
```bash
# 查看主要日志
tail -f /opt/yaogan-mcp/logs/yaogan_server_8000.log

# 查看MCP日志
tail -f /opt/yaogan-mcp/logs/yaogan_mcp.log

# 查看API调用日志
tail -f /opt/yaogan-mcp/logs/api_calls.log
```

## 故障排除

### 常见问题

#### 1. 服务无法启动
**问题**: 服务启动失败
**解决**:
```bash
# 检查Python环境
which python
conda info --envs

# 检查依赖
pip list | grep -E "(fastmcp|starlette|uvicorn)"

# 查看详细错误
cat /opt/yaogan-mcp/logs/yaogan_server_8000.log
```

#### 2. 网络连接问题
**问题**: 无法连接到遥感大楼服务
**解决**:
```bash
# 检查网络连通性
./yaogan-mcp-server-run.sh check

# 手动测试连接
ping 10.101.240.20
ping 10.101.240.10
ping 10.101.240.23
```

#### 3. Token认证问题
**问题**: API调用认证失败
**解决**:
- 使用 `refresh_token` 工具手动刷新
- 检查用户名密码配置
- 确认认证API端点正确

#### 4. 端口冲突
**问题**: 端口已被占用
**解决**:
```bash
# 检查端口使用
netstat -tlnp | grep 8000

# 使用其他端口启动
./yaogan-mcp-server-run.sh start 8001
```

### 日志级别调整
在服务器代码中修改日志级别：
```python
logger = setup_logger("yaogan_mcp", "logs/yaogan_mcp.log", level=logging.DEBUG)
```

## 性能优化

### 建议配置

#### 1. 系统资源
- **内存**: 最小4GB，推荐8GB+
- **CPU**: 最小2核，推荐4核+
- **磁盘**: 预留足够空间用于日志和临时文件

#### 2. 网络优化
- 确保到各服务节点的网络延迟最小
- 考虑部署在与计算集群相同的网段

#### 3. 并发配置
根据需要调整Uvicorn并发设置：
```python
uvicorn.run(starlette_app, host=host, port=port, workers=4)
```

## 安全考虑

### 网络安全
- 仅在内网环境使用
- 配置防火墙规则限制访问
- 定期更新认证凭据

### 数据安全
- 定期备份重要配置
- 监控日志文件大小
- 使用强密码

## 监控和维护

### 健康检查
定期检查服务状态：
```bash
# 自动化健康检查脚本
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart yaogan-mcp
```

### 日志轮换
配置logrotate防止日志文件过大：
```bash
# /etc/logrotate.d/yaogan-mcp
/opt/yaogan-mcp/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    copytruncate
}
```

## 技术支持

如遇到问题，请按以下步骤操作：

1. **环境检查**: 运行 `./yaogan-mcp-server-run.sh check`
2. **日志分析**: 查看相关日志文件
3. **服务重启**: 尝试重启服务
4. **配置验证**: 确认所有配置项正确

---

**部署完成后，您将拥有一个完全适配遥感大楼环境的MCP服务器，支持山东耕地流出分析的各种功能。** 