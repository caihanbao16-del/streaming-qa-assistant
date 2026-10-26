import asyncio
import os

import httpx


async def embed_texts(texts):
    if not 1 <= len(texts) <= 10:
        raise ValueError("每次需要传入1到10段文字")

    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise RuntimeError("没有设置 DASHSCOPE_API_KEY")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "text-embedding-v4",
                "input": texts,
                "dimensions": 1024,
                "encoding_format": "float"
            }
        )

        response.raise_for_status()
        result = response.json()

    items = sorted(result["data"], key=lambda item: item["index"])

    vectors = [item["embedding"] for item in items]
    return vectors


async def main():
    texts = [
        "RIS 可以通过调节反射单元改变无线信号的传播。",
        "智能反射表面能够辅助改善无线通信覆盖。"
    ]

    vectors = await embed_texts(texts)

    print("输入文字数量：", len(texts))
    print("返回向量数量：", len(vectors))
    print("第一个向量的维度：", len(vectors[0]))
    print("第一个向量的前5个数字：", vectors[0][:5])


if __name__ == "__main__":
    asyncio.run(main())