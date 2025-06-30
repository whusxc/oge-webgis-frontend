#!/usr/bin/env bash

# MCP 服务管理脚本 (使用 Conda 环境 mcpserver)
# 用法: ./mcp_service.sh {start|stop|restart|status} [port]
# 如果未指定端口, 默认使用 8000

# ------------------ 配置区域 ------------------
CONDA_ENV_NAME="mcpserver"
CONDA_BASE=$(conda info --base)                  # Conda 根目录
PYTHON_BIN="$CONDA_BASE/envs/$CONDA_ENV_NAME/bin/python"  # 目标 Python
SCRIPT_PATH="/home/mcp/new_server/shandong_mcp_server_enhanced.py"   # 业务脚本

DEFAULT_PORT=8000                               # 默认端口

# ------------------ 解析参数 ------------------
ACTION="$1"                                     # 第一个参数: 动作
PORT_ARG="$2"                                  # 第二个参数: 端口(可选)

# 如果传入的端口为纯数字则覆盖默认端口
if [[ "$PORT_ARG" =~ ^[0-9]+$ ]]; then
    PORT="$PORT_ARG"
else
    PORT="$DEFAULT_PORT"
fi

SERVICE_ARGS="--mode http --host 0.0.0.0 --port $PORT"      # 构造启动参数

WORKDIR=$(dirname "$SCRIPT_PATH")               # 工作目录
LOG_FILE="$WORKDIR/logs/server_${PORT}.log"      # 端口相关日志文件
PID_FILE="/var/run/mcp_service_${PORT}.pid"       # 端口相关 PID 文件

# ------------------ 功能函数 ------------------
start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        echo "服务已在运行 (端口: $PORT, PID: $(cat "$PID_FILE"))"
    else
        echo "正在启动服务 (端口: $PORT)..."
        cd "$WORKDIR" || exit 1
        nohup "$PYTHON_BIN" "$SCRIPT_PATH" $SERVICE_ARGS > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "服务启动成功 (端口: $PORT, PID: $(cat "$PID_FILE"))"
    fi
}

stop() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        echo "正在停止服务 (端口: $PORT, PID: $(cat "$PID_FILE"))..."
        kill "$(cat "$PID_FILE")"
        rm -f "$PID_FILE"
        echo "服务已停止 (端口: $PORT)"
    else
        echo "服务未运行 (端口: $PORT)"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        echo "服务正在运行 (端口: $PORT, PID: $(cat "$PID_FILE"))"
    else
        echo "服务未运行 (端口: $PORT)"
    fi
}

restart() {
    stop
    sleep 1
    start
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
    *)
        echo "用法: $0 {start|stop|restart|status} [port]"
        exit 1
        ;;
esac