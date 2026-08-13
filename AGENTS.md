# Repository guidance

This repository contains one shared writing skill packaged for Codex and Claude Code.

## Source of truth

- `skills/nuko-nova-unslop/SKILL.md` defines runtime behavior.
- `output-styles/nuko-nova-unslop.md` makes the standard apply to every Claude Code response while the plugin is enabled.
- `skills/nuko-nova-unslop/agents/openai.yaml` keeps implicit Codex invocation enabled.
- The files under `skills/nuko-nova-unslop/references/` hold detailed rules and maintenance guidance.
- `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` must keep name, version, description, author, repository, and license aligned.
- `upstreams.lock.json` records reviewed upstream state; a new SHA is not accepted until its relevant diff has been reviewed and the package gates pass.

## Editing contract

- Preserve the skill's fact and voice safeguards when changing pattern rules.
- Add a regression fixture for every non-obvious behavioral fix.
- Never turn a context-sensitive signal into proof of AI authorship.
- Never ingest a third-party phrase corpus wholesale. Curate small, explainable rules with false-positive boundaries.
- Keep the skill body concise and route detailed material into one-level references.
- Treat unslopped human-facing prose as the default acceptance criterion, not an optional user-requested pass.

## Required checks

Run these before committing:

```bash
python3 tests/validate_bundle.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 /Users/judiazm/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/nuko-nova-unslop
python3 /Users/judiazm/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Run `claude plugin validate .` when Claude Code is available. Treat package validation, marketplace registration, installation, and client reload as separate states.
