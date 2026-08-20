# Repository guidance

This repository contains one shared writing skill packaged for Codex and Claude Code.

## Source of truth

- `skills/nuko-nova-unslop/SKILL.md` defines runtime behavior.
- `skills/unslop/SKILL.md` is the short explicit alias and must only route to the canonical skill.
- `output-styles/nuko-nova-unslop.md` makes the standard apply to every Claude Code response while the plugin is enabled.
- `skills/nuko-nova-unslop/agents/openai.yaml` keeps implicit Codex invocation enabled.
- The files under `skills/nuko-nova-unslop/references/` hold detailed rules and maintenance guidance.
- `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` must keep name, version, description, author, repository, and license aligned.
- `upstreams.lock.json` records reviewed upstream state; a new SHA is not accepted until its relevant diff has been reviewed and the package gates pass.
- A recurring owner-created automation may publish only when its prompt explicitly grants the exact Nuko Nova Unslop push, release, marketplace, and client-update actions and every target is reverified during that run.

## Editing contract

- Preserve the skill's fact and voice safeguards when changing pattern rules.
- Keep the zero-em-dash house preference subordinate to quotations and fixed strings, but not to an author sample unless the user explicitly requests em dashes for the current piece. Never satisfy it with spaced double hyphens or staccato fragments.
- Keep personality inside an owned voice; never let an edit donate opinions or experiences to a represented author.
- Treat human writing as purposeful, audience-aware, emotionally proportionate language, not as automatic slang, casualness, quirks, fragments, or deliberate mistakes.
- Apply the no-cringe standard through ownership, proportion, audience fit, and substance. Keep subjective cringe signals contextual and advisory.
- Treat delegated prose as source material and apply the skill in the parent before delivery because client output styles may not propagate to subagents.
- Do not ship lifecycle hooks or any final-output interceptor. The writing skill may advise and lint, but it must never block, rewrite, or delay an answer at a client lifecycle boundary.
- Add a regression fixture for every non-obvious behavioral fix.
- Never turn a context-sensitive signal into proof of AI authorship.
- Never ingest a third-party phrase corpus wholesale. Curate small, explainable rules with false-positive boundaries.
- Keep the skill body concise and route detailed material into one-level references.
- Treat unslopped human-facing prose as the default acceptance criterion, not an optional user-requested pass.
- On authorized automated evolution runs, publish accepted behavioral changes through the full repository, release, marketplace, and client-update sequence. Report a no-op when no justified change exists.

## Required checks

Run these before committing:

```bash
python3 tests/validate_bundle.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 /Users/judiazm/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/nuko-nova-unslop
python3 /Users/judiazm/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/unslop
python3 /Users/judiazm/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Run `claude plugin validate .` when Claude Code is available. Treat package validation, marketplace registration, installation, and client reload as separate states.
