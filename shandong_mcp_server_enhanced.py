#!/usr/bin/env python3
"""
山东耕地流出分析 MCP服务器 - 增强版
整合FastMCP框架，支持HTTP和stdio两种传输方式
"""

import asyncio
import json
import logging
import httpx
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar
from pydantic import BaseModel
from enum import IntEnum
from typing import Annotated
from pydantic import Field
import traceback

# MCP SDK 导入
try:
    from mcp.server.fastmcp import FastMCP, Context
    from mcp.server.sse import SseServerTransport
    from mcp.server import Server
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
    import uvicorn
    import argparse
except ImportError as e:
    print(f"Error importing enhanced MCP dependencies: {e}")
    print("Please install: pip install fastmcp starlette uvicorn")
    exit(1)

T = TypeVar("T")

# ============ 配置部分 ============

# 服务器配置
MCP_SERVER_NAME = "shandong-cultivated-analysis-enhanced"

# API配置
BASE_GATEWAY_URL = "http://172.20.70.142:16555/gateway"
OGE_API_BASE_URL = "http://172.30.22.116:16555/gateway/computation-api/process"
INTRANET_API_BASE_URL = BASE_GATEWAY_URL+"/computation-api/process"
INTRANET_AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMyNCwidXNlcl9uYW1lIjoiZWR1X2FkbWluIiwic2NvcGUiOlsid2ViIl0sImV4cCI6MTc1MDAwMzQ1NiwidXVpZCI6ImY5NTBjZmYyLTA3YzgtNDYxYS05YzI0LTkxNjJkNTllMmVmNiIsImF1dGhvcml0aWVzIjpbIkFETUlOSVNUUkFUT1JTIl0sImp0aSI6IkhrbG9YdDhiMTFmMDJXTFRON3pXc0FkVlk3TSIsImNsaWVudF9pZCI6InRlc3QiLCJ1c2VybmFtZSI6ImVkdV9hZG1pbiJ9.RAaOX2Bzqn0ys8ZpzlsYaVY6RQuYMNwzYXWcJ_9KD8U"
AUTH_TOKEN_URL = "http://172.20.70.141/api/oauth/token"
"http://172.20.70.142:16555/gateway/computation-api/vector/statistical/guoTuBianGeng"

# DAG批处理API配置
DAG_API_BASE_URL = "http://172.20.70.141/api/oge-dag-22"
DEFAULT_USER_ID = "f950cff2-07c8-461a-9c24-9162d59e2ef6"
DEFAULT_USERNAME = "edu_admin"
CATALOG_URL   = "http://172.20.70.141/api/asset/batch-result/catalog"
# 执行结果与dagId绑定，数据插入
INSERT_REPORT_URL = BASE_GATEWAY_URL+"/asset/algorithm-processing-result/insert"




# ============ 响应格式定义 ============

class RetCode(IntEnum):
    SUCCESS = 0
    FAILED = 1

class Result(BaseModel):
    success: bool = False
    code: Optional[int] = None
    msg: Optional[str] = None
    data: Optional[T] = None
    map_type:Optional[T] = None
    operation: Optional[str] = None
    execution_time: Optional[float] = None
    api_endpoint: Optional[str] = "oge"

    @classmethod
    def succ(cls, data: T = None, msg="成功", operation=None, map_type=None, execution_time=None, api_endpoint="oge"):
        return cls(
            success=True, 
            code=RetCode.SUCCESS, 
            msg=msg, 
            data=data,
            map_type=map_type,
            operation=operation,
            execution_time=execution_time,
            api_endpoint=api_endpoint
        )

    @classmethod
    def failed(cls, code: int = RetCode.FAILED, msg="操作失败", map_type=map_type, operation=None):
        return cls(success=False, code=code, msg=msg, map_type=map_type, operation=operation)

# ============ 日志配置 ============

# def setup_logger(name: str = None, file: str = None, level=logging.INFO) -> logging.Logger:
#     """设置结构化日志"""
#     logger = logging.getLogger(name)
#     logger.propagate = False
#     logger.setLevel(level)
    
#     if logger.hasHandlers():
#         logger.handlers.clear()

#     formatter = logging.Formatter(
#         fmt='%(name)s - %(asctime)s - %(levelname)s - %(message)s',
#         datefmt='%Y-%m-%d %H:%M:%S'
#     )

#     # 文件日志
#     if file:
#         Path(file).parent.mkdir(parents=True, exist_ok=True)
#         file_handler = logging.FileHandler(filename=file, mode='a', encoding='utf-8')
#         file_handler.setFormatter(formatter)
#         file_handler.setLevel(level)
#         logger.addHandler(file_handler)

#     # 控制台日志
#     stream_handler = logging.StreamHandler()
#     stream_handler.setFormatter(formatter)
#     stream_handler.setLevel(level)
#     logger.addHandler(stream_handler)

#     return logger

