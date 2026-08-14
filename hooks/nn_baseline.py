#!/usr/bin/env python3
"""Inject and enforce the Nuko Nova Unslop baseline in Codex and Claude Code."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_STYLE = ROOT / "output-styles" / "nuko-nova-unslop.md"
LINTER = ROOT / "skills" / "nuko-nova-unslop" / "scripts" / "unslop_lint.py"
BLOCKING_RULES = {
    "chatbot-artifact",
    "citation-leak",
    "cutoff-disclaimer",
    "dash-cluster",
    "dash-substitute",
}
CODEX_REMINDER = (
    "Apply Nuko Nova Unslop to mutable human-facing prose: be direct, specific, and readable; "
    "use no em dashes or invented facts or voice; preserve facts, quotes, code, fixed text, and earned personality."
)
SUBAGENT_BASELINE = """Nuko Nova Unslop is mandatory for every human-facing sentence you draft or return. Write direct, specific, readable mutable prose without em dashes or spaced double-hyphen substitutes. Preserve supported facts, uncertainty, quotations, citations, code, commands, identifiers, and fixed wording. Keep real judgment, warmth, humor, rhythm, and point of view when the voice is owned or authorized. Never invent a represented person's experience, opinion, emotion, source, metric, commitment, or other detail to make prose sound human. Return prose as reviewable source material, not as an unchecked final."""


def output_style_body() -> str:
    text = OUTPUT_STYLE.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("output style frontmatter is missing")
    return text.split("---\n", 2)[2].strip()


def load_linter() -> ModuleType:
    spec = importlib.util.spec_from_file_location("nuko_nova_unslop_linter", LINTER)
    if spec is None or spec.loader is None:
        raise ImportError("unable to load unslop linter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def emit_context(event: str, context: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": context,
                }
            },
            ensure_ascii=False,
        )
    )


def stop_reason(message: str) -> str | None:
    findings = [
        finding
        for finding in load_linter().lint_text(message, "strict")
        if finding.rule_id in BLOCKING_RULES
    ]
    if not findings:
        return None
    labels = ", ".join(dict.fromkeys(finding.rule_id for finding in findings))
    excerpts = "; ".join(finding.excerpt for finding in findings[:3])
    return (
        f"Nuko Nova Unslop found final-output violations ({labels}): {excerpts}. "
        "Revise the answer once. Remove assistant wrappers or leaked artifacts and replace mutable-prose "
        "em dashes or spaced double hyphens with natural punctuation. Preserve quotations, code, fixed text, "
        "en dash ranges, facts, and the owned voice. Keep earned personality and do not create staccato fragments. "
        "If every flagged span is a quotation, fixed text, protected source wording, or a literal command, deliver it "
        "unchanged instead of rewriting it."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        event = payload.get("hook_event_name")
        if event == "SessionStart":
            emit_context(event, output_style_body())
        # Codex documents PLUGIN_ROOT; Claude Code documents CLAUDE_PLUGIN_ROOT only.
        elif event == "UserPromptSubmit" and "PLUGIN_ROOT" in os.environ:
            emit_context(event, CODEX_REMINDER)
        elif event == "SubagentStart":
            emit_context(event, SUBAGENT_BASELINE)
        elif event == "Stop":
            if payload.get("stop_hook_active"):
                return 0
            message = payload.get("last_assistant_message")
            if not isinstance(message, str) or not message.strip():
                return 0
            reason = stop_reason(message)
            if reason:
                print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
