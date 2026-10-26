import os
import httpx
import json

async def generate_answer(question):
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise RuntimeError("没有设置 DASHSCOPE_API_KEY")

    # 创建异步 HTTP 客户端，退出代码块时自动关闭
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": "qwen-flash",
                "messages": [
                    {
                        "role": "system",
                        "content": "请用中文简洁回答用户的问题。",
                    },
                    {
                        "role": "user",
                        "content": question,
                    },
                ],
                "enable_thinking": False,
                "max_tokens": 500,
            },
        )

        response.raise_for_status()
        result = response.json()

    return result["choices"][0]["message"]["content"]

async def generate_answer_stream(
        question,
        system_prompt="请用中文简洁回答用户的问题。"
):
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise RuntimeError("没有设置 DASHSCOPE_API_KEY")

    # 先占位，避免请求尚未建立就出错时，变量不存在
    client = None
    response = None

    print("[模型连接] 开始请求百炼", flush=True)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": "qwen-flash",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": question,
                        },
                    ],
                    "enable_thinking": False,
                    "max_tokens": 500,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()

                print("[模型连接] 已收到响应，开始读取", flush=True)

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue

                    data_text = line[5:].strip()

                    if data_text == "[DONE]":
                        break

                    if not data_text:
                        continue

                    chunk = json.loads(data_text)

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    text = choices[0].get("delta", {}).get("content")

                    if text:
                        yield text

    finally:
        print("[模型连接] 进入最终检查", flush=True)

        if response is not None:
            print(
                "[模型连接] response.is_closed =",
                response.is_closed,
                flush=True,
            )
        else:
            print("[模型连接] 尚未取得响应对象", flush=True)

        if client is not None:
            print(
                "[模型连接] client.is_closed =",
                client.is_closed,
                flush=True,
            )