def setup_mcp_logger(name, file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # 一定要 True，让它往上冒泡到 root
    logger.propagate = True

    # 只在第一次配置时加 handler
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        # 文件
        if file:
            Path(file).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(file, encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        # 控制台
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger

# 创建日志实例
logger = setup_mcp_logger("shandong_mcp", "logs/shandong_mcp.log")
api_logger = setup_mcp_logger("shandong_api", "logs/api_calls.log")

# ============ FastMCP实例 ============

mcp = FastMCP(MCP_SERVER_NAME)

# ============ Token管理 ============

async def refresh_intranet_token() -> tuple[bool, str]:
    """自动刷新内网token"""
    global INTRANET_AUTH_TOKEN
    
    try:
        logger.info("开始刷新内网token...")
        
        url = AUTH_TOKEN_URL
        
        params = {
            "scopes": "web",
            "client_secret": "123456",
            "client_id": "test",
            "grant_type": "password",
            "username": "edu_admin",
            "password": "123456"
        }
        
        body = {
            "username": "edu_admin",
            "password": "123456"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params, json=body, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'token' in data['data']:
                    token = data['data']['token']
                    token_head = data['data'].get('tokenHead', 'Bearer').rstrip()  # 去掉尾部空格
                    full_token = f"{token_head} {token}"
                    
                    # 更新全局token
                    INTRANET_AUTH_TOKEN = full_token
                    
                    logger.info(f"Token刷新成功: {full_token[:50]}...")
                    logger.info(f"Token格式检查 - head: '{token_head}', length: {len(full_token)}")
                    return True, full_token
                else:
                    logger.error(f"Token响应格式异常: {data}")
                    return False, f"Token响应格式异常: {data}"
            else:
                error_msg = f"Token获取失败 - 状态码: {response.status_code} - 响应: {response.text}"
                logger.error(error_msg)
                return False, error_msg
                
    except Exception as e:
        error_msg = f"Token刷新异常: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

# ============ 通用API调用函数 ============

async def call_api_with_timing(
    url: str,
    method: str = 'POST',
    params: dict | None = None, 
    json_data: dict = None,
    headers: dict = None,
    timeout: int = 120,
    auto_retry_on_token_expire: bool = True,
    use_intranet_token: bool = False
) -> tuple[dict, float]:
    """通用API调用，带性能监控和自动token刷新"""
    global INTRANET_AUTH_TOKEN
    start_time = time.perf_counter()
    
    # 如果指定使用内网token，则动态更新headers
    if use_intranet_token:
        if headers is None:
            headers = {"Content-Type": "application/json"}
        headers["Authorization"] = INTRANET_AUTH_TOKEN
        logger.info(f"使用内网token: {INTRANET_AUTH_TOKEN[:50]}...")
        logger.info(f"实际发送headers: {dict((k, v[:50] + '...' if k == 'Authorization' and len(v) > 50 else v) for k, v in headers.items())}")
    
    # 检查是否需要自动重试
    should_auto_retry = (
        use_intranet_token and 
        auto_retry_on_token_expire
    )
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 处理GET请求的参数
            if method.upper() == "GET":
                # headers.pop("Content-Type")
                response = await client.get(
                    # method=method.upper(),
                    url=url,
                    params=params,
                    headers=headers or {"Content-Type": "application/json"}
                )
            else:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=json_data,
                    headers=headers or {"Content-Type": "application/json"}
                )
            
            execution_time = time.perf_counter() - start_time
            
            if response.status_code == 200:
                # 安全处理JSON解析
                response_text = response.text.strip()
                try:
                    result = response.json()
                    # result["info-url"] = str(response.url)
                except Exception as json_error:
                    # 如果JSON解析失败，返回原始文本作为结果
                    logger.info(f"响应不是JSON格式，作为纯文本处理: {response_text[:100]}...")
                    # 对于DAG状态查询，直接返回文本状态
                    if "/getState" in url:
                        result = response_text if response_text else "unknown"
                    else:
                        result = {
                            "raw_text": response_text,
                            "json_parse_error": str(json_error),
                            "content_type": response.headers.get("content-type", "unknown")
                        }
                
                # 检查是否为token过期错误
                if (should_auto_retry and 
                    isinstance(result, dict) and 
                    result.get("code") == 40003):
                    
                    logger.warning("检测到token过期(40003)，尝试自动刷新...")
                    
                    # 刷新token
                    success, new_token = await refresh_intranet_token()
                    
                    if success:
                        logger.info("Token刷新成功，重新调用API...")
                        
                        # 确保使用新token重新构建headers
                        new_headers = None
                        if use_intranet_token:
                            new_headers = {
                                "Content-Type": "application/json",
                                "Authorization": new_token
                            }
                        
                        # 重新调用API（递归，但禁用自动重试避免无限循环）
                        return await call_api_with_timing(
                            url=url,
                            method=method,
                            params=params,
                            json_data=json_data,
                            headers=new_headers,
                            timeout=timeout,
                            auto_retry_on_token_expire=False,  # 禁用重试避免循环
                            use_intranet_token=False  # 已经手动设置headers了，不需要再次设置
                        )
                    else:
                        logger.error(f"Token刷新失败: {new_token}")
                        api_logger.error(f"API调用失败(token刷新失败) - URL: {url}")
                        return {"error": f"Token过期且刷新失败: {new_token}", "code": 40003}, execution_time
                
                api_logger.info(f"API调用成功 - URL: {url} - 耗时: {execution_time:.4f}s")
                return result, execution_time
            elif response.status_code == 401 and should_auto_retry:
                # 处理HTTP 401状态码（认证失败）
                logger.warning("检测到401状态码，尝试自动刷新token...")
                
                # 刷新token
                success, new_token = await refresh_intranet_token()
                
                if success:
                    logger.info("Token刷新成功，重新调用API...")
                    
                    # 确保使用新token重新构建headers
                    new_headers = None
                    if use_intranet_token:
                        new_headers = {
                            "Content-Type": "application/json",
                            "Authorization": new_token
                        }
                    
                    # 重新调用API（递归，但禁用自动重试避免无限循环）
                    return await call_api_with_timing(
                        url=url,
                        method=method,
                        params=params,
                        json_data=json_data,
                        headers=new_headers,
                        timeout=timeout,
                        auto_retry_on_token_expire=False,  # 禁用重试避免循环
                        use_intranet_token=False  # 已经手动设置headers了，不需要再次设置
                    )
                else:
                    logger.error(f"Token刷新失败: {new_token}")
                    api_logger.error(f"API调用失败(token刷新失败) - URL: {url}")
                    return {"error": f"401认证失败且token刷新失败: {new_token}", "status_code": 401}, execution_time
            else:
                error_detail = f"API调用失败 - URL: {url} - 状态码: {response.status_code} - 耗时: {execution_time:.4f}s"
                if response.status_code == 401:
                    current_token_preview = INTRANET_AUTH_TOKEN[:30] + "..." if INTRANET_AUTH_TOKEN else "None"
                    error_detail += f" - 当前token预览: {current_token_preview}"
                api_logger.error(error_detail)
                return {"error": response.text, "status_code": response.status_code}, execution_time
                
    except Exception as e:
        execution_time = time.perf_counter() - start_time
        api_logger.error(f"API调用异常 - URL: {url} - 错误: {str(e)} - 耗时: {execution_time:.4f}s")
        return {"error": str(e)}, execution_time

# ============ 工具定义 ============

# @mcp.tool()
async def refresh_token(ctx: Context = None) -> str:
    """
    手动刷新内网认证Token
    
    当遇到token过期错误(40003)时，可以使用此工具手动刷新token，其他错误情况，与token过期异常无关的问题，不需要调取
    """
    operation = "刷新Token"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"手动执行{operation}")
        
        success, token_or_error = await refresh_intranet_token()
        
        if success:
            result = Result.succ(
                data={
                    "new_token": token_or_error[:50] + "...",  # 只显示前50个字符
                    "token_length": len(token_or_error),
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                msg=f"{operation}成功",
                map_type="refresh_token",
                operation=operation,
                api_endpoint="auth"
            )
            
            if ctx:
                await ctx.session.send_log_message("info", f"{operation}成功，新token已更新")
        else:
            result = Result.failed(
                msg=f"{operation}失败: {token_or_error}",
                map_type="refresh_token",
                operation=operation
            )
            
            if ctx:
                await ctx.session.send_log_message("error", f"{operation}失败: {token_or_error}")
        
        logger.info(f"{operation}执行完成 - 成功: {success}")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="refresh_token",
            operation=operation
        )
        return result.model_dump_json()

# @mcp.tool()
async def check_token_status(ctx: Context = None) -> str:
    """
    检查当前内网认证Token状态,请注意除非是token过期异常的错误，否则不要调用该工具
    
    用于调试token问题，显示当前token的信息
    """
    global INTRANET_AUTH_TOKEN
    operation = "检查Token状态"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation}")
        
        if INTRANET_AUTH_TOKEN:
            # 尝试解析JWT token的有效期（如果是JWT格式）
            token_info = {
                "has_token": True,
                "token_preview": INTRANET_AUTH_TOKEN[:50] + "...",
                "token_length": len(INTRANET_AUTH_TOKEN),
                "starts_with_bearer": INTRANET_AUTH_TOKEN.startswith("Bearer "),
                "has_double_space": "Bearer  " in INTRANET_AUTH_TOKEN,  # 检测双空格问题
                "current_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "bearer_prefix_length": len(INTRANET_AUTH_TOKEN.split(' ')[0]) if ' ' in INTRANET_AUTH_TOKEN else 0
            }
            
            # 如果是JWT token，尝试解析过期时间
            if "Bearer " in INTRANET_AUTH_TOKEN:
                jwt_part = INTRANET_AUTH_TOKEN.replace("Bearer ", "")
                try:
                    import base64
                    import json
                    # 简单解析JWT payload（不验证签名）
                    parts = jwt_part.split('.')
                    if len(parts) >= 2:
                        # 添加padding如果需要
                        payload = parts[1]
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.b64decode(payload)
                        payload_data = json.loads(decoded)
                        
                        if 'exp' in payload_data:
                            exp_time = payload_data['exp']
                            exp_readable = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp_time))
                            token_info["expires_at"] = exp_readable
                            token_info["expires_timestamp"] = exp_time
                            token_info["is_expired"] = time.time() > exp_time
                        
                        if 'user_name' in payload_data:
                            token_info["username"] = payload_data['user_name']
                            
                except Exception as e:
                    token_info["parse_error"] = str(e)
            
            result = Result.succ(
                data=token_info,
                msg=f"{operation}成功",
                map_type="check_token_status",
                operation=operation,
                api_endpoint="debug"
            )
        else:
            result = Result.failed(
                msg=f"{operation}: 当前没有token",
                map_type="check_token_status",
                operation=operation
            )
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成")
        
        logger.info(f"{operation}执行完成")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="check_token_status",
            operation=operation
        )
        return result.model_dump_json()

# @mcp.tool()
async def coverage_aspect_analysis(
    bbox: List[float],
    coverage_type: str = "Coverage",
    pretreatment: bool = True,
    product_value: str = "Platform:Product:ASTER_GDEM_DEM30",
    radius: int = 1,
    ctx: Context = None
) -> str:
    """
    坡向分析 - 基于DEM数据计算坡向信息
    
    Parameters:
    - bbox: 边界框坐标 [minLon, minLat, maxLon, maxLat]
    - coverage_type: 覆盖类型
    - pretreatment: 是否进行预处理
    - product_value: 产品数据源
    - radius: 计算半径
    """
    operation = "坡向分析"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - 边界框: {bbox}")
        
        # 构建算法参数
        algorithm_args = {
            "coverage": {
                "type": coverage_type,
                "pretreatment": pretreatment,
                "preParams": {"bbox": bbox},
                "value": [product_value]
            },
            "radius": radius
        }
        
        # 调用内网API
        api_payload = {
            "name": "Coverage.aspect",
            "args": algorithm_args,
            "dockerImageSource": "DOCKER_HUB"
        }
        
        api_result, execution_time = await call_api_with_timing(
            url=INTRANET_API_BASE_URL,
            json_data=api_payload,
            use_intranet_token=True
        )
        
        if "error" in api_result:
            result = Result.failed(
                msg=f"{operation}失败: {api_result.get('error')}",
                map_type="coverage_aspect_analysis",
                operation=operation
            )
        else:
            result = Result.succ(
                data=api_result,
                msg=f"{operation}执行成功",
                map_type="coverage_aspect_analysis",
                operation=operation,
                execution_time=execution_time,
                api_endpoint="intranet"
            )
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成，耗时{execution_time:.2f}秒")
        
        logger.info(f"{operation}执行完成 - 耗时: {execution_time:.2f}秒")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="coverage_aspect_analysis",
            operation=operation
        )
        return result.model_dump_json()

# spatial_intersection 工具已删除

# coverage_slope_analysis 工具已删除

# terrain_analysis_suite 工具已删除

# get_oauth_token 和 refresh_intranet_token 工具已删除

