# extract_text.py
from pathlib import Path
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document

def extract_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text(path):
    """
    Returns extracted text for .pdf, .docx/.doc, .txt
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    suffix = p.suffix.lower()
    if suffix == '.pdf':
        # pdfminer returns a string
        return extract_pdf_text(str(p))
    elif suffix in ('.docx', '.doc'):
        return extract_docx(str(p))
    else:
        return p.read_text(encoding='utf-8', errors='ignore')

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extract_text.py path/to/resume.pdf")
        sys.exit(1)
    path = sys.argv[1]
    txt = extract_text(path)
    print("----EXTRACTED TEXT START----")
    print(txt[:2000])
    print("----EXTRACTED TEXT END----")
