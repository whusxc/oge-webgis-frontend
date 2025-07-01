# OGE WebGIS MCP开发周报

时间: 2024年12月  
项目: OGE WebGIS + MCP服务集成

---

## 本周工作总结

主要完成工作

1. MCP服务器核心开发
   - 完成山东环境MCP服务器开发，共计2431行代码
   - 实现基于FastMCP框架的7个核心GIS分析工具
   - 建立JWT认证系统和自动令牌刷新机制
   - 设计DAG工作流批处理架构

2. 前端WebGIS系统开发
   - 基于Vue 3 + Vite技术栈构建前端界面
   - 集成Mapbox GL JS地图引擎和交互控件
   - 开发MCP工具调用界面和任务进度展示组件
   - 实现DeepSeek AI对话系统，支持自然语言转GIS操作

3. 环境适配与网络配置
   - 解决山东环境与遥感大楼的网络连通性问题
   - 配置外网穿透服务器(http://111.37.195.111:7002)作为代理
   - 编写PowerShell和批处理自动化部署脚本
   - 处理Python环境依赖问题(fastmcp, starlette, uvicorn)

4. 核心算法实现
   - 农田适宜性分析多约束条件算法
   - 坡度分析和土地利用变更检测工具
   - 空间查询和几何处理API封装
   - 数据导出和可视化接口

技术突破点

- 令牌管理: 解决OGE API的40003过期错误，实现自动续期机制
- 跨环境部署: 通过网络代理解决内网API无法直接访问的问题
- 工作流编排: 将Python分析代码转换为可执行的DAG任务
- AI工具链: 实现自然语言到GIS分析流程的智能转换

工作量统计

- MCP服务器代码: 2431行 (Python)
- 前端代码: ~800行 (Vue/JavaScript)
- 配置脚本: 6个批处理/Shell脚本
- 核心工具: 7个GIS分析接口

---

## 一、MCP服务器开发（山东环境）

1.1 核心架构实现

基于FastMCP框架开发了完整的地理分析服务器(`shandong_mcp_server_enhanced.py`, 2431行)。FastMCP是基于Anthropic MCP协议的Python实现，支持工具注册、上下文管理和异步通信。

服务器端点配置:
```python
# 服务端点配置  
BASE_GATEWAY_URL = "http://172.20.70.142:16555/gateway"
INTRANET_API_BASE_URL = BASE_GATEWAY_URL+"/computation-api/process"
DAG_API_BASE_URL = "http://172.20.70.141/api/oge-dag-22"
AUTH_TOKEN_URL = "http://172.20.70.141/api/oauth/token"

# 双传输模式
async def run_stdio_server():
    # MCP stdio协议
async def run_http_server():
    # HTTP REST API
```

响应格式标准化设计:
```python
class Result(BaseModel):
    success: bool = False
    code: Optional[int] = None
    msg: Optional[str] = None
    data: Optional[T] = None
    execution_time: Optional[float] = None
    api_endpoint: Optional[str] = "oge"
```

该设计采用Pydantic数据模型确保类型安全，统一所有API响应格式。execution_time字段用于性能监控，api_endpoint标识数据来源。

1.2 Token自动管理机制

技术背景: OGE API采用JWT认证机制，token有效期较短，频繁出现40003过期错误。传统方案需要用户手动刷新，影响分析流程连续性。

自动刷新实现方案:
```python
async def call_api_with_timing(
    url: str, method: str = 'POST', 
    use_intranet_token: bool = False,
    auto_retry_on_token_expire: bool = True
) -> tuple[dict, float]:
    # 检测40003/401错误，自动刷新token并重试
    if (should_auto_retry and 
        isinstance(result, dict) and 
        result.get("code") == 40003):
        
        success, new_token = await refresh_intranet_token()
        if success:
            # 使用新token重新调用API（递归，禁用重试避免循环）
            return await call_api_with_timing(...)
```

Token刷新机制实现:
```python
async def refresh_intranet_token() -> tuple[bool, str]:
    params = {
        "scopes": "web", "client_secret": "123456",
        "client_id": "test", "grant_type": "password",
        "username": "edu_admin", "password": "123456"
    }
    
    response = await client.post(AUTH_TOKEN_URL, params=params, json=body)
    if response.status_code == 200:
        token = data['data']['token']
        token_head = data['data'].get('tokenHead', 'Bearer').rstrip()
        INTRANET_AUTH_TOKEN = f"{token_head} {token}"
```

该实现使用OAuth2密码授权模式，通过edu_admin账户获取新token。关键技术点包括：处理tokenHead前缀空格问题、全局token变量更新、异常处理机制。

1.3 DAG批处理工作流

核心技术架构基于有向无环图(DAG)的任务调度系统。将Python地理分析代码转换为可执行的DAG任务，支持分布式执行和状态监控。

工具链实现:
```python
@mcp.tool()
async def execute_code_to_dag(code: str, user_id: str):
    # Python代码 -> DAG任务定义
    api_result, _ = await call_api_with_timing(
        url=f"{DAG_API_BASE_URL}/executeCode",
        json_data={"code": code, "userId": user_id}
    )

@mcp.tool() 
async def submit_batch_task(dag_id: str, task_name: str):
    # DAG任务 -> 执行队列
    api_result, _ = await call_api_with_timing(
        url=f"{DAG_API_BASE_URL}/addTaskRecord",
        json_data={"id": dag_id, "taskName": task_name}
    )

@mcp.tool()
async def query_task_status(dag_id: str):
    # 查询执行状态 + 结果验证
    dag_resp, _ = await fetch(f"{DAG_API_BASE_URL}/getState", {"dagId": dag_id})
    catalog_resp, _ = await fetch(CATALOG_URL, {"dagId": dag_id})
```

工作流编排实现:
```python
async def execute_dag_workflow(
    code: str,
    wait_for_completion: bool = False,
    check_interval: int = 10,
    max_wait_time: int = 300
):
    # 步骤1: 代码转DAG
    dag_result = await execute_code_to_dag(code=code, user_id=DEFAULT_USER_ID)
    dag_ids = dag_result["data"]["dag_ids"]
    
    # 步骤2: 提交批处理任务  
    submit_result = await submit_batch_task(dag_id=dag_ids[0])
    
    # 步骤3: 轮询状态(可选)
    if wait_for_completion:
        while waited_time < max_wait_time:
            status = await query_task_status(dag_id=dag_ids[0])
            if status["data"]["is_completed"] or status["data"]["is_failed"]:
                break
            await asyncio.sleep(check_interval)
```

该工作流采用三段式设计：代码解析→任务提交→状态监控。支持同步/异步两种执行模式，通过轮询机制实现任务状态跟踪。

1.4 主要工具实现

耕地数据查询算法:
```python
@mcp.tool()
async def shandong_farmland_vector_query(
    administrative_divisions: list[str] = ["雪野镇"],
    year: str = "2023"
):
    # 调用统计接口获取可用区域
    resp, _ = await call_api_with_timing(
        url=BASE_GATEWAY_URL+"/computation-api/vector/statistical/guoTuBianGeng",
        method="GET",
        params={"DLMC": "旱地,水浇地,水田", "ZLDWMC": ""},
        use_intranet_token=True
    )
    
    # 数据过滤和SQL生成
    valid_divisions = set(item["region_name"] for item in resp["data"])
    if "雪野镇" in administrative_divisions:
        query = "SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田')"
    else:
        valid_villages = [name for name in administrative_divisions if name in valid_divisions]
        division_sql = ", ".join(f"'{v}'" for v in valid_villages)
        query = f"SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田') AND ZLDWMC IN ({division_sql})"
```

耕地适宜性分析算法:
```python
@mcp.tool()
async def farmland_suitability_analysis(data_query_sql: str):
    # 生成OGE代码
    oge_code = f"""import oge
oge.initialize()
service = oge.Service.initialize()

# 数据查询
cultivated = service.getProcess("FeatureCollection.runBigQuery").execute(r"{data_query_sql}", "geom")
cultivated_bounds = service.getProcess("FeatureCollection.bounds").execute(cultivated)

# 约束条件处理
slope = service.getFeatureCollection("shp_podu")
slope_morethan15 = service.getProcess("FeatureCollection.filterMetadata").execute(slope, "pdjb", "greater_than", 4)
urban = service.getFeatureCollection("shp_chengzhenkaifa")
ecology = service.getFeatureCollection("shp_shengtaibaohu")

# 空间分析
urban_intersection = service.getProcess("FeatureCollection.intersection").execute(cultivated, urban)
ecology_intersection = service.getProcess("FeatureCollection.intersection").execute(cultivated, ecology)
slope_intersection = service.getProcess("FeatureCollection.intersection").execute(cultivated, slope_extent)

# 细碎化分析
cultivated_area = service.getProcess("FeatureCollection.area").execute(slope_erase)
fragmented = service.getProcess("FeatureCollection.filterMetadata").execute(cultivated_area, "area", "less_than", 3333.3333)

# 结果导出
deprecated.export("cultivated_protected")"""
    
    # 执行DAG工作流
    return await execute_dag_workflow(
        code=oge_code,
        task_name=f"farmland_outflow_{time.time()}",
        wait_for_completion=True
    )
```

该算法实现多约束条件的耕地适宜性评价：
1. 坡度约束：筛选坡度等级>4(15度)的地块
2. 城镇约束：识别城镇开发边界内的耕地
3. 生态约束：检测生态保护红线范围内的耕地  
4. 细碎化约束：计算面积<5亩的细碎地块，结合10米缓冲区分析周边连通性

算法采用空间叠加分析方法，通过intersection、erase等GIS操作实现多层约束的逐级筛选。

---

## 二、遥感大楼环境适配与前端开发

2.1 环境适配问题

技术问题分析：遥感大楼内网环境缺乏OGE计算集群部署，无法直接复用山东环境的服务端点配置。
```
川: 我想问问我们遥感大楼这儿的oge，有类似山东那边的这种网址吗
快乐就好.: 好像没有
快乐就好.: 遥感院那边环境我们没有维护
```

网络架构解决方案：采用外网穿透技术，通过NAT端口映射访问公司内网的OGE服务器。
```
快乐就好.: 我们公司楼下有一套后端的环境
快乐就好.: 我们楼下服务器，网关16555端口穿透到111.37.195.111的7002端口
```

服务器配置重构:
```python
# 原配置（山东环境）
BASE_GATEWAY_URL = "http://172.20.70.142:16555/gateway"

# 新配置（外网穿透）
OGE_EXTERNAL_URL = "http://111.37.195.111:7002"
OGE_BACKEND_URL = OGE_EXTERNAL_URL
OGE_API_BASE_URL = f"{OGE_BACKEND_URL}/gateway/computation-api/process"
```

网络连通性测试:
```bash
PS> Invoke-WebRequest -Uri "http://111.37.195.111:7002"
StatusCode        : 200
StatusDescription : OK
```

该测试验证了外网穿透链路的可用性，确认HTTP协议层面的连通性。

2.2 前端开发

构建工具配置优化 - 基于Vite的开发服务器代理配置:
```javascript
// vite.config.js
export default {
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api/mcp': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/mcp/, '')
      },
      '/api/oge': {
        target: 'http://111.37.195.111:7002',  // 更新为可用服务器
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/oge/, '')
      }
    }
  }
}
```

HTTP客户端配置管理 - 实现开发/生产环境的自动切换:
```javascript
// src/services/api.js
const OFFLINE_MODE = false // 启用在线模式

const ogeApi = createApiInstance(
  import.meta.env.DEV ? '/api/oge' : 'http://111.37.195.111:7002'
)

// src/stores/app.js  
oge: {
  baseUrl: import.meta.env.DEV ? '/api/oge' : 'http://111.37.195.111:7002',
  timeout: 30000,
  connected: false
}
```

该配置采用环境变量判断机制，开发环境使用代理路径避免跨域问题，生产环境直接连接外网服务器。

大语言模型集成架构 - DeepSeek API调用实现:
```javascript
// src/services/deepseek.js
const DEEPSEEK_CONFIG = {
  apiKey: process.env.DEEPSEEK_API_KEY,
  baseURL: 'https://api.deepseek.com/v1',
  model: 'deepseek-chat'
}

async function callDeepSeekWithMCP(messages, tools) {
  const response = await fetch(`${DEEPSEEK_CONFIG.baseURL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${DEEPSEEK_CONFIG.apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: DEEPSEEK_CONFIG.model,
      messages: messages,
      tools: tools.map(tool => ({
        type: 'function',
        function: {
          name: tool.name,
          description: tool.description,
          parameters: tool.inputSchema
        }
      }))
    })
  })
}

