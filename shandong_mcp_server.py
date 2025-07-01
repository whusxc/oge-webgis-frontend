#!/usr/bin/env python3
"""
山东耕地流出分析 MCP服务器 - 遥感大楼适配版
整合FastMCP框架，支持HTTP和stdio两种传输方式
适配遥感大楼环境 (10.101.240.x 网段)
"""

import asyncio
import json
import logging
import httpx
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar
from pydantic import BaseModel
from enum import IntEnum

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

# ============ 配置部分 - 更新为可用OGE环境 ============

# 服务器配置
MCP_SERVER_NAME = "oge-mcp-analysis-server"

# 根据志威哥提供的信息更新配置
# 楼下服务器网关16555端口穿透到111.37.195.111的7002端口
OGE_EXTERNAL_URL = "http://111.37.195.111:7002"  # 外网穿透地址
OGE_GATEWAY_PORT = "16555"  # 内网网关端口

# API配置 - 使用可用的穿透服务器
OGE_BACKEND_URL = OGE_EXTERNAL_URL  # 使用外网穿透地址
OGE_FRONTEND_URL = OGE_EXTERNAL_URL  # 前端也使用同一地址

# 适配后的API地址配置
OGE_API_BASE_URL = f"{OGE_BACKEND_URL}/gateway/computation-api/process"
INTRANET_API_BASE_URL = f"{OGE_BACKEND_URL}/api/computation/process"
INTRANET_AUTH_TOKEN = "Bearer TOKEN_TO_BE_UPDATED"  # 需要根据实际环境获取

# 计算服务配置（如果需要的话）
COMPUTE_CLUSTER_MASTER = OGE_BACKEND_URL  # 使用同一后端地址
DAG_API_BASE_URL = f"{COMPUTE_CLUSTER_MASTER}/api/oge-dag"
LIVY_API_BASE_URL = f"{COMPUTE_CLUSTER_MASTER}/livy"

# 用户配置
DEFAULT_USER_ID = "mcp-user"
DEFAULT_USERNAME = "admin"  # 根据实际情况调整

# 移除不可用的MinIO配置，使用OGE后端存储
# MINIO_ENDPOINT = "http://10.101.240.23:9007"  # 注释掉不可用的配置
# MINIO_ACCESS_KEY = "oge"
# MINIO_SECRET_KEY = "ypfamily608"

# ============ 响应格式定义 ============

class RetCode(IntEnum):
    SUCCESS = 0
    FAILED = 1

class Result(BaseModel):
    success: bool = False
    code: Optional[int] = None
    msg: Optional[str] = None
    data: Optional[T] = None
    operation: Optional[str] = None
    execution_time: Optional[float] = None
    api_endpoint: Optional[str] = "oge"

    @classmethod
    def succ(cls, data: T = None, msg="成功", operation=None, execution_time=None, api_endpoint="oge"):
        return cls(
            success=True, 
            code=RetCode.SUCCESS, 
            msg=msg, 
            data=data,
            operation=operation,
            execution_time=execution_time,
            api_endpoint=api_endpoint
        )

    @classmethod
    def failed(cls, code: int = RetCode.FAILED, msg="操作失败", operation=None):
        return cls(success=False, code=code, msg=msg, operation=operation)

# ============ 日志配置 ============

