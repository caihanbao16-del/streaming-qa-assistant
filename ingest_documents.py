import asyncio
import hashlib
from pathlib import Path

from document_loader import load_document
from text_splitter import split_documents
from embedding_service import embed_texts
from knowledge_store import get_collection


async def ingest_document(file_path, source_name=None):
    file_path = Path(file_path)

    documents = await asyncio.to_thread(load_document, file_path)

    if source_name is not None:
        for document in documents:
            document["source"] = source_name

    chunks = await asyncio.to_thread(split_documents, documents)

    if not chunks:
        raise ValueError("文件中没有可以入库的文字")

    # 根据文件内容生成标识，同一份文件得到相同标识
    document_id = hashlib.sha256(
        file_path.read_bytes()
    ).hexdigest()

    collection = get_collection()

    # 每批处理10个切片
    for start in range(0, len(chunks), 10):
        batch = chunks[start:start + 10]
        texts = [chunk["text"] for chunk in batch]

        vectors = await embed_texts(texts)

        if len(vectors) != len(batch):
            raise RuntimeError("返回的向量数量与切片数量不一致")

        ids = []
        metadatas = []

        for chunk in batch:
            ids.append(
                f"{document_id}:{chunk['chunk_index']}"
            )

            metadata = {
                "document_id": document_id,
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"]
            }

            # TXT 没有页码，只有存在页码时才保存这个字段
            if chunk["page"] is not None:
                metadata["page"] = chunk["page"]

            metadatas.append(metadata)

        await asyncio.to_thread(
            collection.upsert,
            ids=ids,
            documents=texts,
            embeddings=vectors,
            metadatas=metadatas
        )

        print(f"已入库：{start + len(batch)}/{len(chunks)}")

    print("当前知识库切片总数：", collection.count())

    return {
        "document_id": document_id,
        "source": source_name or file_path.name,
        "chunk_count": len(chunks)
    }


if __name__ == "__main__":
    file_path = (
        Path(__file__).resolve().parent
        / "knowledge_docs"
        / "ris_signal_processing.pdf"
    )

    asyncio.run(ingest_document(file_path))