# Contributing

Propose changes through a pull request. Explain the observed writing failure, why the existing rule missed or mishandled it, the false-positive boundary, and the regression case that proves the change.

Do not submit generic word bans, scraped private writing, or large third-party phrase dumps. A new rule must be understandable, context-aware, attributable, and testable.

## Plugin blueprint

Keep one writing contract in `skills/nuko-nova-unslop/SKILL.md`. The `unslop` alias routes to it, and `tighten` adds its explicit second pass after the canonical workflow. Supporting references explain the rules in detail. Use [CONTEXT.md](CONTEXT.md) for the domain terms.

The Python helpers separate Markdown recognition from editorial decisions:

| Module | Responsibility |
| --- | --- |
| `markdown_source.py` | Recognize fences, containers, comments, and tables; mask selected spans without changing offsets or line endings. |
| `unslop_lint.py` | Choose which source spans are exempt, then report advisory findings on visible prose. Table prose remains lintable. |
| `preservation_guard.py` | Compare protected source and rewrite content, including code and tables, and report differences for review. |

Keep scanner details inside `markdown_source.py`; test editorial outcomes through `lint_text` and `compare`. Add a synthetic fixture for each non-obvious correction, including nearby prose that must remain visible. The command-line tests also run copied helpers from another directory to verify the installed package can resolve its shared module.

The MCP host embeds the canonical skill directory and serves the same public files. It accepts no user prose. The bundle validator checks the exact shipped file set, and the MCP checks verify that its catalog includes the shared helper. New helper files must pass both checks.

Keep the helpers dependency-free and local. The plugin has no lifecycle hooks. Prefer a shared implementation only when existing callers need the same behavior; keep caller-specific policies with their caller.

## Validation

Run `pnpm install --frozen-lockfile`, then `pnpm check` for the same portable gates used by CI: bundle integrity, Python behavior tests, and MCP tests and type checks. Run the additional client and creator checks in [AGENTS.md](AGENTS.md) before committing.
