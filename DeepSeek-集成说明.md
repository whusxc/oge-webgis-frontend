# OGE WebGIS + DeepSeek AI 集成说明

## 🎯 功能特性

✅ **DeepSeek AI 聊天助手** - 智能对话和问答  
✅ **MCP 工具自动调用** - 通过DeepSeek调用地理分析工具  
✅ **实时工具执行** - 坡度分析、缓冲区分析、环境检查等  
✅ **对话历史管理** - 完整的上下文理解  
✅ **智能错误处理** - 优雅的降级和重试机制  
✅ **工具执行可视化** - 直观显示工具调用过程

## 🚀 快速开始

### 1. 获取DeepSeek API密钥

1. 访问 [DeepSeek 官网](https://www.deepseek.com)
2. 注册账号并登录
3. 进入API管理页面
4. 创建新的API密钥
5. 复制密钥（格式：`sk-xxxxxxxxxxxxxxxx`）

### 2. 配置环境变量

在 `oge-webgis-frontend` 目录下创建 `.env.local` 文件：

```env
# DeepSeek AI API 配置
VITE_DEEPSEEK_API_KEY=sk-your-real-api-key-here

# MCP 服务器配置
VITE_MCP_SERVER_URL=http://localhost:8000

# AI 服务配置  
VITE_AI_PROVIDER=deepseek
VITE_ENABLE_MCP_TOOLS=true
```

⚠️ **重要**: 
- 替换 `sk-your-real-api-key-here` 为您的真实API密钥
- 不要将 `.env.local` 文件提交到代码仓库

### 3. 启动服务

**方法一：使用启动脚本（推荐）**
```bash
.\start-with-deepseek.cmd
```

**方法二：手动启动**
```bash
# 1. 启动MCP服务器
python shandong_mcp_server.py --mode http --host 0.0.0.0 --port 8000

# 2. 启动前端服务（新终端窗口）
cd oge-webgis-frontend
npm run dev
```

### 4. 访问系统

- 🌐 **前端界面**: http://localhost:3000
- 🔧 **MCP服务器**: http://localhost:8000
- 💬 **AI聊天**: 前端界面右侧聊天面板

## 💡 使用示例

### 智能环境检查

**用户输入**：
```
检查一下系统状态
```

**DeepSeek响应**：
🛠️ *自动调用 check_yaogan_environment 工具*
```
系统环境检查完成！
✅ 遥感大楼环境状态：5/7个服务正常运行
- 计算集群：正常
- Livy API：正常  
- MinIO存储：正常
- Hadoop HDFS：正常
- Prometheus监控：正常
- OGE前端：502错误
- 备用服务：离线

当前环境整体健康，可以正常进行地理分析任务。
```

### 智能坡度分析

**用户输入**：
```
我想分析北京市朝阳区的地形坡度
```

**DeepSeek响应**：
🛠️ *自动调用 slope_analysis 工具*
```
正在为您进行朝阳区地形坡度分析...

分析结果：
- 分析区域：北京市朝阳区
- 平均坡度：2.3°
- 最大坡度：15.7°（奥林匹克公园附近）
- 坡度分级：
  * 平坦区域（0-3°）：占75.2%
  * 缓坡区域（3-8°）：占20.1%
  * 中坡区域（8-15°）：占4.5%
  * 陡坡区域（>15°）：占0.2%

建议：该区域地形相对平坦，适合城市建设和交通规划。
```

### 智能缓冲区分析

**用户输入**：
```
帮我在地铁站周围做一个500米的缓冲区分析
```

**DeepSeek响应**：
```
我需要具体的地铁站位置信息才能进行缓冲区分析。请提供：
1. 地铁站的经纬度坐标，或
2. 地铁站的具体名称和城市

例如："北京地铁国贸站"或"经度116.4074，纬度39.9042"
```

**用户补充**：
```
北京地铁国贸站
```

**DeepSeek响应**：
🛠️ *自动调用 buffer_analysis 工具*
```
正在为国贸站创建500米缓冲区...

缓冲区分析完成：
- 中心点：国贸地铁站（116.4074°E, 39.9042°N）
- 缓冲半径：500米
- 覆盖面积：约0.785平方公里
- 影响范围：
  * 商业建筑：35栋
  * 住宅小区：12个
  * 公交站点：8个
  * 主要道路：建国门外大街、东三环中路

该缓冲区覆盖了CBD核心商务区，是北京重要的交通枢纽。
```

## 🔧 技术架构

### 系统架构图

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   用户输入   │───▶│  DeepSeek AI  │───▶│  工具选择    │
└─────────────┘    └──────────────┘    └─────────────┘
                           │                     │
                           ▼                     ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   智能回复   │◄───│   结果解析    │◄───│ MCP工具执行  │
└─────────────┘    └──────────────┘    └─────────────┘
```

### 核心组件

#### 1. DeepSeekService (`src/services/deepseek.js`)
- **功能**: DeepSeek API调用封装
- **特性**: 
  - 工具自动选择
  - 参数智能解析
  - MCP工具集成
  - 错误处理和重试

#### 2. ChatBox组件 (`src/components/ChatBox.vue`)
- **功能**: 聊天界面和交互
- **特性**:
  - 实时对话
  - 工具调用可视化
  - 工具结果详情
  - 对话历史管理

#### 3. API服务 (`src/services/api.js`)
- **功能**: 统一API管理
- **特性**:
  - 多AI提供商支持
  - 自动降级策略
  - 错误处理

### 可用的MCP工具

| 工具名称 | 功能描述 | 必需参数 | 可选参数 |
|---------|----------|----------|----------|
| `check_yaogan_environment` | 检查遥感大楼环境状态 | 无 | 无 |
| `slope_analysis` | 地形坡度分析 | `bounds` | `resolution` |
| `buffer_analysis` | 缓冲区空间分析 | `geometry`, `distance` | 无 |
| `farmland_outflow` | 耕地流出变化分析 | `region`, `start_year`, `end_year` | 无 |

#### 工具参数说明

**slope_analysis**
```json
{
  "bounds": [116.0, 39.5, 117.0, 40.5],  // [minLng, minLat, maxLng, maxLat]
  "resolution": 30                        // 分析分辨率（米）
}
```

**buffer_analysis**
```json
{
  "geometry": {                          // GeoJSON格式
    "type": "Point",
    "coordinates": [116.4074, 39.9042]
  },
  "distance": 500                        // 缓冲距离（米）
}
```

## ⚙️ 配置选项

### AI提供商切换

在 `src/services/api.js` 中修改：

```javascript
const AI_CONFIG = {
  provider: 'deepseek',    // 'deepseek' | 'mcp' | 'mock'
  enableMCPTools: true     // 是否启用MCP工具调用
}
```

### DeepSeek模型配置

在 `src/services/deepseek.js` 中修改：

```javascript
const response = await deepseekApi.post('/chat/completions', {
  model: "deepseek-chat",     // 模型名称
  temperature: 0.7,           // 创造性（0-1）
  max_tokens: 2000,          // 最大输出长度
  // ... 其他参数
})
```

## 🛡️ 安全配置

### API密钥保护

1. **环境变量隔离**
   ```bash
   # 添加到 .gitignore
   echo ".env.local" >> .gitignore
   ```

2. **密钥轮换**
   - 定期更换API密钥
   - 监控使用量和异常访问

3. **权限控制**
   - 限制API密钥权限范围
   - 设置使用量限制

### 网络安全

```javascript
// CORS配置（仅开发环境）
server: {
  proxy: {
    '/api/deepseek': {
      target: 'https://api.deepseek.com',
      changeOrigin: true,
      secure: true
    }
  }
}
```

## 🔍 故障排除

### 常见问题

#### 1. API密钥错误
```
错误: DeepSeek API密钥无效或已过期
```
**解决方案**:
- 检查 `.env.local` 文件中的密钥格式
- 确认密钥未过期且有足够余额
- 重新生成API密钥

#### 2. 网络连接失败
```
错误: 网络连接失败，请检查网络设置
```
**解决方案**:
- 检查网络连接
- 确认防火墙设置
- 尝试使用代理

#### 3. MCP工具调用失败
```
错误: 工具调用失败: check_yaogan_environment
```
**解决方案**:
- 确认MCP服务器正在运行
- 检查服务器健康状态：`curl http://localhost:8000/health`
- 查看MCP服务器日志

#### 4. 前端无法访问
```
错误: 无法访问 http://localhost:3000
```
**解决方案**:
- 检查Node.js版本（推荐16+）
- 重新安装依赖：`npm install`
- 检查端口占用：`netstat -ano | findstr :3000`

### 调试方法

#### 1. 启用详细日志
```javascript
// 在浏览器控制台
localStorage.setItem('debug', 'true')
```

#### 2. 检查网络请求
- 打开浏览器开发者工具
- 查看Network标签页
- 检查API请求和响应

#### 3. 查看错误信息
```javascript
// 在ChatBox组件中添加错误详情
console.error('DeepSeek调用失败:', error)
console.log('请求参数:', requestData)
console.log('响应数据:', responseData)
```

## 📊 性能优化

### 对话历史管理
```javascript
// 限制对话历史长度
const MAX_HISTORY_LENGTH = 20
if (conversationHistory.length > MAX_HISTORY_LENGTH) {
  conversationHistory.splice(0, conversationHistory.length - MAX_HISTORY_LENGTH)
}
```

### 工具调用缓存
```javascript
// 缓存相同参数的工具调用结果
const toolCache = new Map()
const cacheKey = `${toolName}_${JSON.stringify(parameters)}`
if (toolCache.has(cacheKey)) {
  return toolCache.get(cacheKey)
}
```

### 请求优化
```javascript
// 请求防抖
const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}
```

## 🔄 更新升级

### 版本更新
```bash
# 更新前端依赖
cd oge-webgis-frontend
npm update

# 更新Python依赖
pip install --upgrade fastmcp starlette uvicorn
```

### 功能扩展

#### 添加新的MCP工具
1. 在MCP服务器中实现新工具
2. 在 `deepseek.js` 中添加工具描述
3. 更新工具显示名称映射

#### 集成其他AI模型
```javascript
// 在 api.js 中添加新的AI提供商
case 'openai':
  return await openaiService.chat(message, sessionId, conversationHistory)
case 'claude':
  return await claudeService.chat(message, sessionId, conversationHistory)
```

## 📋 部署清单

### 开发环境
- [x] DeepSeek API密钥配置
- [x] MCP服务器启动
- [x] 前端开发服务器
- [x] 环境变量配置
- [x] 网络连接测试

### 生产环境
- [ ] HTTPS证书配置
- [ ] 域名和DNS设置
- [ ] 负载均衡配置
- [ ] 监控和日志系统
- [ ] 备份和恢复策略

## 📞 技术支持

### 文档资源
- [DeepSeek API文档](https://api.deepseek.com/docs)
- [Vue 3 官方文档](https://vuejs.org/)
- [Element Plus 组件库](https://element-plus.org/)

### 问题反馈
如遇到问题，请提供以下信息：
1. 操作系统版本
2. Node.js和Python版本
3. 错误信息和日志
4. 重现步骤

---

## 🎉 开始使用

现在您可以启动系统并体验DeepSeek AI驱动的智能地理分析助手了！

1. 配置API密钥：创建 `.env.local` 文件
2. 启动服务：运行 `.\start-with-deepseek.cmd`
3. 访问界面：打开 http://localhost:3000
4. 开始对话：在右侧聊天面板与AI助手交流

**示例对话**：
- "检查系统状态"
- "分析北京的地形坡度"  
- "在公园周围创建缓冲区"
- "查看耕地变化趋势"

享受智能化的地理分析体验！🚀 