import asyncio

from embedding_service import embed_texts
from knowledge_store import get_collection


async def retrieve_documents(question, top_k=3):
    question = question.strip()

    if not question:
        raise ValueError("问题不能为空")

    if top_k <= 0:
        raise ValueError("检索数量必须大于0")

    collection = await asyncio.to_thread(get_collection)
    count = await asyncio.to_thread(collection.count)

    if count == 0:
        return []

    # 一个问题对应一个向量
    question_vectors = await embed_texts([question])

    result = await asyncio.to_thread(
        collection.query,
        query_embeddings=question_vectors,
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"]
    )

    records = []

    # 当前只查询了一个问题，所以取第0组结果
    texts = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    for text, metadata, distance in zip(
        texts, metadatas, distances
    ):
        records.append({
            "text": text,
            "source": metadata["source"],
            "page": metadata.get("page"),
            "distance": distance
        })

    return records


async def main():
    question = "RIS 如何改善无线通信覆盖？"
    records = await retrieve_documents(question, top_k=3)

    print("问题：", question)
    print("检索结果数量：", len(records))

    if not records:
        print("知识库为空，请先导入资料。")
        return

    for number, record in enumerate(records, start=1):
        print(f"\n—— 第{number}个片段 ——")
        print("来源：", record["source"])
        print("页码：", record["page"])
        print("距离：", round(record["distance"], 4))
        print("正文：")
        print(record["text"])


if __name__ == "__main__":
    asyncio.run(main())