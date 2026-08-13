#!/usr/bin/env python3
"""Dependency-free writing-signal linter for Nuko Nova Unslop.

This tool reports explicit patterns and document-shape signals. It does not
classify authorship and intentionally leaves context-sensitive editorial
decisions to the skill.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PROFILE_LEVEL = {"balanced": 1, "strict": 2, "nuko-nova": 3}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    label: str
    pattern: re.Pattern[str]
    suggestion: str
    severity: str = "warning"
    profiles: tuple[str, ...] = ("balanced", "strict", "nuko-nova")


@dataclass(frozen=True)
class Finding:
    rule_id: str
    label: str
    severity: str
    line: int
    column: int
    excerpt: str
    suggestion: str


def rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


RULES = (
    Rule(
        "chatbot-artifact",
        "Chatbot artifact",
        rx(
            r"(?:^|[.!?]\s+)(?:certainly|of course)[!,]"
            r"|\b(?:i hope this helps|would you like me to"
            r"|let me know if you(?:'d| would) like (?:me|us) to"
            r"|here(?:'s| is) (?:the|an?) (?:draft|overview|rewrite))\b"
        ),
        "Remove the assistant-to-user wrapper and begin with the content.",
        "error",
    ),
    Rule(
        "cutoff-disclaimer",
        "Training-cutoff disclaimer",
        rx(r"\bas of my (?:last|latest) (?:training|knowledge) (?:update|cutoff)\b|\bas an ai(?: language)? model\b"),
        "Verify the fact, state what is unknown, or cut the sentence.",
        "error",
    ),
    Rule(
        "reasoning-artifact",
        "Reasoning artifact",
        rx(r"\b(?:let(?:'s| us) think (?:step by step|this through)|i need to (?:analyze|reason|consider)|my reasoning is)\b"),
        "Keep the conclusion or action, not hidden-process narration.",
        "error",
    ),
    Rule(
        "citation-leak",
        "Citation markup leak",
        rx(r"(?:oaicite|contentReference|turn\d+(?:search|view|fetch)\d+|\ue200cite\ue202)"),
        "Repair the citation from its source or remove the broken marker.",
        "error",
    ),
    Rule(
        "placeholder-leak",
        "Unfilled placeholder",
        rx(r"\[(?:your name|insert (?:statistic|citation|detail|text)|todo(?::[^\]]*)?)\]|\b(?:TODO|TBD|FIXME)\b"),
        "Fill this from supplied material or mark the unresolved gap explicitly.",
        "error",
    ),
    Rule(
        "significance-inflation",
        "Significance inflation",
        rx(r"\b(?:pivotal moment|testament to|plays? (?:a )?(?:vital|crucial|key) role|marks? (?:a )?(?:major|significant|historic) shift|indelible mark|setting the stage for)\b"),
        "State what happened and give a supported consequence.",
    ),
    Rule(
        "promotional-fog",
        "Promotional fog",
        rx(r"\b(?:groundbreaking|game[ -]?chang(?:er|ing)|world[ -]?class|best[ -]?in[ -]?class|cutting[ -]?edge|breathtaking|must[ -]?visit|vibrant tapestry)\b"),
        "Replace the label with a supported feature, result, or constraint.",
    ),
    Rule(
        "vague-authority",
        "Vague authority",
        rx(r"\b(?:experts (?:say|agree|believe|argue)|studies (?:show|indicate|suggest)|research (?:shows|indicates|suggests)|industry (?:reports|observers) (?:say|suggest|note)|some critics argue)\b"),
        "Name a verified source or remove the appeal to authority.",
    ),
    Rule(
        "negative-reframe",
        "Negative reframe",
        rx(r"\b(?:it(?:'s| is) not (?:just |only )?[^.!?;]{2,90}[,;:]\s*(?:it(?:'s| is) |but )|not [^.!?]{2,55}\.\s*not [^.!?]{2,55}\.\s*(?:just |only )|not only\b[^.!?]{2,100}\bbut also\b)"),
        "State the positive claim directly unless the contrast carries real information.",
    ),
    Rule(
        "fake-insider",
        "Fake-insider setup",
        rx(r"\b(?:here(?:'s| is) (?:the thing|what nobody tells you|the uncomfortable truth)|what most people (?:miss|get wrong)|the part (?:everyone|most people) (?:misses|skips))\b"),
        "Remove the setup and let the claim stand on evidence.",
    ),
    Rule(
        "signposting",
        "Signposting announcement",
        rx(r"\b(?:let(?:'s| us) (?:dive in|dive into|explore|break this down|unpack)|without further ado|here(?:'s| is) what you need to know)\b"),
        "Begin with the substance.",
    ),
    Rule(
        "superficial-ing",
        "Superficial -ing clause",
        rx(r",\s*(?:highlighting|underscoring|showcasing|symbolizing|reflecting|emphasizing|demonstrating|ensuring|fostering)\b[^.!?]{3,120}"),
        "Delete the clause or state a supported mechanism or consequence.",
    ),
    Rule(
        "abstract-outcome",
        "Abstract outcome",
        rx(r"\b(?:unlock (?:value|potential|insights?|opportunities)|elevate (?:the |your )?(?:experience|workflow|brand)|transform (?:the |your )?(?:workflow|business|experience)|drive (?:meaningful )?(?:impact|value|innovation)|navigate the complexities)\b"),
        "Name what changes, for whom, and by what mechanism.",
    ),
    Rule(
        "corporate-therapist",
        "Corporate therapist voice",
        rx(r"\b(?:lean into (?:our|your|the) strengths|foster (?:a culture of )?(?:alignment|accountability|collaboration)|create space for|meet (?:people|teams) where they are)\b"),
        "Name the action, owner, behavior, or decision.",
    ),
    Rule(
        "hedging-filler",
        "Importance announcement",
        rx(r"\bit(?:'s| is) (?:worth noting|important to (?:note|remember|understand)) that\b"),
        "State the point directly and delete the announcement that it matters.",
    ),
    Rule(
        "interpretive-label",
        "Opinion-free connector",
        rx(r"\bthis (?:underscores|speaks to)\b|\bthis (?:signals|highlights) (?:that|the (?:need|importance|shift))\b"),
        "State the judgment, trade-off, or consequence directly instead of a neutral connector.",
        "info",
        profiles=("strict", "nuko-nova"),
    ),
    Rule(
        "dash-substitute",
        "Spaced double-hyphen substitute",
        rx(r"(?<=\S)\s--\s(?=\S)"),
        "Restructure the sentence instead of substituting two hyphens for an em dash.",
        profiles=("strict", "nuko-nova"),
    ),
    Rule(
        "generic-conclusion",
        "Generic conclusion",
        rx(r"\b(?:in conclusion|to sum up|at the end of the day|the future looks bright|exciting times lie ahead|only time will tell|this represents? (?:a )?(?:major|significant) step (?:in the right direction|forward))\b"),
        "End on a concrete fact, consequence, decision, or next action.",
    ),
    Rule(
        "transition-stack",
        "Formulaic transition",
        rx(r"^(?:Additionally|Moreover|Furthermore|Importantly|That said|With that said),"),
        "Connect the ideas directly; repeated announcement transitions flatten the rhythm.",
        profiles=("strict", "nuko-nova"),
    ),
    Rule(
        "watched-vocabulary",
        "Contextual AI-coded vocabulary",
        rx(r"\b(?:delve|tapestry|testament|multifaceted|ever-changing landscape|seamless|streamline|leverage|utilize|robust|empower|supercharge)\b"),
        "Check whether a plainer, more exact word fits; preserve valid technical or authorial use.",
        "info",
        profiles=("strict", "nuko-nova"),
    ),
    Rule(
        "via-negativa",
        "Via-negativa value proposition",
        rx(r"(?:^|[.!?]\s+)(?:No|Without)\s+(?:surprises|fluff|filler|guessing|guesswork|scope creep|hidden fees|fees|fuss|prep|hassle|headaches|shortcuts|templates)\b"),
        "Describe what the reader receives or how the process works.",
        profiles=("nuko-nova",),
    ),
    Rule(
        "collaborative-cta",
        "Generic collaborative call to action",
        rx(r"\bLet(?:'s| us) (?:build something|create something|get started|work together|make it happen)(?: together)?\b"),
        "Use the specific next action, such as applying, booking, or starting the project.",
        profiles=("nuko-nova",),
    ),
)


FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
LINK_TARGET_RE = re.compile(r"(?<=\]\()[^)]+(?=\))")
URL_RE = re.compile(r"https?://[^\s)>]+")
QUOTED_SPAN_RE = re.compile(r'"[^"\n]*"|“[^”\n]*”')


def mask_exempt_spans(text: str) -> str:
    chars = list(text)
    for pattern in (FENCE_RE, INLINE_CODE_RE, LINK_TARGET_RE, URL_RE, QUOTED_SPAN_RE):
        for match in pattern.finditer(text):
            for index in range(match.start(), match.end()):
                if chars[index] != "\n":
                    chars[index] = " "
    return "".join(chars)


def position(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    previous = text.rfind("\n", 0, offset)
    column = offset + 1 if previous < 0 else offset - previous
    return line, column


def excerpt(text: str, start: int, end: int, width: int = 120) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end < 0:
        line_end = len(text)
    value = re.sub(r"\s+", " ", text[line_start:line_end]).strip()
    if len(value) <= width:
        return value
    return value[: width - 1].rstrip() + "…"


def phrase_findings(text: str, masked: str, profile: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        if profile not in rule.profiles:
            continue
        for match in rule.pattern.finditer(masked):
            line, column = position(text, match.start())
            findings.append(
                Finding(
                    rule.rule_id,
                    rule.label,
                    rule.severity,
                    line,
                    column,
                    excerpt(text, match.start(), match.end()),
                    rule.suggestion,
                )
            )
    return findings


STRUCTURAL_DASH_PREFIX_RE = re.compile(
    r"^\s*(?:"
    r"[-*+]\s+(?:\*\*[^*\n]{1,50}\*\*|`[^`\n]{1,50}`)"
    r"|#{1,6}\s+(?:\[[^\]\n]{1,50}\]|v?\d+(?:\.\d+){1,3})"
    r")\s*$"
)


def balanced_structural_dash_offsets(masked: str, offsets: list[int]) -> set[int]:
    """Exclude label separators from balanced rhythm counts, not strict house checks."""
    exempt: set[int] = set()
    for offset in offsets:
        line_start = masked.rfind("\n", 0, offset) + 1
        if STRUCTURAL_DASH_PREFIX_RE.match(masked[line_start:offset]):
            exempt.add(offset)
    return exempt


def dash_finding(text: str, masked: str, profile: str) -> Finding | None:
    offsets = [match.start() for match in re.finditer("—", masked)]
    if profile == "balanced":
        offsets = sorted(set(offsets) - balanced_structural_dash_offsets(masked, offsets))
    words = max(1, len(re.findall(r"\b[\w’'-]+\b", masked)))
    if not offsets:
        return None
    threshold = 4 if profile == "balanced" else 1
    density = len(offsets) * 500 / words
    if profile == "balanced" and (len(offsets) < threshold or density < threshold):
        return None
    if profile != "balanced" and len(offsets) < threshold:
        return None
    line, column = position(text, offsets[0])
    return Finding(
        "dash-cluster",
        "Em-dash cluster" if len(offsets) > 1 else "Em dash in new prose",
        "info" if profile == "balanced" else "warning",
        line,
        column,
        excerpt(text, offsets[0], offsets[0] + 1),
        f"Review {len(offsets)} em dash(es); restructure mutable prose with a comma, colon, parentheses, "
        "or a separate sentence rather than staccato fragments. Preserve quotations, fixed strings, and "
        "valid en-dash ranges.",
    )


SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?](?=\s|$)")
LIST_ITEM_RE = re.compile(r"\s*(?:[-*+]|\d+[.)])\s")


def rhythm_findings(text: str, masked: str) -> list[Finding]:
    sentences: list[tuple[int, int, bool]] = []
    for match in SENTENCE_RE.finditer(masked):
        count = len(re.findall(r"\b[\w’'-]+\b", match.group()))
        if count:
            line_start = masked.rfind("\n", 0, match.start()) + 1
            in_list = bool(LIST_ITEM_RE.match(masked, line_start))
            sentences.append((match.start(), count, in_list))
    findings: list[Finding] = []

    for index in range(len(sentences) - 2):
        window = sentences[index : index + 3]
        if all(count <= 4 and not in_list for _, count, in_list in window):
            start = window[0][0]
            line, column = position(text, start)
            findings.append(
                Finding(
                    "staccato-drama",
                    "Stacked short sentences",
                    "warning",
                    line,
                    column,
                    excerpt(text, start, sentences[index + 2][0] + 40),
                    "Join related thoughts unless each short sentence earns its emphasis.",
                )
            )
            break

    lengths = [count for _, count, _ in sentences]
    if len(lengths) >= 8:
        mean = sum(lengths) / len(lengths)
        variance = sum((value - mean) ** 2 for value in lengths) / len(lengths)
        coefficient = math.sqrt(variance) / mean if mean else 0
        if 10 <= mean <= 26 and coefficient < 0.20:
            line, column = position(text, sentences[0][0])
            findings.append(
                Finding(
                    "uniform-rhythm",
                    "Uniform sentence rhythm",
                    "info",
                    line,
                    column,
                    excerpt(text, sentences[0][0], sentences[0][0] + 80),
                    "Check whether repeated sentence length and shape make the prose feel assembled.",
                )
            )
    return findings


def lint_text(text: str, profile: str = "balanced") -> list[Finding]:
    if profile not in PROFILE_LEVEL:
        raise ValueError(f"unknown profile: {profile}")
    # Curly apostrophes are normal typography; match phrases through them
    # without shifting offsets.
    masked = mask_exempt_spans(text).replace("’", "'").replace("‘", "'")
    findings = phrase_findings(text, masked, profile)
    dash = dash_finding(text, masked, profile)
    if dash:
        findings.append(dash)
    findings.extend(rhythm_findings(text, masked))
    return sorted(findings, key=lambda item: (item.line, item.column, item.rule_id))


def iter_inputs(paths: list[str]) -> Iterable[tuple[str, str]]:
    if not paths:
        yield "<stdin>", sys.stdin.read()
        return
    for raw in paths:
        path = Path(raw)
        yield str(path), path.read_text(encoding="utf-8")


def render_text(source: str, findings: list[Finding]) -> str:
    if not findings:
        return f"{source}: no deterministic writing signals found"
    lines = [f"{source}: {len(findings)} writing signal(s)"]
    for item in findings:
        lines.append(
            f"{source}:{item.line}:{item.column}: {item.severity} "
            f"[{item.rule_id}] {item.label}: {item.excerpt}\n"
            f"  {item.suggestion}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report anti-slop writing signals without classifying authorship."
    )
    parser.add_argument("paths", nargs="*", help="UTF-8 text or Markdown files; reads stdin when omitted")
    parser.add_argument("--profile", choices=sorted(PROFILE_LEVEL), default="balanced")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)

    records = []
    total = 0
    for source, content in iter_inputs(args.paths):
        findings = lint_text(content, args.profile)
        total += len(findings)
        if args.format == "json":
            records.append({"source": source, "profile": args.profile, "findings": [asdict(item) for item in findings]})
        else:
            print(render_text(source, findings))
    if args.format == "json":
        print(json.dumps(records, indent=2, ensure_ascii=False))
    return 1 if args.fail_on_findings and total else 0


if __name__ == "__main__":
    raise SystemExit(main())