def setup_logger(name: str = None, file: str = None, level=logging.INFO) -> logging.Logger:
    """设置结构化日志"""
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(level)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt='%(name)s - %(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件日志
    if file:
        Path(file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(filename=file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    # 控制台日志
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)

    return logger

# 创建日志实例
logger = setup_logger("yaogan_mcp", "logs/yaogan_mcp.log")
api_logger = setup_logger("yaogan_api", "logs/api_calls.log")

# ============ FastMCP实例 ============

mcp = FastMCP(MCP_SERVER_NAME)

# ============ Token管理 - 适配遥感大楼环境 ============

async def refresh_intranet_token() -> tuple[bool, str]:
    """自动刷新OGE环境token - 适配可用服务器"""
    global INTRANET_AUTH_TOKEN
    
    try:
        logger.info("开始刷新OGE环境token...")
        
        # 使用可用服务器的认证API
        url = f"{OGE_BACKEND_URL}/api/oauth/token"
        
        params = {
            "scopes": "web",
            "client_secret": "123456",
            "client_id": "oge_client", 
            "grant_type": "password",
            "username": DEFAULT_USERNAME,
            "password": "123456"  # 根据实际环境修改
        }
        
        body = {
            "username": DEFAULT_USERNAME,
            "password": "123456"  # 根据实际环境修改
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"尝试连接OGE服务器: {url}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params, json=body, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'token' in data['data']:
                    token = data['data']['token']
                    token_head = data['data'].get('tokenHead', 'Bearer').rstrip()
                    full_token = f"{token_head} {token}"
                    
                    # 更新全局token
                    INTRANET_AUTH_TOKEN = full_token
                    
                    logger.info(f"OGE Token刷新成功: {full_token[:50]}...")
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
        logger.info(f"使用OGE服务器token: {INTRANET_AUTH_TOKEN[:50]}...")
        logger.info(f"实际发送headers: {dict((k, v[:50] + '...' if k == 'Authorization' and len(v) > 50 else v) for k, v in headers.items())}")
    
    # 检查是否需要自动重试
    should_auto_retry = (
        use_intranet_token and 
        auto_retry_on_token_expire
    )
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 处理GET请求的参数
            if method.upper() == "GET" and headers and "params" in headers:
                params = headers.pop("params")
                response = await client.request(
                    method=method.upper(),
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

# ============ 环境检查工具 ============

@mcp.tool()
async def check_yaogan_environment(ctx: Context = None) -> str:
    """
    检查遥感大楼环境连通性和服务状态
    
    检查前端、后端、计算集群、MinIO等服务的可访问性
    """
    operation = "检查遥感大楼环境"
    
    try:
        if ctx:
            await ctx.session.send_log_message("info", f"开始执行{operation}...")
        
        logger.info(f"开始执行{operation}")
        
        check_results = {}
        
        # 检查服务列表
        services_to_check = [
            {"name": "OGE前端", "url": f"{OGE_FRONTEND_URL}/health", "type": "frontend"},
            {"name": "计算集群主节点", "url": f"{COMPUTE_CLUSTER_MASTER}/health", "type": "compute"},
            {"name": "Spark Master Web UI", "url": f"{COMPUTE_CLUSTER_MASTER}:9091", "type": "spark"},
            {"name": "Hadoop Web UI", "url": f"{COMPUTE_CLUSTER_MASTER}:8088", "type": "hadoop"},
            {"name": "HBase Web UI", "url": f"{COMPUTE_CLUSTER_MASTER}:16010", "type": "hbase"},
            {"name": "Livy API", "url": f"{LIVY_API_BASE_URL}/sessions", "type": "livy"},
            {"name": "MinIO Web UI", "url": f"{OGE_BACKEND_URL}/login", "type": "minio"},
        ]
        
        for service in services_to_check:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(service["url"])
                    check_results[service["name"]] = {
                        "status": "accessible" if response.status_code < 500 else "error",
                        "status_code": response.status_code,
                        "url": service["url"],
                        "type": service["type"]
                    }
            except Exception as e:
                check_results[service["name"]] = {
                    "status": "unreachable",
                    "error": str(e),
                    "url": service["url"],
                    "type": service["type"]
                }
        
        # 计算健康服务数量
        accessible_count = sum(1 for result in check_results.values() if result["status"] == "accessible")
        total_count = len(check_results)
        
        environment_status = {
            "environment": "遥感大楼",
            "network_segment": "10.101.240.x",
            "accessible_services": accessible_count,
            "total_services": total_count,
            "health_ratio": f"{accessible_count}/{total_count}",
            "service_details": check_results,
            "environment_config": {
                "frontend": OGE_FRONTEND_URL,
                "compute_master": COMPUTE_CLUSTER_MASTER,
                "livy_api": LIVY_API_BASE_URL,
                "minio": OGE_BACKEND_URL
            }
        }
        
        result = Result.succ(
            data=environment_status,
            msg=f"{operation}完成 - {accessible_count}/{total_count} 个服务可访问",
            operation=operation,
            api_endpoint="environment"
        )
        
        if ctx:
            await ctx.session.send_log_message("info", f"{operation}执行完成")
        
        logger.info(f"{operation}执行完成 - 健康服务: {accessible_count}/{total_count}")
        return result.model_dump_json()
        
    except Exception as e:
        logger.error(f"{operation}执行失败: {str(e)}")
        result = Result.failed(
            msg=f"{operation}执行失败: {str(e)}",
            operation=operation
        )
        return result.model_dump_json()

# ============ 工具定义 ============

@mcp.tool()
async def refresh_token(ctx: Context = None) -> str:
    """
    手动刷新遥感大楼环境认证Token
    
    当遇到token过期错误(40003)时，可以使用此工具手动刷新token
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
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "environment": "遥感大楼"
                },
                msg=f"{operation}成功",
                operation=operation,
                api_endpoint="auth"
            )
            
            if ctx:
                await ctx.session.send_log_message("info", f"{operation}成功，新token已更新")
        else:
            result = Result.failed(
                msg=f"{operation}失败: {token_or_error}",
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
            operation=operation
        )
        return result.model_dump_json()

@mcp.tool()
async def check_token_status(ctx: Context = None) -> str:
    """
    检查当前遥感大楼环境认证Token状态
    
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
                "has_double_space": "Bearer  " in INTRANET_AUTH_TOKEN,
                "current_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "bearer_prefix_length": len(INTRANET_AUTH_TOKEN.split(' ')[0]) if ' ' in INTRANET_AUTH_TOKEN else 0,
                "environment": "遥感大楼"
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
                operation=operation,
                api_endpoint="debug"
            )
        else:
            result = Result.failed(
                msg=f"{operation}: 当前没有token",
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
            operation=operation
        )
        return result.model_dump_json()

# 继续添加其他工具函数...
# (为了简洁，这里省略了其他工具函数的完整代码，在实际部署时需要包含所有原有的工具函数)

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
            "environment": "遥感大楼",
            "endpoints": {
                "sse": "/sse",
                "health": "/health",
                "messages": "/messages/"
            }
        })

    async def handle_info(request: Request):
        return JSONResponse({
            "server_name": MCP_SERVER_NAME,
            "environment": "遥感大楼",
            "version": "2.5.0-yaogan",
            "description": "山东耕地流出分析MCP服务器 - 遥感大楼适配版",
            "features": [
                "遥感大楼环境适配",
                "环境连通性检查",
                "自动Token刷新",
                "坡向分析", 
                "山东耕地流出分析",
                "多约束耕地流出分析",
                "大数据查询",
                "DAG批处理工作流",
                "MinIO存储集成"
            ],
            "environment_config": {
                "frontend": OGE_FRONTEND_URL,
                "compute_cluster": COMPUTE_CLUSTER_MASTER,
                "livy_api": LIVY_API_BASE_URL,
                "minio": OGE_BACKEND_URL
            },
            "available_tools": [
                "check_yaogan_environment",
                "refresh_token",
                "check_token_status",
                "coverage_aspect_analysis", 
                "farmland_outflow",
                "run_big_query",
                "execute_code_to_dag",
                "submit_batch_task", 
                "query_task_status",
                "execute_dag_workflow"
            ]
        })

    async def handle_root(request: Request):
        return JSONResponse({
            "server_name": MCP_SERVER_NAME,
            "environment": "遥感大楼",
            "version": "2.5.0-yaogan",
            "status": "running",
            "description": "山东耕地流出分析MCP服务器 - 遥感大楼适配版",
            "endpoints": {
                "/": "服务信息",
                "/health": "健康检查", 
                "/info": "详细信息",
                "/sse": "SSE连接",
                "/messages/": "消息处理"
            },
            "message": "MCP服务器运行正常"
        })

    async def handle_check_environment(request: Request):
        """处理环境检查请求"""
        try:
            # 直接调用环境检查功能，不使用Context
            result = await check_yaogan_environment()
            return JSONResponse({
                "success": True,
                "data": result,
                "message": "环境检查完成"
            })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": str(e),
                "message": "环境检查失败"
            }, status_code=500)

    async def handle_ai_session(request: Request):
        """处理AI会话创建"""
        return JSONResponse({
            "success": True,
            "session_id": f"session_{int(time.time())}",
            "message": "会话创建成功"
        })

    async def handle_layers(request: Request):
        """处理图层获取请求"""
        return JSONResponse({
            "success": True,
            "data": [
                {"id": 1, "name": "底图图层", "type": "base", "visible": True},
                {"id": 2, "name": "卫星影像", "type": "raster", "visible": False},
                {"id": 3, "name": "遥感大楼数据", "type": "vector", "visible": True}
            ],
            "message": "图层数据获取成功"
        })

    return Starlette(
        debug=debug,
        routes=[
            Route("/", endpoint=handle_root),
            Route("/sse", endpoint=handle_sse),
            Route("/health", endpoint=handle_health),
            Route("/info", endpoint=handle_info),
            Route("/check_yaogan_environment", endpoint=handle_check_environment, methods=["GET", "POST"]),
            Route("/ai/session", endpoint=handle_ai_session, methods=["POST"]),
            Route("/layers", endpoint=handle_layers, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

# ============ 主程序 ============

async def run_stdio_server():
    """运行stdio模式的服务器"""
    logger.info("启动遥感大楼MCP服务器 (stdio模式)...")
    
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
    logger.info(f"启动遥感大楼MCP服务器 (HTTP模式) - {host}:{port}")
    
    mcp_server = mcp._mcp_server
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    uvicorn.run(starlette_app, host=host, port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='遥感大楼MCP服务器')
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