# @mcp.tool()
async def process_single_tool_testing(
    # region_id: str = "ASTGTM_N28E056",
    # product_id: str = "ASTER_GDEM_DEM30", 
    # center_lon: float = 56.25,
    # center_lat: float = 28.40,
    # zoom_level: int = 11,
    wait_for_completion: bool = False,  # 默认立即返回，避免超时
    ctx: Context = None
) -> str:
    """
    该工具为：整体流程单个工具测试
    该工具为测试使用，除非用户指定测试的要求，否则不应该被调用。
    该工具测试的是按照代码提交的方式，执行成个流程，返回最终的结果。
    该方式的工作流程：
    1. 提交任务（立即返回DAG ID）
    2. 使用返回的DAG ID调用 query_task_status 查询进度
    3. 执行状态为starting与running，要调用query_task_status 轮训进度，每5秒一次，直到状态成功或者轮训次数超过10次
    
    Parameters:
    - wait_for_completion: 是否等待任务完成 (默认: False，立即返回避免超时)
    
    返回信息包含：
    - 任务状态和DAG ID
    - 下一步操作指引
    - 查询状态的具体参数
    """
    operation = "山东耕地流出分析"
    region_id: str = "ASTGTM_N28E056",
    product_id: str = "ASTER_GDEM_DEM30", 
    center_lon: float = 56.25,
    center_lat: float = 28.40,
    zoom_level: int = 11,
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - 区域: {region_id}, 产品: {product_id}")
        
        # 构建OGE代码
        oge_code = f"""import oge

oge.initialize()
service = oge.Service()

dem = service.getCoverage(coverageID="{region_id}", productID="{product_id}")
aspect = service.getProcess("Coverage.aspect").execute(dem, 1)

vis_params = {{"min": -1, "max": 1, "palette": ["#808080", "#949494", "#a9a9a9", "#bdbebd", "#d3d3d3","#e9e9e9"]}}
aspect.styles(vis_params).export("aspect")
oge.mapclient.centerMap({center_lon}, {center_lat}, {zoom_level})"""
        
        logger.info(f"生成的OGE代码长度: {len(oge_code)} 字符")
        
        # 调用execute_dag_workflow执行完整工作流
        workflow_result = await execute_dag_workflow(
            code=oge_code,
            task_name="shandong_farmland_outflow_analysis",
            filename="shandong_aspect_analysis",
            auto_submit=True,
            wait_for_completion=wait_for_completion,
            check_interval=10,          # 每10秒轮询一次
            max_wait_time=1800,         # 30分钟超时
            ctx=ctx
        )
        
        # 解析workflow结果
        import json
        workflow_data = json.loads(workflow_result)
        
        if workflow_data.get("success"):
            # 提取关键信息
            workflow_details = workflow_data.get("data", {})
            final_status = workflow_details.get("final_status", "unknown")
            
            result_data = {
                "region_id": region_id,
                "product_id": product_id,
                "analysis_type": "aspect_analysis",
                "map_center": {"lon": center_lon, "lat": center_lat, "zoom": zoom_level},
                "workflow_status": final_status,
                "execution_steps": workflow_details.get("steps", []),
                "execution_times": workflow_details.get("execution_times", {}),
                "dag_info": {
                    "dag_ids": workflow_details.get("dag_ids", []),
                    "primary_dag_id": workflow_details.get("dag_ids", ["unknown"])[0],
                    "task_name": "shandong_farmland_outflow_analysis"
                },
                "next_action": {
                    "tool_name": "query_task_status",
                    "parameters": {
                        "dag_id": workflow_details.get("dag_ids", ["unknown"])[0]
                    },
                    "description": "查询任务执行状态"
                } if final_status == "submitted" else None
            }
            
            if final_status == "completed":
                msg = f"{operation}执行成功 - DEM坡向分析已完成并可视化"
            elif final_status == "submitted":
                primary_dag_id = workflow_details.get("dag_ids", ["unknown"])[0]
                msg = f"{operation}任务已提交 - DAG ID: {primary_dag_id}\n" + \
                      f"💡 请使用以下命令查询进度：\n" + \
                      f"query_task_status(dag_id=\"{primary_dag_id}\")"
            else:
                msg = f"{operation}执行完成 - 状态: {final_status}"
            
            result = Result.succ(
                data=result_data,
                msg=msg,
                map_type="process_single_tool_testing",
                operation=operation,
                api_endpoint="dag_workflow"
            )
        else:
            # 工作流执行失败
            error_msg = workflow_data.get("msg", "工作流执行失败")
            final_status = "failed"
            result = Result.failed(
                msg=f"{operation}失败: {error_msg}",
                map_type="process_single_tool_testing",
                operation=operation
            )
            result.data = workflow_data.get("data")
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成")
        
        logger.info(f"{operation}执行完成 - 最终状态: {final_status}")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="process_single_tool_testing",
            operation=operation
        )
        return result.model_dump_json()


# @mcp.tool()
async def shandong_farmland_vector_query_old(
    # administrative_division: Annotated[str,Field(description="要查询的标准地区名称",required = False)] = "雪野镇",
    administrative_divisions: Annotated[list[str], Field(description="要查询的标准地区名称列表", required=False)] = ["雪野镇"],
    year: Annotated[str,Field(description="要查询的年份",required = False)] = "2023",
    ctx: Context = None
) -> str:
    """
    数据预处理
    
    Return:
        包含数据是否存在的信息与查询语句的信息包
    """
    operation = "耕地矢量查询"
    query = "SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田')"
    ZLDWMC = ['三槐树村', '上游村', '上秋林村', '东下游村', '东峪村', '东张村', '东抬头村', '东栾宫村', '东站村', '冬暖村', '北双王村', '北峪村', '北栾宫村', '北江水村', '北白座村', '华山村', '华山林场', '南双王村', '南圈村', '南峪村', '南嵬石村', '南栾宫村', '南白座村', '吕祖泉村', '大厂村', '大寨村', '大罗圈村', '娘娘庙村', '学山村', '安子湾村', '官正村', '富家庄村', '小楼村', '岭东村', '房干村', '望米台村', '朱公泉村', '李家庄村', '李白杨村', '栖龙湾村', '桥子村', '毛家林村', '狂山村', '王老村', '石子口村', '石泉村', '红哨子村', '胡多罗村', '胡家庄村', '船厂村', '花峪村', '蜂窝村', '西下游村', '西峪河北村', '西峪河南村', '西嵬石村', '西抬头村', '西站村', '邢家峪村', '酉坡村', '阁老村', '雪野村', '雪野水库', '青合圈村', '马家峪村', '马鞍山林场', '鲁地村', '鹿野村', '黑山村', '龙马庄村']
    
    try:
        if ctx:
            if year and administrative_divisions:
                names = "、".join(administrative_divisions)
                await ctx.session.send_log_message("info", f"获取{year}年{names}林耕地适宜性评价关联数据")
            elif administrative_divisions:
                names = "、".join(administrative_divisions)
                await ctx.session.send_log_message("info", f"获取{names}林耕地适宜性评价关联数据")
            elif year:
                await ctx.session.send_log_message("info", f"获取{year}年林耕地适宜性评价关联数据")
            else:
                await ctx.session.send_log_message("info", "获取林耕地适宜性评价关联数据")

            await ctx.session.send_log_message("info", "进行数据完整性检查与预处理")
        
        valid_divisions = set(ZLDWMC)
        removed_divisions = []
        valid_villages = []

        # 初始去重
        administrative_divisions = list(set(administrative_divisions))
        api_result = {
            "status_code": 200,
            "msg": "",
            "data": {
                "query_sql": query,
                "valid_villages":valid_villages,
                "removed_divisions":removed_divisions
            }
        }

        if "雪野镇" in administrative_divisions:
            # 若包含“雪野镇”，则忽略其他村名，但记录不合法的
            for name in administrative_divisions:
                if name != "雪野镇" and name not in valid_divisions:
                    removed_divisions.append(name)
            query = "SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田')"
        else:
            # 仅为村级，筛选有效村
            valid_villages = [name for name in administrative_divisions if name in valid_divisions]
            removed_divisions = [name for name in administrative_divisions if name not in valid_divisions]

            if valid_villages:
                division_sql = ", ".join(f"'{v}'" for v in valid_villages)
                query = f"SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田') AND ZLDWMC IN ({division_sql})"

        res_msg = f"数据存在，可以执行计算"
        api_result["data"]["query_sql"]=query
        
        if "雪野镇" not in administrative_divisions and len(valid_villages) < 1 :
            api_result = {"info": f"数据库内没有该年份或地区的数据", "status_code": 200,"data":None}
            res_msg = f"数据库内没有该年份/地区的数据"
        if year != "2023":
            api_result = {"info": f"数据库内没有该年份或地区的数据", "status_code": 200,"data":None}
            res_msg = f"数据库内没有该年份/地区的数据"

        
        if "error" in api_result:
            error_detail = api_result.get('error', '未知错误')
            status_code = api_result.get('status_code', '未知状态码')
            result = Result.failed(
                msg=f"{operation}失败: {error_detail} (状态码: {status_code})",
                map_type="shandong_farmland_vector_query",
                operation=operation
            )
            
        else:
            result = Result.succ(
                data=api_result,
                msg=f"{operation}执行成功,"+res_msg,
                map_type="shandong_farmland_vector_query",
                operation=operation,
                api_endpoint="intranet"
            )
        
        # if ctx:
        #     # await ctx.session.send_log_message("info", f"{operation}执行完成，耗时{execution_time:.2f}秒")
        #     await ctx.session.send_log_message("info", res_msg)
        
        logger.info(f"{operation}执行完成")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="shandong_farmland_vector_query",
            operation=operation
        )
        return result.model_dump_json()


