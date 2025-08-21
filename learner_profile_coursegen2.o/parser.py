import fitz  # PyMuPDF
import docx

def parse_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def parse_docx(uploaded_file):
    doc = docx.Document(uploaded_file)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return parse_pdf(uploaded_file)
    elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        return parse_docx(uploaded_file)
    else:
        raise Exception(f"Unsupported file type: {uploaded_file.type}")
