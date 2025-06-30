#!/usr/bin/env bash

# 遥感大楼MCP服务管理脚本
# 用法: ./yaogan-mcp-server-run.sh {start|stop|restart|status} [port]
# 如果未指定端口, 默认使用 8000

# ------------------ 配置区域 ------------------
# 遥感大楼环境特定配置
ENVIRONMENT="yaogan-building"
CONDA_ENV_NAME="mcpserver"
CONDA_BASE=$(conda info --base)
PYTHON_BIN="$CONDA_BASE/envs/$CONDA_ENV_NAME/bin/python"

# 脚本路径 - 需要根据实际部署位置调整
SCRIPT_PATH="/opt/yaogan-mcp/shandong_mcp_server_enhanced-遥感大楼适配版.py"
DEFAULT_PORT=8000

# 环境检查URLs
FRONTEND_URL="http://10.101.240.20"
COMPUTE_MASTER="http://10.101.240.10"
MINIO_URL="http://10.101.240.23:9007"

# ------------------ 解析参数 ------------------
ACTION="$1"
PORT_ARG="$2"

if [[ "$PORT_ARG" =~ ^[0-9]+$ ]]; then
    PORT="$PORT_ARG"
else
    PORT="$DEFAULT_PORT"
fi

SERVICE_ARGS="--mode http --host 0.0.0.0 --port $PORT"
WORKDIR=$(dirname "$SCRIPT_PATH")
LOG_FILE="$WORKDIR/logs/yaogan_server_${PORT}.log"
PID_FILE="/var/run/yaogan_mcp_service_${PORT}.pid"

# ------------------ 环境检查函数 ------------------
check_environment() {
    echo "======================================="
    echo "遥感大楼环境连通性检查"
    echo "======================================="
    
    # 检查前端服务
    echo -n "检查OGE前端 ($FRONTEND_URL): "
    if curl -s --connect-timeout 5 "$FRONTEND_URL" > /dev/null 2>&1; then
        echo "✓ 可访问"
    else
        echo "✗ 无法访问"
    fi
    
    # 检查计算集群主节点
    echo -n "检查计算集群主节点 ($COMPUTE_MASTER): "
    if curl -s --connect-timeout 5 "$COMPUTE_MASTER" > /dev/null 2>&1; then
        echo "✓ 可访问"
    else
        echo "✗ 无法访问"
    fi
    
    # 检查MinIO
    echo -n "检查MinIO存储 ($MINIO_URL): "
    if curl -s --connect-timeout 5 "$MINIO_URL" > /dev/null 2>&1; then
        echo "✓ 可访问"
    else
        echo "✗ 无法访问"
    fi
    
    # 检查大数据组件
    echo -n "检查Spark Master UI (${COMPUTE_MASTER}:9091): "
    if curl -s --connect-timeout 5 "${COMPUTE_MASTER}:9091" > /dev/null 2>&1; then
        echo "✓ 可访问"
    else
        echo "✗ 无法访问"
    fi
    
    echo -n "检查Hadoop Web UI (${COMPUTE_MASTER}:8088): "
    if curl -s --connect-timeout 5 "${COMPUTE_MASTER}:8088" > /dev/null 2>&1; then
        echo "✓ 可访问"
    else
        echo "✗ 无法访问"
    fi
    
    echo -n "检查Livy API (${COMPUTE_MASTER}:8998): "
    if curl -s --connect-timeout 5 "${COMPUTE_MASTER}:8998" > /dev/null 2>&1; then
        echo "✓ 可访问"
    else
        echo "✗ 无法访问"
    fi
    
    echo "======================================="
}

# ------------------ 功能函数 ------------------
start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        echo "遥感大楼MCP服务已在运行 (端口: $PORT, PID: $(cat "$PID_FILE"))"
    else
        echo "正在启动遥感大楼MCP服务 (端口: $PORT)..."
        
        # 检查脚本文件是否存在
        if [ ! -f "$SCRIPT_PATH" ]; then
            echo "错误: 脚本文件不存在: $SCRIPT_PATH"
            echo "请确保已正确部署MCP服务器文件"
            exit 1
        fi
        
        # 检查conda环境
        if [ ! -f "$PYTHON_BIN" ]; then
            echo "错误: Conda环境不存在: $CONDA_ENV_NAME"
            echo "请先创建conda环境: conda create -n $CONDA_ENV_NAME python=3.9"
            exit 1
        fi
        
        # 创建日志目录
        mkdir -p "$WORKDIR/logs"
        
        # 启动服务
        cd "$WORKDIR" || exit 1
        nohup "$PYTHON_BIN" "$SCRIPT_PATH" $SERVICE_ARGS > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        
        # 等待服务启动
        sleep 3
        
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
            echo "遥感大楼MCP服务启动成功!"
            echo "  - 端口: $PORT"
            echo "  - PID: $(cat "$PID_FILE")"
            echo "  - 日志: $LOG_FILE"
            echo "  - 健康检查: http://localhost:$PORT/health"
            echo "  - 环境信息: http://localhost:$PORT/info"
        else
            echo "服务启动失败，请检查日志: $LOG_FILE"
            exit 1
        fi
    fi
}

stop() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        echo "正在停止遥感大楼MCP服务 (端口: $PORT, PID: $(cat "$PID_FILE"))..."
        kill "$(cat "$PID_FILE")"
        rm -f "$PID_FILE"
        echo "服务已停止 (端口: $PORT)"
    else
        echo "服务未运行 (端口: $PORT)"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        echo "遥感大楼MCP服务正在运行"
        echo "  - 端口: $PORT"
        echo "  - PID: $(cat "$PID_FILE")"
        echo "  - 环境: $ENVIRONMENT"
        echo "  - 日志: $LOG_FILE"
        echo "  - 健康检查: http://localhost:$PORT/health"
    else
        echo "服务未运行 (端口: $PORT)"
    fi
}

restart() {
    stop
    sleep 2
    start
}

install_deps() {
    echo "正在安装遥感大楼MCP服务依赖..."
    
    # 激活conda环境并安装依赖
    source "$CONDA_BASE/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_NAME"
    
    pip install fastmcp starlette uvicorn httpx pydantic
    
    echo "依赖安装完成"
}

# ------------------ 脚本入口 ------------------
case "$ACTION" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    check)
        check_environment
        ;;
    install)
        install_deps
        ;;
    *)
        echo "遥感大楼MCP服务管理脚本"
        echo ""
        echo "用法: $0 {start|stop|restart|status|check|install} [port]"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动MCP服务"
        echo "  stop    - 停止MCP服务"
        echo "  restart - 重启MCP服务"
        echo "  status  - 查看服务状态"
        echo "  check   - 检查环境连通性"
        echo "  install - 安装Python依赖"
        echo ""
        echo "参数说明:"
        echo "  port    - 可选，指定服务端口 (默认: $DEFAULT_PORT)"
        echo ""
        echo "示例:"
        echo "  $0 start         # 使用默认端口8000启动"
        echo "  $0 start 8001    # 使用端口8001启动"
        echo "  $0 check         # 检查遥感大楼环境连通性"
        exit 1
        ;;
esac 