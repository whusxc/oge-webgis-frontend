#!/bin/bash

# OGE 前端快速部署脚本
# 适用于开发和生产环境

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查Node.js环境
check_node() {
    print_step "检查Node.js环境..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装，请先安装Node.js 16+"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        print_error "Node.js版本过低，需要16+，当前版本: $(node -v)"
        exit 1
    fi
    
    print_message "Node.js版本: $(node -v) ✓"
}

# 检查npm/pnpm
check_package_manager() {
    print_step "检查包管理器..."
    
    if command -v pnpm &> /dev/null; then
        PACKAGE_MANAGER="pnpm"
        print_message "使用 pnpm"
    elif command -v npm &> /dev/null; then
        PACKAGE_MANAGER="npm"
        print_message "使用 npm"
    else
        print_error "未找到npm或pnpm"
        exit 1
    fi
}

# 安装依赖
install_dependencies() {
    print_step "安装项目依赖..."
    
    if [ ! -f "package.json" ]; then
        print_error "package.json 文件不存在"
        exit 1
    fi
    
    $PACKAGE_MANAGER install
    print_message "依赖安装完成 ✓"
}

# 开发模式
dev_mode() {
    print_step "启动开发服务器..."
    print_message "访问地址: http://localhost:3000"
    print_warning "按 Ctrl+C 停止服务"
    
    $PACKAGE_MANAGER run dev
}

# 构建生产版本
build_production() {
    print_step "构建生产版本..."
    
    # 清理旧的构建文件
    if [ -d "dist" ]; then
        rm -rf dist
        print_message "已清理旧构建文件"
    fi
    
    # 执行构建
    $PACKAGE_MANAGER run build
    
    if [ -d "dist" ]; then
        print_message "构建完成 ✓"
        print_message "构建文件位于: ./dist"
    else
        print_error "构建失败"
        exit 1
    fi
}

# 部署到Nginx
deploy_nginx() {
    print_step "部署到Nginx..."
    
    # 默认Nginx路径
    NGINX_PATH="/usr/share/nginx/html/oge-gaplus"
    
    if [ ! -z "$1" ]; then
        NGINX_PATH="$1"
    fi
    
    print_message "部署路径: $NGINX_PATH"
    
    # 检查是否有权限
    if [ ! -w "$(dirname "$NGINX_PATH")" ]; then
        print_warning "需要管理员权限，请输入密码"
        sudo mkdir -p "$NGINX_PATH"
        sudo cp -r dist/* "$NGINX_PATH/"
        sudo chown -R www-data:www-data "$NGINX_PATH"
    else
        mkdir -p "$NGINX_PATH"
        cp -r dist/* "$NGINX_PATH/"
    fi
    
    print_message "部署完成 ✓"
}

# 创建Nginx配置
create_nginx_config() {
    print_step "创建Nginx配置..."
    
    cat > nginx.conf << EOF
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html/oge-gaplus;
    index index.html;
    
    # Gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Vue Router History模式支持
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API代理到MCP服务
    location /api/mcp/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # API代理到OGE服务
    location /api/oge/ {
        proxy_pass http://10.101.240.20/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    print_message "Nginx配置已生成: nginx.conf"
    print_warning "请将配置复制到 /etc/nginx/sites-available/ 并启用"
}

# 部署到Docker
deploy_docker() {
    print_step "创建Docker配置..."
    
    # 创建Dockerfile
    cat > Dockerfile << EOF
FROM nginx:alpine

# 复制构建文件
COPY dist/ /usr/share/nginx/html/

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

    # 创建docker-compose.yml
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  oge-gaplus-frontend:
    build: .
    ports:
      - "3000:80"
    container_name: oge-gaplus-frontend
    restart: unless-stopped
    networks:
      - oge-network

networks:
  oge-network:
    external: true
EOF

    print_message "Docker配置已生成"
    print_message "使用命令: docker-compose up -d"
}

# 显示帮助信息
show_help() {
    echo "OGE 前端部署脚本"
    echo ""
    echo "用法: ./deploy.sh [选项]"
    echo ""
    echo "选项:"
    echo "  dev                    启动开发服务器"
    echo "  build                  构建生产版本"
    echo "  deploy [path]          部署到指定路径(默认nginx路径)"
    echo "  nginx                  创建Nginx配置文件"
    echo "  docker                 创建Docker配置"
    echo "  full [path]            完整部署(install + build + deploy)"
    echo "  help                   显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh dev        # 开发模式"
    echo "  ./deploy.sh build      # 构建"
    echo "  ./deploy.sh full       # 完整部署"
    echo "  ./deploy.sh deploy /var/www/html/oge  # 部署到指定路径"
}

# 主函数
main() {
    print_message "OGE 前端部署脚本启动"
    print_message "=============================="
    
    # 检查基础环境
    check_node
    check_package_manager
    
    case "${1:-help}" in
        "dev")
            install_dependencies
            dev_mode
            ;;
        "build")
            install_dependencies
            build_production
            ;;
        "deploy")
            if [ ! -d "dist" ]; then
                print_error "构建文件不存在，请先运行 build"
                exit 1
            fi
            deploy_nginx "$2"
            ;;
        "nginx")
            create_nginx_config
            ;;
        "docker")
            if [ ! -d "dist" ]; then
                print_error "构建文件不存在，请先运行 build"
                exit 1
            fi
            create_nginx_config
            deploy_docker
            ;;
        "full")
            install_dependencies
            build_production
            deploy_nginx "$2"
            print_message "=============================="
            print_message "部署完成！"
            print_message "访问地址: http://localhost (如果部署到默认路径)"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@" 