@mcp.tool()
async def shandong_farmland_vector_query(
    administrative_divisions: Annotated[list[str], Field(description="要查询的标准地区名称列表-list[str]", required=False)] = ["雪野镇"],
    year: Annotated[str,Field(description="要查询的年份",required = False)] = "2023",
    ctx: Context = None
) -> str:
    """
    数据预处理
    
    如果数据库无数据的话，不用再次调用，返回用户即可
    Return:
        包含数据是否存在的信息与查询语句的信息包,查询无数据，不会返回查询sql
    """
    operation = "耕地数据查询"
    DLMC_LIST = ["旱地", "水浇地", "水田"]
    ZLDWMC = []
    params = {"DLMC": ",".join(DLMC_LIST),"ZLDWMC":",".join(ZLDWMC)}
    vector_query_url = BASE_GATEWAY_URL+"/computation-api/vector/statistical/guoTuBianGeng"
    # params["DLMC"] = ",".join(DLMC_LIST)
    # params["ZLDWMC"] = ",".join(ZLDWMC)
    # if ZLDWMC:
    #     params["ZLDWMC"] = zldwmc
    
    try:
        # 调用通用接口函数
        resp, _ = await call_api_with_timing(
            url=vector_query_url,
            method="GET",
            params=params,
            # 如果你们内部需要 token，可以加 use_intranet_token=True
            use_intranet_token=True
        )
        
        MC_list = []
        # 检查 code、拿到 data
        if isinstance(resp, dict) and resp.get("code") == 20000:
            # ZLDWMC 就是一个 [{ "cnt": 3, "region_name": "...", "all_area": ... }, ...] 的列表
            MC_list = resp.get("data", [])
        else:
            # 根据实际情况抛错或返回空
            raise RuntimeError(f"调用失败：{resp}")

        if ctx:
            if year and administrative_divisions:
                names = "、".join(administrative_divisions)
                await ctx.session.send_log_message("info", f"获取{year}年{names}林耕地适宜性评价关联数据")
            elif administrative_divisions:
                names = "、".join(administrative_divisions)
                await ctx.session.send_log_message("info", f"获取{names}林耕地适宜性评价关联数据")
            elif year:
                await ctx.session.send_log_message("info", f"获取{year}年林耕地适宜性评价关联数据")
            else:
                await ctx.session.send_log_message("info", "获取林耕地适宜性评价关联数据")
        
        valid_divisions = set(item["region_name"] for item in MC_list)
        removed_divisions = []
        valid_villages = []

        query = ""
        # 初始去重
        administrative_divisions = set(administrative_divisions)
        api_result = {
            "status_code": 200,
            "msg": "",
            "data": {
                "query_sql": query,
                "valid_villages":valid_villages,
                "removed_divisions":removed_divisions
            }
        }

        if "雪野镇" in administrative_divisions:
            # 若包含“雪野镇”，则忽略其他村名，但记录不合法的
            for name in administrative_divisions:
                if name != "雪野镇" and name not in valid_divisions:
                    removed_divisions.append(name)
                else:
                    valid_villages.append(name)
            query = "SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田')"
            valid_villages.append("雪野镇")
        else:
            # 仅为村级，筛选有效村
            valid_villages.extend([name for name in administrative_divisions if name in valid_divisions])
            removed_divisions.extend([name for name in administrative_divisions if name not in valid_divisions])
            if valid_villages:
                division_sql = ", ".join(f"'{v}'" for v in valid_villages)
                query = f"SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田') AND ZLDWMC IN ({division_sql})"

        res_msg = f"数据存在，可以执行计算"
        api_result["data"]["query_sql"]=query
        data_is_exist = True
        
        if "雪野镇" not in administrative_divisions and len(valid_villages) < 1 :
            api_result = {"info": f"数据库内没有该年份或地区的数据", "status_code": 200,"data":None}
            res_msg = "数据库内没有该年份/地区的数据"
            data_is_exist = False
        if year != "2023":
            api_result = {"info": f"数据库内没有该年份或地区的数据", "status_code": 200,"data":None}
            res_msg = "数据库内没有该年份/地区的数据"
            data_is_exist = False
        
        if "error" in api_result:
            error_detail = api_result.get('error', '未知错误')
            status_code = api_result.get('status_code', '未知状态码')
            result = Result.failed(
                msg=f"{operation}失败: {error_detail} (状态码: {status_code})",
                map_type="shandong_farmland_vector_query",
                operation=operation
            )
            
        else:
            result = Result.succ(
                data=api_result,
                msg=f"{operation}执行成功,"+res_msg,
                map_type="shandong_farmland_vector_query",
                operation=operation,
                api_endpoint="intranet"
            )
            if ctx:
                if data_is_exist:
                    await ctx.session.send_log_message("info", "进行数据完整性检查与预处理")
                else:
                    await ctx.session.send_log_message("info", "数据库内没有该年份/地区的数据")
        
        logger.info(f"{operation}执行完成")
        print(result)
        return result.model_dump_json()
    except Exception as e:
        logger.error(f"{operation}执行失败: {e}")
        result = Result.failed(
            msg=f"{operation}执行失败: {e}",
            map_type="shandong_farmland_vector_query",
            operation=operation
        )
        return result.model_dump_json()

# 耕地适宜性分析
@mcp.tool()
async def farmland_suitability_analysis(
    data_query_sql: Annotated[str,Field(description="数据预处理的query_sql",required = True)],
    wait_for_completion: bool = True,
    ctx: Context = None
) -> str:
    """
    耕地地块合并

    """
    operation = "耕地流出分析"
    slope_threshold: int = 4           # 坡度等级阈值，4对应15度
    fragment_area_threshold: float = 3333.3333  # 细碎化面积阈值（5亩=3333.33平方米）
    buffer_distance: float = 10.0     # 缓冲区距离（米）
    peripheral_area_threshold: float = 6666.6667  # 周边面积阈值（10亩）
    # 630演示，加入信息
    additional_json_data = {
        "pre": [
            {
                "name": "生态保护红线",
                "type": "ecology",
                "url": "http://59.206.223.134:7000/service/xueye_bio_protected_boundary?type=wvts&tablename=xueye_bio_protected_boundary&z={z}&x={x}&y={y}",
                "detailmeta": "{center: [121.709337,37.308754],zoom:12}"
            },
            {
                "name": "城镇开发边界",
                "type": "town",
                "url": "http://59.206.223.134:7000/service/xueye_urban_boundary?type=wvts&tablename=xueye_urban_boundary&z={z}&x={x}&y={y}",
                "detailmeta": "{center: [121.709337,37.308754],zoom:12}"
            },
            {
                "name": "耕地地块数据",
                "type": "farmland",
                "url": "http://59.206.223.134:7000/service/ogeArable?type=wvts&tablename=ogeArable&z={z}&x={x}&y={y}",
                "detailmeta": "{center: [121.709337,37.308754],zoom:12}"
            },
            {
                "name": "大于15度的坡度",
                "type": "slope",
                "url": "http://59.206.223.134:7000/service/xueye_slope_boundary?type=wvts&tablename=xueye_slope_boundary&z={z}&x={x}&y={y}",
                "detailmeta": "{center: [121.709337,37.308754],zoom:12}"
            }
        ],
        "aft": [
            {
                "name": "坡度大于15度耕地",
                "type": "slope",
                "processId": "f950cff2-07c8-461a-9c24-9162d59e2ef6_1749970088021_3012"
            },
            {
                "name": "细碎化耕地",
                "type": "fragmented",
                "processId": "f950cff2-07c8-461a-9c24-9162d59e2ef6_1749970088021_3012"
            },
            {
                "name": "在生态保护红线内",
                "type": "ecology",
                "processId": "f950cff2-07c8-461a-9c24-9162d59e2ef6_1749970088021_3012"
            },
            {
                "name": "在城镇开发边界内",
                "type": "urban",
                "processId": "f950cff2-07c8-461a-9c24-9162d59e2ef6_1749970088021_3012"
            }
        ]
    }
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", "进行已提取耕地地块合并")
        
        logger.info(f"开始执行{operation} - 坡度阈值: {slope_threshold}, 面积阈值: {fragment_area_threshold}")
        
        # 构建OGE代码
        oge_code = f"""import oge
oge.initialize()

service = oge.Service.initialize()
query = r"{data_query_sql}"
cultivated = service.getProcess("FeatureCollection.runBigQuery").execute(query, "geom") #耕地
cultivated_bounds = service.getProcess("FeatureCollection.bounds").execute(cultivated)
# 重点管控区域 大于15度耕地 几何
slope = service.getFeatureCollection("shp_podu") #坡度 GCS_China_Geodetic_Coordinate_System_2000
slope_morethan15_ = service.getProcess("FeatureCollection.filterMetadata").execute(slope, "pdjb", "greater_than", 4) #超过15度的耕地
slope_morethan15 = service.getProcess("FeatureCollection.reproject").execute(slope_morethan15_, "EPSG:4527")
slope_extent = service.getProcess("FeatureCollection.filterBounds").execute(slope_morethan15, cultivated_bounds)
urban_ = service.getFeatureCollection("shp_chengzhenkaifa") #城镇开发边界
urban = service.getProcess("FeatureCollection.reproject").execute(urban_, "EPSG:4527")
ecology_ = service.getFeatureCollection("shp_shengtaibaohu") #生态保护红线
ecology = service.getProcess("FeatureCollection.reproject").execute(ecology_, "EPSG:4527")

# cultivated_protected = service.getProcess("FeatureCollection.reproject").execute(cultivated, "EPSG:4527")

urban_intersection = service.getProcess("FeatureCollection.intersection").execute(cultivated, urban) #流出1
urban_erase = service.getProcess("FeatureCollection.erase").execute(cultivated, urban)
ecology_intersection = service.getProcess("FeatureCollection.intersection").execute(urban_erase, ecology) ##流出3
ecology_erase = service.getProcess("FeatureCollection.erase").execute(urban_erase, ecology)
slope_intersection = service.getProcess("FeatureCollection.intersection").execute(ecology_erase, slope_extent) #流出4
slope_erase = service.getProcess("FeatureCollection.erase").execute(ecology_erase, slope_extent)

#筛选细碎化耕地
cultivated1_area = service.getProcess("FeatureCollection.area").execute(slope_erase) #增加area字段
cultivated1_lessthan5 = service.getProcess("FeatureCollection.filterMetadata").execute(cultivated1_area, "area", "less_than", 3333.3333)
cultivated1_buffer = service.getProcess("FeatureCollection.buffer").execute(cultivated1_lessthan5, 10)
cultivated1_join = service.getProcess("FeatureCollection.spatialJoinOneToOne").execute(cultivated1_buffer, cultivated1_area, "buffer", "geom", True, "Intersects", ["area"], ["sum"])
cultivated1_subtract = service.getProcess("FeatureCollection.subtract").execute(cultivated1_join, "area_sum", "area", "area_peri")
deprecated1 = service.getProcess("FeatureCollection.filterMetadata").execute(cultivated1_subtract, "area_peri", "less_than", "6666.6667") #流出5

urban_intersection_reason = service.getProcess("FeatureCollection.constantColumn").execute(urban_intersection, "reason", "urban")
ecology_intersection_reason = service.getProcess("FeatureCollection.constantColumn").execute(ecology_intersection, "reason", "ecology")
slope_intersection_reason = service.getProcess("FeatureCollection.constantColumn").execute(slope_intersection, "reason", "slope")
deprecated1_reason = service.getProcess("FeatureCollection.constantColumn").execute(deprecated1, "reason", "fragmented")

deprecated = service.getProcess("FeatureCollection.mergeAll").execute([urban_intersection_reason,ecology_intersection_reason,slope_intersection_reason,deprecated1_reason]) #需要流出的耕地
deprecated_area = service.getProcess("FeatureCollection.area").execute(deprecated)
deprecated_CGCS2000 = service.getProcess("FeatureCollection.reproject").execute(deprecated_area, "EPSG:4490")
deprecated_CGCS2000.export("cultivated_protected")"""  
        
    
        logger.info(f"生成的OGE代码长度: {len(oge_code)} 字符")
        
        # 调用execute_dag_workflow执行完整工作流
        res_filename = "大模型farmland_outflow_result"+str(time.time())
        workflow_result = await execute_dag_workflow(
            code=oge_code,
            task_name=res_filename,
            filename=res_filename,
            auto_submit=True,
            wait_for_completion=wait_for_completion,
            format="geojson",
            check_interval=10,          # 每10秒轮询一次
            max_wait_time=1800,         # 30分钟超时
            ctx=ctx
        )
        
        # 解析workflow结果
        import json
        workflow_data = json.loads(workflow_result)
        
        if workflow_data.get("success"):
            # 提取关键信息
            workflow_details = workflow_data.get("data", {})
            final_status = workflow_details.get("final_status", "unknown")

            result_data = {
                "analysis_type": "farmland_outflow_analysis",
                "workflow_status": final_status,
                "dag_id": workflow_details.get("dag_ids", ["unknown"])[0]
                # "outflow_categories": [
                #     {"type": "urban", "description": "城镇开发边界内耕地"},
                #     {"type": "nature", "description": "自然保护地内耕地"},
                #     {"type": "ecology", "description": "生态保护红线内耕地"},
                #     {"type": "slope",   "description": f"坡度大于{slope_threshold}级的耕地"},
                #     {"type": "fragmented", "description": f"细碎化耕地（<{fragment_area_threshold/666.67:.1f}亩）"}
                # ]
            }
            if final_status == "completed":
                msg = f"{operation}执行成功 - 耕地流出分析已完成"
                # 插入结果信息到数据库，绑定recordId与结果文件，以便可以通过另一个接口查找
                workflow_report_payload = {
                    "uid": 324,
                    "algorithmName": "大模型耕地适宜性分析单工具",
                    "algorithmResultName": f"{res_filename}.geojson",  # 注意filename应不带扩展名
                    "resultStatus": 1,
                    "resultFileStatus": 1,
                    "processingTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 或传入值
                    "recordId": workflow_details.get("dag_ids", ["unknown"])[0],  # 或替换为自定义recordId
                    "filePath": f"oge-user/f950cff2-07c8-461a-9c24-9162d59e2ef6/result/"
                }

                # 调用统一封装函数,绑定id与结果文件
                workflow_report_result, _ = await call_api_with_timing(
                    url=INSERT_REPORT_URL,
                    json_data=workflow_report_payload,
                    use_intranet_token=True  # 关键点：开启内网token自动处理
                )

                # 你可以根据返回做额外处理
                if isinstance(workflow_report_result, dict) and workflow_report_result.get("code") == 200:
                    logger.info("算法处理结果成功上报绑定processId")
                else:
                    logger.warning(f"上报失败，响应: {workflow_report_result}")

            elif final_status == "submitted":
                primary_dag_id = workflow_details.get("dag_ids", ["unknown"])[0]
                msg = f"{operation}任务已提交 - dagId/processId/recordId: {primary_dag_id}\n" + \
                      f"请使用以下命令查询进度：\n" + \
                      f"query_task_status(recordId=\"{primary_dag_id}\")\n" + \
                      f"分析参数：坡度阈值{slope_threshold}级，面积阈值{fragment_area_threshold/666.67:.1f}亩"
            else:
                msg = f"{operation}执行完成 - 状态: {final_status}"
            
            result = Result.succ(
                data=result_data,
                msg=msg,
                map_type="farmland_suitability_analysis",
                operation=operation,
                api_endpoint="dag_workflow"
            )
        else:
            # 工作流执行失败
            workflow_details = workflow_data.get("data", {})
            error_msg = workflow_data.get("msg", "工作流执行失败")
            final_status = "failed"
            result = Result.failed(
                msg=f"{operation}失败: {error_msg}",
                map_type="farmland_suitability_analysis",
                operation=operation
            )
            result.data = workflow_data.get("data")
        additional_json_data = update_process_id(additional_json_data,workflow_details.get("dag_ids", ["unknown"])[0])
        if ctx:
            await ctx.session.send_log_message("info", "耕地地块合并完成")
        
        logger.info(f"{operation}执行完成 - 最终状态: {final_status}")
        # 演示，需要加进去的数据
        
        result.data = {**(result.data or {}), **additional_json_data}
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="farmland_suitability_analysis",
            operation=operation
        )
        result.data = {**(result.data or {}), **additional_json_data}
        return result.model_dump_json()


