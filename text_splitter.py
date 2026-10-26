from pathlib import Path
from document_loader import load_document


def split_documents(documents, chunk_size=1000, overlap=200):
    if chunk_size <= 0:
        raise ValueError("每片长度必须大于0")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("重叠长度必须大于等于0，并且小于每片长度")

    chunks = []

    for document in documents:
        text = document["text"]
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append({
                    "source": document["source"],
                    "page": document["page"],
                    "chunk_index": len(chunks) + 1,
                    "text": chunk_text
                })

            if end == len(text):
                break

            start = end - overlap

    return chunks


if __name__ == "__main__":
    file_path = (
        Path(__file__).parent
        / "knowledge_docs"
        / "ris_signal_processing.pdf"
    )

    documents = load_document(file_path)
    chunks = split_documents(documents)

    print("读取单元数：", len(documents))
    print("切片总数：", len(chunks))

    for chunk in chunks[:3]:
        print("\n切片编号：", chunk["chunk_index"])
        print("来源：", chunk["source"])
        print("页码：", chunk["page"])
        print("字符数：", len(chunk["text"]))
        print("内容预览：", chunk["text"][:150])