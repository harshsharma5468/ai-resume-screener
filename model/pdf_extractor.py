import io
import pdfplumber


def extract_text_from_pdf(file) -> str:
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_text_from_bytes(file_bytes: bytes) -> str:
    return extract_text_from_pdf(io.BytesIO(file_bytes))