# @mcp.tool()
async def run_big_query(
    # query: str,
    # geometry_column: str = "geom",
    ctx: Context = None
) -> str:
    """
    查询山东省耕地矢量,只会返回数据的标识，通过标识后续可以访问结果数据
    
    Parameters:
        无参数
    """
    operation = "大数据查询"
    query = "SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田')"
    geometry_column = "geom"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - 查询: {query[:100]}...")
        
        # 构建算法参数
        algorithm_args = {
            "query": query,
            "geometryColumn": geometry_column
        }
        
        # 调用内网API
        api_payload = {
            "name": "FeatureCollection.runBigQuery",
            "args": algorithm_args,
            "dockerImageSource": "DOCKER_HUB"
        }
        
        api_result, execution_time = await call_api_with_timing(
            url=INTRANET_API_BASE_URL,
            json_data=api_payload,
            use_intranet_token=True
        )
        
        if "error" in api_result:
            error_detail = api_result.get('error', '未知错误')
            status_code = api_result.get('status_code', '未知状态码')
            result = Result.failed(
                msg=f"{operation}失败: {error_detail} (状态码: {status_code})",
                map_type="run_big_query",
                operation=operation
            )
        else:
            result = Result.succ(
                data=api_result,
                msg=f"{operation}执行成功",
                map_type="run_big_query",
                operation=operation,
                execution_time=execution_time,
                api_endpoint="intranet"
            )
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成，耗时{execution_time:.2f}秒")
        
        logger.info(f"{operation}执行完成 - 耗时: {execution_time:.2f}秒")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="run_big_query",
            operation=operation
        )
        return result.model_dump_json()


# ============ DAG批处理工具 ============

# @mcp.tool()
async def execute_code_to_dag(
    code: str,
    user_id: str = DEFAULT_USER_ID,
    sample_name: str = "",
    auth_token: str = None,
    ctx: Context = None
) -> str:
    """
    将代码转化为DAG生成任务
    
    Parameters:
    - code: 要执行的OGE代码
    - user_id: 用户UUID
    - sample_name: 示例代码名称（可为空）
    - auth_token: 认证Token（可选，默认使用全局Token）
    """
    operation = "代码转DAG任务"
    
    try:
        # if ctx:
        #     await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation}")
        
        # 构建API URL
        api_url = f"{DAG_API_BASE_URL}/executeCode"
        
        # 构建请求数据
        request_data = {
            "code": code,
            "userId": user_id,
            "sampleName": sample_name
        }
        
        # 准备认证
        use_custom_token = bool(auth_token)
        final_headers = None
        
        if use_custom_token:
            if not auth_token.startswith("Bearer "):
                auth_token = f"Bearer {auth_token}"
            final_headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }
        
        logger.info(f"调用API: {api_url}")
        logger.info(f"请求数据: userId={user_id}, sampleName={sample_name}")
        
        # 调用API
        api_result, execution_time = await call_api_with_timing(
            url=api_url,
            method="POST",
            json_data=request_data,
            headers=final_headers,
            timeout=300,     # 5分钟超时，DAG创建可能需要更长时间
            use_intranet_token=not use_custom_token
        )
        
        if "error" not in api_result:
            # 提取DAG信息
            dags = api_result.get("dags", {})
            space_params = api_result.get("spaceParams", {})
            log_info = api_result.get("log", "")
            
            # 提取DAG ID
            dag_ids = []
            for key, value in dags.items():
                if isinstance(value, dict):
                    dag_ids.append(key)
                elif isinstance(value, str):
                    dag_ids.append(value)
            
            result_data = {
                "dags": dags,
                "dag_ids": dag_ids,
                "space_params": space_params,
                "log": log_info,
                "user_id": user_id,
                "sample_name": sample_name
            }
            
            result = Result.succ(
                data=result_data,
                msg=f"{operation}成功，生成了{len(dag_ids)}个DAG任务",
                operation=operation,
                map_type="execute_code_to_dag",
                execution_time=execution_time,
                api_endpoint="dag"
            )
            
            logger.info(f"{operation}成功 - 生成DAG数量: {len(dag_ids)}")
            
        else:
            result = Result.failed(
                msg=f"{operation}失败: {api_result.get('error', '未知错误')}",
                map_type="execute_code_to_dag",
                operation=operation
            )
        
        # if ctx:
        #     await ctx.session.send_log_message("info", f"{operation}执行完成，耗时{execution_time:.2f}秒")
        
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="execute_code_to_dag",
            operation=operation
        )
        return result.model_dump_json()

