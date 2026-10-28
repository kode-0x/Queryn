from __future__ import annotations

from app.api.schemas import ResearchResult

_MOCK_BANNER = (
    "> **Simulated sources.** The attributions below are deterministic mock "
    "results labeled `[SIMULATED SOURCE]` with `mock://` URIs. They are not real "
    "research and must not be presented as such."
)


def render_markdown(result: ResearchResult) -> str:
    lines: list[str] = [result.report.rstrip(), "", "## Attributions", ""]
    if any(source.mock for source in result.sources):
        lines.append(_MOCK_BANNER)
        lines.append("")
    if not result.sources:
        lines.append("_No sources attributed._")
    for source in result.sources:
        label = " [SIMULATED SOURCE]" if source.mock else ""
        lines.append(f"- `{source.id}`{label} [{source.title}]({source.uri})")
        if source.snippet:
            lines.append(f"  - {source.snippet}")
    return "\n".join(lines).rstrip() + "\n"
