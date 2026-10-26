from pathlib import Path
from pypdf import PdfReader


def load_pdf_pages(file_path):
    file_path = Path(file_path)
    reader = PdfReader(file_path)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append({
            "source": file_path.name,
            "page": page_number,
            "text": text
        })

    return pages

def load_txt(file_path):
    file_path = Path(file_path)
    text = file_path.read_text(encoding="utf-8-sig")

    return [{
        "source": file_path.name,
        "page": None,
        "text": text
    }]


def load_document(file_path):
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf_pages(file_path)

    if suffix == ".txt":
        return load_txt(file_path)

    raise ValueError("目前只支持 PDF 和 TXT 文件")

if __name__ == "__main__":
    pdf_path = (
        Path(__file__).parent
        / "knowledge_docs"
        / "ris_signal_processing.pdf"
    )

    pages = load_document(pdf_path)

    print("总页数：", len(pages))
    print("文件名：", pages[0]["source"])
    print("第一页文字预览：")
    print(pages[0]["text"][:500])