# @mcp.tool()
async def submit_batch_task(
    dag_id: str,
    task_name: str = None,
    filename: str = None,
    crs: str = "EPSG:4326",
    scale: str = "1000",
    format: str = "geojson",
    username: str = DEFAULT_USERNAME,
    script: str = "",
    auth_token: str = None,
    ctx: Context = None
) -> str:
    """
    提交批处理任务运行
    
    Parameters:
    - dag_id: DAG任务ID
    - task_name: 任务名称（可选，默认自动生成）
    - filename: 文件名（可选，默认自动生成）
    - crs: 坐标参考系统
    - scale: 比例尺
    - format: 输出格式
    - username: 用户名
    - script: 脚本代码
    - auth_token: 认证Token（可选，默认使用全局Token）
    """
    operation = "提交批处理任务"
    
    try:
        # if ctx:
        #     await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - DAG ID: {dag_id}")
        
        # 构建API URL
        api_url = f"{DAG_API_BASE_URL}/addTaskRecord"
        
        # 生成默认任务名和文件名（如果未提供）
        if not task_name:
            timestamp = time.strftime("%Y_%m_%d_%H_%M_%S")
            task_name = f"task_{timestamp}"
            
        if not filename:
            timestamp = time.strftime("%Y_%m_%d_%H_%M_%S")
            filename = f"file_{timestamp}"
        
        # 构建请求数据
        request_data = {
            "taskName": task_name,
            "crs": crs,
            "scale": scale,
            "filename": filename,
            "format": format,
            "id": dag_id,
            "userName": username,
            "script": script
        }
        
        # 准备认证
        use_custom_token = bool(auth_token)
        final_headers = None
        
        if use_custom_token:
            if not auth_token.startswith("Bearer "):
                auth_token = f"Bearer {auth_token}"
            final_headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }
        
        logger.info(f"调用API: {api_url}")
        logger.info(f"请求数据: taskName={task_name}, dagId={dag_id}")
        
        # 调用API
        api_result, execution_time = await call_api_with_timing(
            url=api_url,
            method="POST",
            json_data=request_data,
            headers=final_headers,
            timeout=300,     # 5分钟超时，任务提交可能需要更长时间
            use_intranet_token=not use_custom_token
        )
        
        if "error" not in api_result:
            # 检查API响应格式
            if api_result.get("code") == 200:
                task_data = api_result.get("data", {})
                
                result_data = {
                    "batch_session_id": task_data.get("batchSessionId"),
                    "task_id": task_data.get("id"),
                    "dag_id": task_data.get("dagId"),
                    "task_name": task_data.get("taskName"),
                    "state": task_data.get("state"),
                    "filename": task_data.get("filename"),
                    "format": task_data.get("format"),
                    "scale": task_data.get("scale"),
                    "crs": task_data.get("crs"),
                    "user_id": task_data.get("userId"),
                    "username": task_data.get("userName"),
                    "folder": task_data.get("folder"),
                    "api_response": api_result
                }
                
                result = Result.succ(
                    data=result_data,
                    msg=f"{operation}成功，任务状态: {task_data.get('state', 'unknown')}",
                    operation=operation,
                    map_type="submit_batch_task",
                    execution_time=execution_time,
                    api_endpoint="dag"
                )
                
                logger.info(f"{operation}成功 - 任务ID: {task_data.get('id')}, 状态: {task_data.get('state')}")
                
            else:
                result = Result.failed(
                    msg=f"{operation}失败: {api_result.get('msg', '未知错误')}",
                    map_type="submit_batch_task",
                    operation=operation
                )
        else:
            result = Result.failed(
                msg=f"{operation}失败: {api_result.get('error', '未知错误')}",
                map_type="submit_batch_task",
                operation=operation
            )
        
        # if ctx:
        #     await ctx.session.send_log_message("info", f"{operation}执行完成，耗时{execution_time:.2f}秒")
        
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="submit_batch_task",
            operation=operation
        )
        return result.model_dump_json()


# @mcp.tool() 
async def old_query_task_status(
    dag_id: str,
    auth_token: str = None,
    ctx: Context = None
) -> str:
    """
    查询批处理任务执行状态，并通过结果目录接口校验最终结果状态
    
    Parameters:
    - dag_id: DAG 任务 ID
    - auth_token: 认证 Token（可选，默认使用全局 Token）
    """
    operation = "查询任务状态"
    RESULT_CATALOG_URL = "http://172.20.70.141/api/asset/batch-result/catalog"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行 {operation}...")
        logger.info(f"开始执行 {operation} - DAG ID: {dag_id}")
        
        # 构建 DAG 状态接口 URL
        api_url = f"{DAG_API_BASE_URL}/getState"
        
        # 准备认证头
        use_custom_token = bool(auth_token)
        final_headers = None
        if use_custom_token:
            if not auth_token.startswith("Bearer "):
                auth_token = f"Bearer {auth_token}"
            final_headers = {
                "Content-Type": "application/json",
                "Authorization": auth_token
            }
        
        params = {"dagId": dag_id}
        
        # 调用 DAG 状态接口
        if use_custom_token:
            start_time = time.perf_counter()
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(api_url, params=params, headers=final_headers)
            execution_time = time.perf_counter() - start_time
            
            if response.status_code == 200:
                # 解析返回的状态（可能是 JSON，也可能是纯文本）
                text = response.text.strip()
                if not text:
                    status_str = "unknown"
                    raw = None
                else:
                    # 解析 JSON 或当作纯文本
                    try:
                        parsed = response.json()
                    except ValueError:
                        parsed = text
                    if isinstance(parsed, dict):
                        raw = parsed
                        status_str = parsed.get("status", str(parsed))
                    else:
                        raw = parsed
                        status_str = str(parsed)
                
                # 初步封装结果
                result_data = {
                    "dag_id": dag_id,
                    "status": status_str,
                    "is_running": status_str in ["running", "starting"],
                    # 后面会根据目录接口覆盖 is_completed/is_failed
                    "is_completed": False,
                    "is_failed": False,
                    "raw_dag_response": raw,
                }
                
                # —— 新增：调用结果目录接口校验最终状态 —— #
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        catalog_resp = await client.get(
                            RESULT_CATALOG_URL,
                            params={"dagId": dag_id},
                            headers=final_headers
                        )
                    if catalog_resp.status_code == 200:
                        catalog = catalog_resp.json()
                        entries = catalog.get("data", [])
                        entry = next((e for e in entries if e.get("dagId") == dag_id), None)
                        if entry:
                            final_state = entry.get("state")
                            result_data["final_state"] = final_state
                            result_data["catalog_entry"] = entry
                            
                            if final_state == "success":
                                result_data["is_completed"] = True
                                result_data["is_failed"] = False
                            else:
                                result_data["is_completed"] = False
                                result_data["is_failed"] = True
                        else:
                            # 没有找到对应记录，视为异常
                            result_data["final_state"] = "unknown"
                            result_data["is_failed"] = True
                    else:
                        logger.warning(f"查询结果目录失败 - HTTP {catalog_resp.status_code}")
                except Exception as e:
                    logger.error(f"查询结果目录异常: {e}")
                # —— 校验结束 —— #
                
                result = Result.succ(
                    data=result_data,
                    msg=(
                        f"{operation}成功，DAG 状态: {status_str}；"
                        f"最终结果状态: {result_data.get('final_state', 'unknown')}"
                    ),
                    operation=operation,
                    execution_time=execution_time,
                    api_endpoint="dag"
                )
                logger.info(
                    f"{operation}成功 - DAG ID: {dag_id}, "
                    f"最终结果状态: {result_data.get('final_state')}"
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                result = Result.failed(
                    msg=f"{operation}失败: {error_msg}",
                    operation=operation
                )
                logger.error(f"{operation}失败 - {error_msg}")
        
        else:
            # 使用内网 Token（可刷新的逻辑）
            get_params = {"dagId": dag_id}
            api_result, execution_time = await call_api_with_timing(
                url=f"{DAG_API_BASE_URL}/getState",
                method="GET",
                headers={"params": get_params},
                timeout=30,
                use_intranet_token=True
            )
            
            if "error" not in api_result:
                # status_str = api_result.get("status", str(api_result))
                if isinstance(api_result, dict):
                    status_str = api_result.get("status", str(api_result))
                else:
                    status_str = str(api_result)
                result_data = {
                    "dag_id": dag_id,
                    "status": status_str,
                    "is_running": status_str in ["running", "starting"],
                    "is_completed": False,
                    "is_failed": False,
                    "raw_dag_response": api_result,
                }
                
                # —— 新增：内网模式下调用结果目录接口 —— #
                try:
                    catalog_result, _ = await call_api_with_timing(
                        url=RESULT_CATALOG_URL,
                        method="GET",
                        headers={"params": {"dagId": dag_id}},
                        timeout=30,
                        use_intranet_token=True
                    )
                    catalog_result, _ = await call_api_with_timing(
                    url=RESULT_CATALOG_URL,
                    method="GET",
                    headers={"params": {"dagId": dag_id}},
                    timeout=30,
                    use_intranet_token=True
                    )
                    # 先尝试把 catalog_result 变成 dict
                    if isinstance(catalog_result, str):
                        try:
                            catalog_result = json.loads(catalog_result)
                        except json.JSONDecodeError:
                            catalog_result = None

                    if isinstance(catalog_result, dict) and "data" in catalog_result:
                        raw_list = catalog_result.get("data") or []
                        # 只保留 dict 项并匹配 dagId
                        entries = [e for e in raw_list if isinstance(e, dict)]
                        entry = next((e for e in entries if e.get("dagId") == dag_id), None)
                    if entry:
                        final_state = entry.get("state")
                        result_data["final_state"] = final_state
                        result_data["catalog_entry"] = entry
                        if final_state == "success":
                            result_data["is_completed"] = True
                            result_data["is_failed"] = False
                        else:
                            result_data["is_completed"] = False
                            result_data["is_failed"] = True
                    else:
                        result_data["final_state"] = "unknown"
                        result_data["is_failed"] = True
                except Exception as e:
                    logger.error(f"查询结果目录异常: {e}")
                # —— 校验结束 —— #
                
                result = Result.succ(
                    data=result_data,
                    msg=(
                        f"{operation}成功，DAG 状态: {status_str}；"
                        f"最终结果状态: {result_data.get('final_state', 'unknown')}"
                    ),
                    operation=operation,
                    execution_time=execution_time,
                    api_endpoint="dag"
                )
                logger.info(
                    f"{operation}成功 - DAG ID: {dag_id}, "
                    f"最终结果状态: {result_data.get('final_state')}"
                )
            else:
                result = Result.failed(
                    msg=f"{operation}失败: {api_result.get('error')}",
                    operation=operation
                )
                logger.error(f"{operation}失败 - {api_result.get('error')}")
        
        if ctx:
            await ctx.session.send_log_message(
                "info",
                f"{operation}执行完成，耗时 {execution_time:.2f} 秒"
            )
        return result.model_dump_json()
    
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"{operation}执行失败: {e}\n{tb}")
        result = Result.failed(
            msg=f"{operation}执行失败: {e}\n{tb}",
            operation=operation
        )
        return result.model_dump_json()


