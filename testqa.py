import aiohttp
from loguru import logger
import asyncio

# =================================================
# 发送问题获取refer与answer
async def test_send_chat_message(question):
    chat_url = f"https://101.40.75.167/standard_qa_symbol/api/standardChat"
    api_key = "acdd8742fba944968b58f276c5cb8a0a"
    headers = {"Token": f"{api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-r1:70b",
        "question": question,
        "stream": False,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(chat_url, headers=headers, json=payload, ssl=False) as response:
            # ret = await response.json()
            ret = await response.text()
            with open("tiaowenwenda.txt", "w", encoding="utf-8") as file:
              file.write(ret)
            return ret
        
question = "托儿所、老年人、残疾人专用住宅的居室要求获得冬至日满窗日照不少于多少h？"
aiResponse = ''

async def my_task():
    ret = await test_send_chat_message(question)
    logger.info(f"Ret111: {ret} ")
    return ret

async def main():
    try:
        # 设置超时时间
        result = await asyncio.wait_for(my_task(), timeout=30000)
        print(result)
    except asyncio.TimeoutError:
        print("任务超时")
ret = asyncio.run(main())