该实现支持Function Calling机制，将MCP工具自动转换为OpenAI兼容的函数定义格式，实现大模型与地理分析工具的无缝集成。

2.3 部署环境问题

Python依赖环境问题:
```bash
PS> python shandong_mcp_server.py --mode http --host 0.0.0.0 --port 8000
Error importing enhanced MCP dependencies: No module named 'mcp'
Please install: pip install fastmcp starlette uvicorn
```

问题分析：遥感大楼环境缺少FastMCP相关Python包，需要安装mcp、fastmcp、starlette、uvicorn等依赖库。

Node.js前端服务运行状态:
```bash
PS> cd oge-webgis-frontend && npm run dev
Port 3000 is in use, trying another one...
  VITE v5.4.19  ready in 503 ms
  ➜  Local:   http://localhost:3001/
```

前端开发服务器正常启动，自动端口切换机制工作正常，支持热重载和跨网络访问。

---

## 三、技术总结

3.1 系统架构实现

MCP服务器技术栈(山东环境生产验证):
- 实现10个核心地理分析工具，覆盖数据查询、空间分析、工作流管理三个层次
- JWT自动刷新机制，解决token过期导致的服务中断问题
- 基于asyncio的DAG批处理工作流，支持大规模地理计算任务
- FastMCP框架提供HTTP REST API和MCP stdio双协议支持