# 逻辑简化版
@mcp.tool()
async def query_task_status(
    dag_id: Annotated[str,Field(description="地块合并的processId，也是recordId/dagId",required = True)],
    auth_token: Annotated[str,Field(description="验证token，一般不需要",required = False)] = None,
    ctx: Context = None
) -> str:
    """
    查询批处理任务执行状态。除非用户指定使用，否则不去调用。
    """
    operation = "查询任务状态"
    DAG_STATE_URL = f"{DAG_API_BASE_URL}/getState"
    # CATALOG_URL   = "http://172.20.70.141/api/asset/batch-result/catalog"

    # 准备 headers & 模式
    use_custom = bool(auth_token)
    if use_custom and not auth_token.startswith("Bearer "):
        auth_token = f"Bearer {auth_token}"
    common_headers = {"Content-Type": "application/json"} if use_custom else {}
    if use_custom:
        common_headers["Authorization"] = auth_token

    # 小工具：发起请求（可复用 httpx 或 call_api_with_timing）
    async def fetch(url: str, params: dict):
        if use_custom:
            start = time.perf_counter()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=params, headers=common_headers)
            return resp, time.perf_counter() - start
        else:
            return await call_api_with_timing(
                url=url,
                method="GET",
                params=params,
                timeout=30,
                use_intranet_token=True
            )

    # 小工具：解析 DAG 接口返回，统一成 (status_str, raw)
    def parse_status(resp_or_obj):
        # httpx.Response 分支
        if isinstance(resp_or_obj, httpx.Response):
            text = resp_or_obj.text.strip()
            if not text:
                return "unknown", None
            try:
                parsed = resp_or_obj.json()
            except ValueError:
                return text, text
        else:
            parsed = resp_or_obj

        if isinstance(parsed, dict):
            return parsed.get("status", str(parsed)), parsed
        else:
            return str(parsed), parsed

    # 小工具：查询目录并提取 entry
    async def check_catalog():
        cat_resp, _ = await fetch(CATALOG_URL, {"dagId": dag_id})
        # 如果是 httpx.Response，需要先 .json()
        if isinstance(cat_resp, httpx.Response):
            if cat_resp.status_code != 200:
                logger.warning(f"查询结果目录失败 HTTP {cat_resp.status_code}")
                return None
            try:
                catalog = cat_resp.json()
            except ValueError:
                return None
        else:
            catalog = cat_resp if isinstance(cat_resp, dict) else None

        if not isinstance(catalog, dict):
            return None

        data = catalog.get("data") or []
        for item in data:
            if isinstance(item, dict) and item.get("dagId") == dag_id:
                return item
        return None

    try:
        # if ctx:
        #     await ctx.session.send_log_message("info", f"开始执行 {operation}...")
        logger.info(f"{operation} 开始 - DAG ID: {dag_id}")

        result_data = {
            "dag_id": dag_id,
            "status": "",
            "is_running": "",
            "is_completed": False,
            "is_failed": False,
            "raw_dag_response": ""
        }


        # 先用 DAG API 判断是否还在跑
        raw_resp, elapsed = await fetch(DAG_STATE_URL, {"dagId": dag_id})
        status_str, raw = parse_status(raw_resp)
        result_data["status"]     = status_str
        result_data["is_running"] = status_str in ["starting","running"]
        # result_data["raw_dag_response"] = raw

        # 只有当 DAG 不再 running 时，才去查目录确认最终结果
        if not result_data["is_running"]:
            entry = await check_catalog()
            if entry:
                final_state = entry.get("state")
                result_data["final_state"]   = final_state
                result_data["catalog_entry"] = entry
                result_data["is_completed"]  = (final_state == "success")
                result_data["is_failed"]     = (final_state in ["failed", "error", "dead", "killed"])
            else:
                result_data["final_state"] = "unknown"
                result_data["is_failed"]   = True
        else:
            # 还在跑，不判失败
            result_data["final_state"] = None
            result_data["is_completed"] = False
            result_data["is_failed"]    = False

        # 4. 构建并返回 Result
        result = Result.succ(
            data=result_data,
            msg=(
                f"{operation}成功，DAG 状态: {status_str}；"
                f"最终结果状态: {result_data.get('final_state')}"
            ),
            operation=operation,
            map_type="query_task_status",
            execution_time=elapsed,
            api_endpoint="dag"
        )
        logger.info(f"{operation} 成功 - 最终状态: {result_data.get('final_state')}")
        return result.model_dump_json()

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"{operation}执行失败: {e}\n{tb}")
        result = Result.failed(
            msg=f"{operation}执行失败: {e}\n{tb}",
            map_type="query_task_status",
            operation=operation
        )
        return result.model_dump_json()


