#!/usr/bin/env python3
"""
遥感大楼环境配置文件
用于配置MCP服务器适配遥感大楼的网络环境
"""

# ============ 遥感大楼环境配置 ============

# 基础网络配置
YAOGAN_NETWORK_SEGMENT = "10.101.240"

# 核心服务地址
OGE_FRONTEND_URL = "http://10.101.240.20"  # 前端地址
OGE_BACKEND_URL = "http://10.101.240.20"   # 后端地址（通过前端代理）
COMPUTE_CLUSTER_MASTER = "http://10.101.240.10"  # 计算集群主节点(ogecal0)

# API端点配置
OGE_API_BASE_URL = f"{OGE_BACKEND_URL}/gateway/computation-api/process"
INTRANET_API_BASE_URL = f"{OGE_BACKEND_URL}/api/computation/process"
DAG_API_BASE_URL = f"{COMPUTE_CLUSTER_MASTER}:8998/api/oge-dag"  # 基于Livy端口

# 认证配置
DEFAULT_USERNAME = "oge_admin"
DEFAULT_USER_ID = "yaogan-building-user"
AUTH_API_URL = f"{OGE_BACKEND_URL}/api/oauth/token"

# 大数据组件配置
SPARK_MASTER_UI = f"{COMPUTE_CLUSTER_MASTER}:9091"  # Spark Master Web UI
HADOOP_UI = f"{COMPUTE_CLUSTER_MASTER}:8088"        # Hadoop Web UI  
HBASE_UI = f"{COMPUTE_CLUSTER_MASTER}:16010"        # HBase Web UI
LIVY_API_URL = f"{COMPUTE_CLUSTER_MASTER}:8998"     # Livy API
ZOOKEEPER_UI = f"{COMPUTE_CLUSTER_MASTER}:2181"     # Zookeeper

# MinIO存储配置
MINIO_ENDPOINT = "http://10.101.240.23:9007"
MINIO_ACCESS_KEY = "oge"
MINIO_SECRET_KEY = "ypfamily608"

# 文件系统路径配置
NFS_SHARED_STORAGE = "/mnt/storage"  # ogecal0上的共享存储
HADOOP_DATA_DIR = "/mnt/hadoop_data"
ZOOKEEPER_DATA_DIR = "/mnt/zookeeper-3.4.13/data/"
DAG_BOOT_DIR = "/mnt/storage/dag-boot"

# 服务健康检查端点
HEALTH_CHECK_ENDPOINTS = {
    "frontend": f"{OGE_FRONTEND_URL}/health",
    "spark": f"{SPARK_MASTER_UI}",
    "hadoop": f"{HADOOP_UI}",
    "hbase": f"{HBASE_UI}", 
    "livy": f"{LIVY_API_URL}/sessions",
    "minio": f"{MINIO_ENDPOINT}/login",
    "compute_master": f"{COMPUTE_CLUSTER_MASTER}/health"
}

# 环境特性
ENVIRONMENT_FEATURES = [
    "Spark集群 (3.0.0)",
    "Hadoop集群 (2.7.3)", 
    "HBase集群 (1.4.13)",
    "Zookeeper集群 (3.4.13)",
    "Livy Spark作业提交",
    "NFS共享存储",
    "MinIO对象存储"
]

def get_config_summary():
    """获取配置摘要信息"""
    return {
        "environment": "遥感大楼",
        "network_segment": YAOGAN_NETWORK_SEGMENT + ".x",
        "frontend_url": OGE_FRONTEND_URL,
        "compute_master": COMPUTE_CLUSTER_MASTER,
        "minio": MINIO_ENDPOINT,
        "features": ENVIRONMENT_FEATURES
    } 