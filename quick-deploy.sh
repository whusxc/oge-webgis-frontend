#!/usr/bin/env bash

# 遥感大楼MCP服务器快速部署脚本
# 自动化完成整个部署过程

set -e  # 出错时停止

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
DEPLOY_DIR="/opt/yaogan-mcp"
CONDA_ENV_NAME="mcpserver"
DEFAULT_PORT=8000

# 打印彩色信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查运行权限
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 检查网络连通性
check_network() {
    print_info "检查遥感大楼网络环境..."
    
    local services=(
        "10.101.240.20:80:OGE前端"
        "10.101.240.10:9091:Spark Master"
        "10.101.240.10:8088:Hadoop"
        "10.101.240.23:9007:MinIO"
    )
    
    local failed=0
    
    for service in "${services[@]}"; do
        IFS=':' read -r ip port name <<< "$service"
        if timeout 5 bash -c "</dev/tcp/$ip/$port" 2>/dev/null; then
            print_success "$name ($ip:$port) - 可访问"
        else
            print_warning "$name ($ip:$port) - 无法访问"
            ((failed++))
        fi
    done
    
    if [[ $failed -gt 0 ]]; then
        print_warning "有 $failed 个服务无法访问，请检查网络连接"
        read -p "是否继续部署？(y/N): " continue_deploy
        if [[ ! $continue_deploy =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查conda
    if ! command -v conda &> /dev/null; then
        print_error "未找到conda，请先安装Anaconda或Miniconda"
        echo "下载地址: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi
    print_success "Conda 已安装"
    
    # 检查curl
    if ! command -v curl &> /dev/null; then
        print_info "安装curl..."
        apt-get update && apt-get install -y curl
    fi
    print_success "Curl 已安装"
    
    # 检查Python版本
    python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
    if [[ $(echo "$python_version >= 3.9" | bc -l 2>/dev/null || echo 0) -eq 1 ]]; then
        print_success "Python $python_version 版本符合要求"
    else
        print_warning "Python版本为 $python_version，建议使用3.9+"
    fi
}

# 创建部署目录
create_deploy_dir() {
    print_info "创建部署目录..."
    
    if [[ -d "$DEPLOY_DIR" ]]; then
        print_warning "目录 $DEPLOY_DIR 已存在"
        read -p "是否删除并重新创建？(y/N): " recreate
        if [[ $recreate =~ ^[Yy]$ ]]; then
            rm -rf "$DEPLOY_DIR"
            print_info "已删除旧目录"
        fi
    fi
    
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR/logs"
    
    print_success "部署目录创建完成: $DEPLOY_DIR"
}

# 创建conda环境
create_conda_env() {
    print_info "创建Conda环境..."
    
    # 检查环境是否已存在
    if conda env list | grep -q "$CONDA_ENV_NAME"; then
        print_warning "Conda环境 $CONDA_ENV_NAME 已存在"
        read -p "是否删除并重新创建？(y/N): " recreate_env
        if [[ $recreate_env =~ ^[Yy]$ ]]; then
            conda env remove -n "$CONDA_ENV_NAME" -y
            print_info "已删除旧环境"
        else
            print_info "使用现有环境"
            return
        fi
    fi
    
    # 创建新环境
    conda create -n "$CONDA_ENV_NAME" python=3.9 -y
    print_success "Conda环境创建完成"
}

# 安装Python依赖
install_python_deps() {
    print_info "安装Python依赖..."
    
    # 激活conda环境
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_NAME"
    
    # 安装依赖包
    pip install --upgrade pip
    pip install fastmcp starlette uvicorn httpx pydantic
    
    print_success "Python依赖安装完成"
}

# 检查并复制文件
copy_files() {
    print_info "检查必需文件..."
    
    local required_files=(
        "shandong_mcp_server_enhanced-整体流程-提示词完善版.py"
        "yaogan_environment_config.py"
        "yaogan-mcp-server-run.sh"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            cp "$file" "$DEPLOY_DIR/"
            print_success "复制文件: $file"
        else
            missing_files+=("$file")
            print_error "缺少文件: $file"
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_error "缺少 ${#missing_files[@]} 个必需文件，请确保以下文件在当前目录："
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    # 设置执行权限
    chmod +x "$DEPLOY_DIR/yaogan-mcp-server-run.sh"
    print_success "文件权限设置完成"
}

# 配置系统服务（可选）
setup_systemd_service() {
    read -p "是否创建systemd服务以自动启动？(y/N): " create_service
    
    if [[ $create_service =~ ^[Yy]$ ]]; then
        print_info "创建systemd服务..."
        
        cat > /etc/systemd/system/yaogan-mcp.service << EOF
[Unit]
Description=Yaogan Building MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOY_DIR
ExecStart=$DEPLOY_DIR/yaogan-mcp-server-run.sh start $DEFAULT_PORT
ExecStop=$DEPLOY_DIR/yaogan-mcp-server-run.sh stop $DEFAULT_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        systemctl enable yaogan-mcp.service
        
        print_success "Systemd服务创建完成"
        print_info "使用以下命令管理服务："
        echo "  启动: systemctl start yaogan-mcp"
        echo "  停止: systemctl stop yaogan-mcp"
        echo "  状态: systemctl status yaogan-mcp"
    fi
}

# 测试部署
test_deployment() {
    print_info "测试部署..."
    
    cd "$DEPLOY_DIR"
    
    # 环境检查
    print_info "运行环境检查..."
    ./yaogan-mcp-server-run.sh check
    
    # 尝试启动服务
    print_info "启动MCP服务..."
    ./yaogan-mcp-server-run.sh start $DEFAULT_PORT
    
    # 等待服务启动
    sleep 5
    
    # 健康检查
    if curl -f "http://localhost:$DEFAULT_PORT/health" > /dev/null 2>&1; then
        print_success "MCP服务启动成功！"
        print_info "服务信息:"
        echo "  - 访问地址: http://localhost:$DEFAULT_PORT"
        echo "  - 健康检查: http://localhost:$DEFAULT_PORT/health"
        echo "  - 服务信息: http://localhost:$DEFAULT_PORT/info"
    else
        print_error "MCP服务启动失败"
        print_info "查看日志: tail -f $DEPLOY_DIR/logs/yaogan_server_$DEFAULT_PORT.log"
        return 1
    fi
}

# 生成使用说明
generate_usage_info() {
    print_info "生成使用说明..."
    
    cat > "$DEPLOY_DIR/README.txt" << EOF
遥感大楼MCP服务器部署完成！

部署信息:
- 部署目录: $DEPLOY_DIR
- Conda环境: $CONDA_ENV_NAME
- 服务端口: $DEFAULT_PORT

管理命令:
cd $DEPLOY_DIR

# 服务管理
./yaogan-mcp-server-run.sh start [port]     # 启动服务
./yaogan-mcp-server-run.sh stop [port]      # 停止服务
./yaogan-mcp-server-run.sh restart [port]   # 重启服务
./yaogan-mcp-server-run.sh status [port]    # 查看状态

# 环境检查
./yaogan-mcp-server-run.sh check           # 检查环境连通性

# 日志查看
tail -f logs/yaogan_server_$DEFAULT_PORT.log    # 服务日志
tail -f logs/yaogan_mcp.log                     # MCP日志
tail -f logs/api_calls.log                      # API调用日志

访问地址:
- 健康检查: http://localhost:$DEFAULT_PORT/health
- 服务信息: http://localhost:$DEFAULT_PORT/info

MCP工具:
- check_yaogan_environment: 检查环境连通性
- farmland_outflow: 耕地流出分析
- refresh_token: 刷新认证Token
- 更多工具请查看服务信息页面

故障排除:
1. 服务启动失败 -> 查看日志文件
2. 网络连接问题 -> 运行环境检查
3. 认证问题 -> 使用refresh_token工具

EOF

    print_success "使用说明已生成: $DEPLOY_DIR/README.txt"
}

# 主函数
main() {
    echo "=========================================="
    echo "   遥感大楼MCP服务器快速部署脚本"
    echo "=========================================="
    echo ""
    
    # 检查权限
    check_permissions
    
    # 检查网络
    check_network
    
    # 检查依赖
    check_dependencies
    
    # 创建部署目录
    create_deploy_dir
    
    # 创建conda环境
    create_conda_env
    
    # 安装Python依赖
    install_python_deps
    
    # 复制文件
    copy_files
    
    # 设置系统服务
    setup_systemd_service
    
    # 测试部署
    if test_deployment; then
        # 生成使用说明
        generate_usage_info
        
        echo ""
        echo "=========================================="
        print_success "部署完成！"
        echo "=========================================="
        echo ""
        print_info "部署摘要:"
        echo "  - 部署目录: $DEPLOY_DIR"
        echo "  - 服务端口: $DEFAULT_PORT"
        echo "  - 服务状态: 运行中"
        echo ""
        print_info "下一步操作:"
        echo "  1. 访问 http://localhost:$DEFAULT_PORT/info 查看服务信息"
        echo "  2. 阅读 $DEPLOY_DIR/README.txt 了解详细使用方法"
        echo "  3. 使用MCP客户端连接服务器进行测试"
        echo ""
    else
        print_error "部署测试失败，请检查日志并手动排除问题"
        exit 1
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 