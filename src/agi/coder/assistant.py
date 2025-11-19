# src/agi/coder/assistant.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List


Issue = Dict[str, Any]


class CodeAdvice:
    """
    Small helper that turns structured AGI issues into human-readable advice.

    Usage example:

        summary, issues = await run_db_checks()
        messages = CodeAdvice.summarize_issues(issues)
    """

    @staticmethod
    def summarize_issues(issues: Iterable[Issue]) -> List[str]:
        """
        Return a list of short one-line messages (for logs / CLI / chat).
        """
        lines: List[str] = []

        for issue in issues:
            component = issue.get("component", "?")
            kind = str(issue.get("kind", "info")).upper()
            summary = issue.get("summary", "")
            hint = issue.get("hint")

            msg = f"[{component}] {kind}: {summary}"
            if hint:
                msg += f" — Suggested fix: {hint}"

            lines.append(msg)

        if not lines:
            lines.append("No issues detected. AGI diagnostics are all green ✅")

        return lines

    @staticmethod
    def to_markdown(issues: Iterable[Issue]) -> str:
        """
        Render issues as markdown bullets (for admin UI / docs / email).
        """
        md_lines: List[str] = []

        for issue in issues:
            component = issue.get("component", "?")
            kind = str(issue.get("kind", "info")).upper()
            summary = issue.get("summary", "")
            hint = issue.get("hint")
            details = issue.get("details")

            md_lines.append(f"- **[{component}] {kind}** – {summary}")
            if hint:
                md_lines.append(f"  - _Fix_: {hint}")
            if details:
                md_lines.append(f"  - _Details_: `{details}`")

        if not md_lines:
            md_lines.append("- ✅ No issues detected.")

        return "\n".join(md_lines)

    @staticmethod
    def explain_single_issue(issue: Issue) -> str:
        """
        Turn a single issue dict into a friendly explanation paragraph.
        """
        component = issue.get("component", "?")
        kind = str(issue.get("kind", "info")).upper()
        summary = issue.get("summary", "")
        hint = issue.get("hint")
        details = issue.get("details")

        parts: List[str] = [
            f"Component **{component}** reported a **{kind}**:",
            summary or "no summary available.",
        ]

        if hint:
            parts.append(f"Suggested fix: {hint}")

        if details:
            parts.append(f"Raw details: {details}")

        return " ".join(parts)
