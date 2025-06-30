# OGE WebGIS 前端平台

基于OGE和MCP的智能地理分析平台前端。

## 🌟 项目特性

- **🗺️ 地图可视化**: 基于Mapbox GL JS的高性能地图渲染
- **🔧 MCP工具集成**: 完整的地理分析工具（坡度分析、缓冲区分析、耕地流出分析等）
- **🤖 AI智能助手**: 集成GPT/ChatGLM的智能对话和分析建议
- **📊 数据管理**: 图层管理、数据导入导出、结果可视化
- **⚡ 现代技术栈**: Vue 3 + Vite + Element Plus + TypeScript
- **📱 响应式设计**: 支持桌面和移动设备
- **🐳 容器化部署**: 支持Docker和传统部署方式

## 🏗️ 技术架构

```
┌─────────────────┬─────────────────┬─────────────────┐
│   前端展示层     │    业务逻辑层     │     数据服务层    │
├─────────────────┼─────────────────┼─────────────────┤
│ Vue 3           │ MCP API         │ MCP服务器        │
│ Mapbox GL JS    │ AI Chat API     │ 遥感大楼环境      │
│ Element Plus    │ 状态管理         │ MinIO存储        │
│ TypeScript      │ 路由管理         │ PostgreSQL      │
└─────────────────┴─────────────────┴─────────────────┘
```

## 📦 快速开始

### 环境要求

- Node.js 16+ 
- npm 或 pnpm
- 现代浏览器(支持ES6+)

### 安装和运行

```bash
# 1. 克隆项目
git clone <repository-url>
cd oge-webgis

# 2. 安装依赖
npm install
# 或使用 pnpm
pnpm install

# 3. 开发模式
npm run dev

# 4. 构建生产版本
npm run build

# 5. 本地预览构建结果
npm run preview
```

### 使用部署脚本

项目提供了便捷的部署脚本：

```bash
# 给脚本执行权限
chmod +x deploy.sh

# 开发模式
./deploy.sh dev

# 完整部署（安装+构建+部署）
./deploy.sh full

# 部署到指定路径
./deploy.sh deploy /var/www/html/oge

# 创建Docker配置
./deploy.sh docker

# 查看帮助
./deploy.sh help
```

## 🎯 功能模块

### 1. 地图视图 (`MapView`)
- 多种底图样式选择
- 图层管理和控制
- 地图交互操作
- 空间数据可视化

### 2. MCP工具箱 (`McpToolBar`)
- **地形分析**: 坡度分析、高程分析
- **空间分析**: 缓冲区分析、叠加分析
- **农业分析**: 耕地流出、作物分类
- **特征提取**: 道路提取、水体提取
- **影像分类**: 遥感影像智能分类

### 3. 智能助手 (`ChatBox`)
- 自然语言交互
- 智能工具推荐
- 分析结果解释
- 操作指导

### 4. 图层管理 (`LayerPanel`)
- 图层增删改查
- 样式和透明度调整
- 图层信息查看
- 结果图层管理

### 5. 任务中心 (`TaskProgress`)
- 任务状态监控
- 进度实时更新
- 结果预览和下载
- 错误处理和重试

## 🔧 配置说明

### 环境配置

项目支持多环境配置，主要配置项位于 `src/stores/app.js`:

```javascript
// MCP服务配置
mcp: {
  baseUrl: 'http://localhost:8000',  // MCP服务器地址
  timeout: 30000
},

// OGE服务配置  
oge: {
  baseUrl: 'http://10.101.240.20',  // 遥感大楼OGE服务
  port: 16555
},

// Mapbox配置
mapbox: {
  accessToken: 'your-mapbox-token',  // 需要替换为您的token
  style: 'mapbox://styles/mapbox/streets-v11',
  center: [116.3974, 39.9093],  // 北京坐标
  zoom: 10
}
```

### API代理配置

开发环境下，API请求通过Vite代理转发：

```javascript
// vite.config.js
proxy: {
  '/api/mcp': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/mcp/, '')
  },
  '/api/oge': {
    target: 'http://10.101.240.20:16555',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/oge/, '')
  }
}
```

## 🚀 部署方案

### 1. Nginx部署

```bash
# 构建项目
npm run build

# 复制到Nginx目录
sudo cp -r dist/* /usr/share/nginx/html/oge/

# 配置Nginx
sudo cp nginx.conf /etc/nginx/sites-available/oge
sudo ln -s /etc/nginx/sites-available/oge /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 2. Docker部署

```bash
# 使用部署脚本
./deploy.sh docker

# 或手动构建
docker build -t oge-frontend .
docker run -d -p 3000:80 --name oge oge-frontend
```

### 3. Docker Compose部署

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🔌 MCP服务集成

### 服务地址配置

确保MCP服务器正常运行在遥感大楼环境：

```bash
# 检查MCP服务状态
curl http://localhost:8000/health

# 检查工具列表
curl http://localhost:8000/tools

# 测试坡度分析
curl -X POST http://localhost:8000/slope_analysis \
  -H "Content-Type: application/json" \
  -d '{"area": "beijing"}'
```

### API接口说明

| 接口 | 方法 | 说明 |
|-----|-----|-----|
| `/health` | GET | 健康检查 |
| `/tools` | GET | 获取可用工具列表 |
| `/slope_analysis` | POST | 坡度分析 |
| `/buffer_analysis` | POST | 缓冲区分析 |
| `/farmland_outflow` | POST | 耕地流出分析 |
| `/road_extraction` | POST | 道路提取 |
| `/water_extraction` | POST | 水体提取 |

## 📊 监控和日志

### 应用监控

- 前端错误监控
- API请求监控  
- 用户行为分析
- 性能指标监控

### 日志管理

```bash
# 查看应用日志
docker logs oge-gaplus-frontend

# 查看Nginx访问日志
tail -f /var/log/nginx/access.log

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log
```

## 🛠️ 开发指南

### 目录结构

```
src/
├── components/          # 可复用组件
│   ├── LayerPanel.vue   # 图层控制面板
│   ├── McpToolBar.vue   # MCP工具栏
│   ├── ChatBox.vue      # 智能助手
│   └── TaskProgress.vue # 任务进度
├── views/               # 页面组件
│   ├── MapView.vue      # 地图主视图
│   ├── Login.vue        # 登录页面
│   └── Dashboard.vue    # 控制台
├── stores/              # 状态管理
│   └── app.js           # 应用状态
├── services/            # API服务
│   └── api.js           # API封装
├── router/              # 路由配置
│   └── index.js         # 路由定义
└── assets/              # 静态资源
    └── styles/          # 样式文件
```

### 添加新工具

1. 在 `McpToolBar.vue` 中添加工具定义
2. 实现工具参数表单
3. 调用MCP API
4. 处理返回结果并显示在地图上

### 样式开发

项目使用SCSS，支持变量和混入：

```scss
// 使用CSS变量
.my-component {
  color: var(--primary-color);
  background: var(--background-color-base);
}

// 使用工具类
.my-layout {
  @extend .flex-between;
  @extend .p-20;
}
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/new-feature`
3. 提交变更: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有建议，请：

1. 查看[常见问题](docs/FAQ.md)
2. 搜索现有[Issues](issues)
3. 创建新的Issue
4. 联系开发团队

## 📝 更新日志

### v1.0.0 (2024-12-XX)
- ✨ 初始版本发布
- 🗺️ 地图基础功能
- 🔧 MCP工具集成
- 🤖 AI助手功能
- 📊 图层管理
- 🚀 部署脚本 