# @mcp.tool()
async def execute_dag_workflow(
    code: str,
    user_id: str = DEFAULT_USER_ID,
    sample_name: str = "",
    task_name: str = None,
    filename: str = None,
    crs: str = "EPSG:4326",
    scale: str = "1000",
    format: str = "tif",
    username: str = DEFAULT_USERNAME,
    auth_token: str = None,
    auto_submit: bool = True,
    wait_for_completion: bool = False,
    check_interval: int = 10,     # 默认15秒检查一次
    max_wait_time: int = 300,    # 默认5分钟超时
    ctx: Context = None
) -> str:
    """
    执行完整的DAG批处理工作流：代码转DAG -> 提交任务 -> (可选)等待完成
    
    Parameters:
    - code: OGE代码
    - user_id: 用户UUID
    - sample_name: 示例代码名称
    - task_name: 任务名称（可选）
    - filename: 文件名（可选）
    - crs: 坐标参考系统
    - scale: 比例尺
    - format: 输出格式
    - username: 用户名
    - auth_token: 认证Token（可选）
    - auto_submit: 是否自动提交任务
    - wait_for_completion: 是否等待任务完成
    - check_interval: 状态检查间隔（秒）
    - max_wait_time: 最大等待时间（秒）
    """
    operation = "DAG批处理工作流"
    workflow_start_time = time.perf_counter()
    
    try:
        # if ctx:
        #     await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation}")
        
        workflow_results = {
            "steps": [],
            "final_status": "unknown",
            "dag_ids": [],
            "task_info": None,
            "execution_times": {}
        }
        
        # 步骤1: 代码转DAG
        # if ctx:
        #     await ctx.session.send_log_message("info", "步骤1: 代码转换为DAG...")
        
        dag_result_json = await execute_code_to_dag(
            code=code,
            user_id=user_id,
            sample_name=sample_name,
            auth_token=auth_token,
            ctx=ctx
        )
        
        dag_result = json.loads(dag_result_json)
        workflow_results["steps"].append({
            "step": 1,
            "name": "代码转DAG",
            "success": dag_result.get("success", False),
            "result": dag_result
        })
        
        if not dag_result.get("success"):
            workflow_results["final_status"] = "failed_at_dag_creation"
            result = Result.failed(
                msg=f"{operation}失败：代码转DAG步骤失败",
                map_type="execute_dag_workflow",
                operation=operation
            )
            result.data = workflow_results
            return result.model_dump_json()
        
        # 获取DAG信息
        dag_data = dag_result.get("data", {})
        dag_ids = dag_data.get("dag_ids", [])
        workflow_results["dag_ids"] = dag_ids
        
        if not dag_ids:
            workflow_results["final_status"] = "no_dag_generated"
            result = Result.failed(
                msg=f"{operation}失败：未生成DAG任务",
                map_type="execute_dag_workflow",
                operation=operation
            )
            result.data = workflow_results
            return result.model_dump_json()
        
        # 使用第一个DAG ID
        primary_dag_id = dag_ids[0]
        logger.info(f"使用DAG ID: {primary_dag_id}")
        
        if auto_submit:
            # 步骤2: 提交批处理任务
            # if ctx:
            #     await ctx.session.send_log_message("info", f"步骤2: 提交批处理任务 (DAG: {primary_dag_id})...")
            
            submit_result_json = await submit_batch_task(
                dag_id=primary_dag_id,
                task_name=task_name,
                filename=filename,
                crs=crs,
                scale=scale,
                format=format,
                username=username,
                script=code,
                auth_token=auth_token,
                ctx=ctx
            )
            
            # script字段内容太多了，是执行的脚本，不需要暴露出来。
            submit_result = json.loads(submit_result_json)
            def _remove_script(obj):
                if isinstance(obj, dict):
                    obj.pop("script", None)
                    for v in obj.values():
                        _remove_script(v)
                elif isinstance(obj, list):
                    for item in obj:
                        _remove_script(item)

            _remove_script(submit_result)

            # tmp_data = submit_result.get("data")
            # if isinstance(tmp_data, dict) and "script" in tmp_data:
            #     tmp_data.pop("script", None)
            #     submit_result["data"] = tmp_data
            workflow_results["steps"].append({
                "step": 2,
                "name": "提交批处理任务",
                "success": submit_result.get("success", False),
                "result": submit_result
            })
            
            if not submit_result.get("success"):
                workflow_results["final_status"] = "failed_at_task_submission"
                result = Result.failed(
                    msg=f"{operation}失败：任务提交步骤失败",
                    map_type="execute_dag_workflow",
                    operation=operation
                )
                result.data = workflow_results
                return result.model_dump_json()
            
            # 获取任务信息
            task_data = submit_result.get("data", {})
            workflow_results["task_info"] = task_data
            
            if wait_for_completion:
                # 步骤3: 等待任务完成
                # if ctx:
                #     await ctx.session.send_log_message("info", f"步骤3: 等待任务完成...")
                # 等待6s，等任务真的提交后再去查询
                await asyncio.sleep(10)
                
                waited_time = 0
                final_status = "unknown"
                try:
                    while waited_time < max_wait_time:
                        status_result_json = await query_task_status(
                            dag_id=primary_dag_id,
                            # auth_token=auth_token,
                            ctx=None  # 避免过多日志
                        )
                        
                        status_result = json.loads(status_result_json)
                        
                        if status_result.get("success"):
                            status_data = status_result.get("data", {})
                            current_status = status_data.get("status", "unknown")
                            
                            if status_data.get("is_completed"):
                                final_status = "completed"
                                workflow_results["final_status"] = "completed"
                                logger.info(f"任务已完成: {current_status}")
                                break
                            elif status_data.get("is_failed"):
                                final_status = "failed"
                                workflow_results["final_status"] = "failed"
                                logger.info(f"任务失败: {current_status}")
                                break
                            # else:
                            #     # 任务仍在运行
                            #     if ctx:
                            #         await ctx.session.send_log_message("info", f"任务状态: {current_status}, 已等待 {waited_time}s")
                        
                        await asyncio.sleep(check_interval)
                        waited_time += check_interval
                except Exception as e:
                    tb = traceback.format_exc()
                    logger.error(f"query_task_status 报错：{tb}", exc_info=True)
                    print(tb)
                if waited_time >= max_wait_time:
                    workflow_results["final_status"] = "timeout"
                    final_status = "timeout"
                
                workflow_results["steps"].append({
                    "step": 3,
                    "name": "等待任务完成",
                    "success": final_status == "completed",
                    "final_status": final_status,
                    "waited_time": waited_time
                })
            else:
                workflow_results["final_status"] = "submitted"
        else:
            workflow_results["final_status"] = "dag_created"
        
        total_execution_time = time.perf_counter() - workflow_start_time
        workflow_results["execution_times"]["total"] = total_execution_time
        
        # 构建最终结果
        if workflow_results["final_status"] in ["completed", "submitted", "dag_created"]:
            result = Result.succ(
                data=workflow_results,
                msg=f"{operation}成功，状态: {workflow_results['final_status']}",
                map_type="execute_dag_workflow",
                operation=operation,
                execution_time=total_execution_time,
                api_endpoint="dag"
            )
        else:
            result = Result.failed(
                msg=f"{operation}完成但状态异常: {workflow_results['final_status']}",
                map_type="execute_dag_workflow",
                operation=operation
            )
            result.data = workflow_results
        
        # if ctx:
        #     await ctx.session.send_log_message("info", f"{operation}执行完成，总耗时{total_execution_time:.2f}秒")
        
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="execute_dag_workflow",
            operation=operation
        )
        result.data = workflow_results
        return result.model_dump_json()

# ============ 其他方法 ============

def update_process_id(data: dict, new_process_id: str):
    """用于630演示，更新processId"""
    if "aft" in data:
        for item in data["aft"]:
            item["processId"] = new_process_id
    return data


# ============ HTTP服务器设置 ============

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """创建支持SSE的Starlette应用"""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    async def handle_health(request: Request):
        return JSONResponse({
            "status": "healthy",
            "server": MCP_SERVER_NAME,
            "endpoints": {
                "sse": "/sse",
                "health": "/health",
                "messages": "/messages/"
            }
        })

    async def handle_info(request: Request):
        return JSONResponse({
            "server_name": MCP_SERVER_NAME,
            "version": "2.4.0",
            "description": "山东耕地流出分析MCP服务器 - 增强版 (10个核心工具 + 自动Token管理)",
            "features": [
                "自动Token刷新",
                "手动Token刷新",
                "坡向分析", 
                "山东耕地流出分析",
                "多约束耕地流出分析",
                "大数据查询",
                "DAG批处理工作流",
                "代码转DAG任务",
                "批处理任务提交",
                "任务状态查询",
                "SSE传输",
                "HTTP endpoints",
                "结构化日志",
                "性能监控"
            ],
            "apis": {
                "intranet_api": INTRANET_API_BASE_URL,
                "dag_api": DAG_API_BASE_URL
            },
            "available_tools": [
                "refresh_token",
                "check_token_status",
                "coverage_aspect_analysis", 
                "shandong_farmland_outflow",
                "farmland_outflow",
                "run_big_query",
                "execute_code_to_dag",
                "submit_batch_task", 
                "query_task_status",
                "execute_dag_workflow"
            ],
            "token_management": {
                "type": "automatic",
                "description": "自动检测token过期(40003)并刷新，也支持手动刷新",
                "auto_refresh": "检测到40003错误时自动刷新",
                "manual_refresh": "可使用refresh_token工具手动刷新", 
                "credentials": "edu_admin/123456",
                "format": "Bearer <jwt_token>"
            }
        })

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/health", endpoint=handle_health),
            Route("/info", endpoint=handle_info),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

# ============ 主程序 ============

async def run_stdio_server():
    """运行stdio模式的服务器"""
    logger.info("启动山东耕地流出分析MCP服务器 (stdio模式)...")
    
    try:
        from mcp import stdio_server
        
        async with stdio_server() as streams:
            await mcp._mcp_server.run(
                streams[0], streams[1], 
                mcp._mcp_server.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器运行出错: {e}")
    finally:
        logger.info("MCP服务器已关闭")

def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """运行HTTP模式的服务器"""
    logger.info(f"启动山东耕地流出分析MCP服务器 (HTTP模式) - {host}:{port}")
    
    mcp_server = mcp._mcp_server
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    uvicorn.run(starlette_app, host=host, port=port)

# 在文件末尾添加测试工具

# @mcp.tool()
async def test_dag_status_api(
    dag_id: str,
    ctx: Context = None
) -> str:
    """
    测试DAG状态查询API - 直接调用不经过封装
    
    用于诊断query_task_status的问题
    """
    operation = "测试DAG状态API"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation} - DAG ID: {dag_id}")
        
        # 构建API URL
        api_url = f"{DAG_API_BASE_URL}/getState"
        params = {"dagId": dag_id}
        
        logger.info(f"测试API调用: {api_url}?dagId={dag_id}")
        
        start_time = time.perf_counter()
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                api_url,
                params=params,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": INTRANET_AUTH_TOKEN
                }
            )
            
            execution_time = time.perf_counter() - start_time
            
            # 详细记录响应信息
            response_info = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content),
                "text_preview": response.text[:200] if response.text else "Empty",
                "is_json": False,
                "execution_time": execution_time
            }
            
            # 尝试解析JSON
            json_data = None
            try:
                json_data = response.json()
                response_info["is_json"] = True
                response_info["json_data"] = json_data
            except Exception as e:
                response_info["json_error"] = str(e)
            
            result = Result.succ(
                data=response_info,
                msg=f"{operation}完成 - 状态码: {response.status_code}",
                map_type="test_dag_status_api",
                operation=operation,
                execution_time=execution_time,
                api_endpoint="dag_test"
            )
            
            logger.info(f"{operation}完成 - 状态码: {response.status_code}, 内容长度: {len(response.content)}")
            
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成")
        
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            map_type="test_dag_status_api",
            operation=operation
        )
        return result.model_dump_json()
    
# 本地测试用
# if __name__ == "__main__":
#     # asyncio.run(shandong_farmland_vector_query_new(["狂山村","阿萨德见客户","雪野镇"]))
#     asyncio.run(farmland_suitability_analysis("SELECT * FROM shp_guotubiangeng WHERE DLMC IN ('旱地', '水浇地', '水田') AND ZLDWMC IN ('狂山村', '东下游村')"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='山东耕地流出分析MCP服务器 - 增强版')
    parser.add_argument('--mode', choices=['stdio', 'http'], default='stdio', help='运行模式')
    parser.add_argument('--host', default='0.0.0.0', help='HTTP模式的绑定地址')
    parser.add_argument('--port', type=int, default=8000, help='HTTP模式的监听端口')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'stdio':
            asyncio.run(run_stdio_server())
        else:
            run_http_server(args.host, args.port)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}") 

