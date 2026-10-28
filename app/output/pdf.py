from __future__ import annotations

from app.api.schemas import ResearchResult
from app.output.markdown import render_markdown


class PdfUnavailableError(Exception):
    pass


def render_pdf(result: ResearchResult) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise PdfUnavailableError("fpdf2 is not installed") from exc

    markdown = render_markdown(result)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    width = pdf.epw
    for raw_line in markdown.splitlines():
        line = raw_line.encode("latin-1", "replace").decode("latin-1")
        if line.strip() == "":
            pdf.ln(4)
            continue
        pdf.multi_cell(width, 6, line, wrapmode="CHAR")
    output = pdf.output()
    return bytes(output)
