from __future__ import annotations

from app.api.schemas import ResearchResult
from app.output.json_out import render_json
from app.output.markdown import render_markdown
from app.output.pdf import render_pdf


class PdfDisabledError(Exception):
    pass


def render_report(result: ResearchResult, pdf_enabled: bool) -> str:
    if result.output_format == "json":
        return render_json(result)
    if result.output_format == "pdf":
        raise PdfDisabledError("pdf output requires rendering to bytes")
    return render_markdown(result)


def render_pdf_bytes(result: ResearchResult, pdf_enabled: bool) -> bytes:
    if not pdf_enabled:
        raise PdfDisabledError("pdf output is disabled in this deployment")
    return render_pdf(result)