前端技术架构:
- Vue 3 Composition API + Vite构建工具，提供现代化开发体验
- Pinia状态管理，实现组件间数据共享和响应式更新
- Mapbox GL JS地图引擎，支持高性能地理数据可视化
- DeepSeek大模型集成，通过Function Calling实现自然语言到GIS操作的转换

3.2 技术瓶颈分析

依赖环境配置问题: 
- 遥感大楼Python环境缺少FastMCP生态相关包(mcp、starlette、uvicorn)
- 需要建立完整的Python虚拟环境和依赖管理机制

服务兼容性待验证:
- 外网穿透服务器(111.37.195.111:7002)的算子支持范围未完全确认
- 新环境下的OGE API认证机制和山东环境可能存在差异
- DAG工作流在不同网络环境下的执行稳定性需要测试

3.3 技术实施路径

环境依赖安装:
```bash
pip install fastmcp starlette uvicorn httpx pydantic
```

系统集成验证步骤:
1. OGE服务器API兼容性测试：验证算子调用接口、参数格式、返回数据结构
2. 认证机制适配：测试token获取、刷新、过期处理在新环境下的表现
3. 端到端功能验证：完整测试"自然语言输入→MCP工具调用→OGE计算→结果返回"流程

性能优化方向:
- 实现MCP工具结果缓存，减少重复计算开销
- 优化大文件传输机制，支持分块上传和断点续传
- 建立服务监控体系，收集性能指标和错误日志 