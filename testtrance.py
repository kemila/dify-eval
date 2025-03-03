from langfuse import Langfuse
import uuid
import aiohttp
from loguru import logger
import asyncio
from pathlib import Path
from datetime import datetime
import re
import json

# 初始化客户端
langfuse = Langfuse(
    # 云地址 可以上报
    # public_key="pk-lf-e512f725-4653-4c68-9ef6-aea0368cc247",
    # secret_key="sk-lf-62864735-f283-4f9c-aa72-8d72048d8a7f",
    # host="https://us.cloud.langfuse.com" # 或自托管地址

    public_key="pk-lf-fbe70eb3-dff9-416f-9ef7-563c8cf3914f",
    secret_key="sk-lf-6b5e55cf-ccb3-446f-8b9d-399761247aaf",
    host="http://192.168.191.120:3000" # 或自托管地址
)
# ret = asyncio.run(main())
# =================================================
# 接口获取数据太慢 直接先用假数据处理
# 读取文件内容
content = Path('tiaowenwenda.txt').read_text(encoding='utf-8')
# 1 分割 refer 和 返回对象
# 将字符串拆分为多个 JSON 对象
json_objects = []
start = 0
brace_count = 0
for i, char in enumerate(content):
    if char == '{':
        brace_count += 1
    elif char == '}':
        brace_count -= 1
        if brace_count == 0:
            json_objects.append(content[start:i+1])
            start = i+1
# 解析 JSON 对象
refer_obj = json.loads(json_objects[0])
model_obj =  json.loads(json_objects[1])

question = "住宅建筑的安全出口要求?"

# =================================================
# 构造trace 后续用于评分
# 生成唯一 session ID
session_id = str(uuid.uuid4())
user_id = "zhengqi_test"
# 1. 创建 Session（可选）
# Langfuse 无独立 session 概念，可通过 trace 的 metadata 关联
# 或用同一 trace_id 贯穿整个会话

# 2. 创建 Trace（表示完整流程）
trace = langfuse.trace(
    name="standard-chat-trace",
    timestamp=datetime.now(),
    input={"question": question},
    output={"text": model_obj["message"]["content"]},
    user_id=user_id,
    metadata={
        "session_id": session_id,
        "user_id": user_id,
        "app_version": "v1.2.0",
    }
)

# 3. 添加 Observations（具体事件）
# 示例：用户提问
# 定义转换函数
def transform(item):
    return {"metadata": {}, "title": item["bookName"], "content": item["content"]}
trace.span(
    name="knowledge-retrieval",
    input={"question": question},
    output={
        "result": list(map(transform, refer_obj['refer']))
    },
    metadata={}
)

# 示例：AI 响应生成
generation = trace.generation(
    name="ai-response-generation",
    input=question,
    output=model_obj["message"]["content"],
    metadata={"model": model_obj["model"]}
)

# 示例：错误记录
# if error_occurred:
#     trace.event(
#         name="api-error",
#         metadata={"error_code": 500, "message": "Internal server error"}
#     )

# 强制上报（异步模式默认延迟发送）
langfuse.flush()




