from pathlib import Path

import chromadb


DATABASE_PATH = Path(__file__).resolve().parent / "knowledge_db"


def get_collection():
    client = chromadb.PersistentClient(
        path=str(DATABASE_PATH)
    )

    collection = client.get_or_create_collection(
        name="ris_documents_v1",
        embedding_function=None
    )

    return collection

def list_knowledge_documents():
    collection = get_collection()

    # 只读取切片附带的信息，不读取原文和向量
    result = collection.get(include=["metadatas"])

    documents = {}

    for metadata in result["metadatas"]:
        document_id = metadata["document_id"]

        # 第一次遇到这份文件，先建立一条统计记录
        if document_id not in documents:
            documents[document_id] = {
                "document_id": document_id,
                "source": metadata["source"],
                "chunk_count": 0
            }

        # 每遇到这份文件的一个切片，数量加1
        documents[document_id]["chunk_count"] += 1

    return sorted(
        documents.values(),
        key=lambda item: item["source"].lower()
    )

def delete_knowledge_document(document_id):
    collection = get_collection()

    result = collection.delete(
        where={"document_id": document_id}
    )

    return result["deleted"]

if __name__ == "__main__":
    collection = get_collection()

    print("知识库保存位置：", DATABASE_PATH)
    print("当前切片数量：", collection.count())