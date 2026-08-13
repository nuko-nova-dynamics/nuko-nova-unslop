# Nuko Nova Unslop

Nuko Nova Unslop is the default editorial layer for human-facing writing in Codex and Claude Code. While enabled, it applies a direct, specific, readable standard to every response and prose artifact without treating human style as a blacklist or sacrificing facts to sound less artificial.

The plugin combines an always-on writing standard, a context-aware editing skill, and dependency-free checks for surface patterns and protected facts. It supports a balanced default, an explicit strict pass, and a Nuko Nova house profile for product and marketing copy.

## Always-on behavior

- Codex receives a universal skill trigger with implicit invocation explicitly enabled.
- Claude Code receives a forced plugin output style that applies at session start whenever the plugin is enabled, while retaining Claude Code's coding instructions.
- The full skill loads for substantive drafting, rewriting, auditing, file editing, linting, and preservation work.
- Short conversational text follows the standard internally without requiring a linter subprocess.

The standard and the linter are separate. The standard shapes every sentence as it is written. The linter is a local backstop for prose files, multi-paragraph deliverables, and text that will be sent, submitted, published, or reused.

## What it does

- Drafts new prose from supplied facts, audience, channel, and voice.
- Audits observable writing patterns without guessing who or what wrote the text.
- Rewrites with minimum-effective edits and an explicit preservation contract.
- Calibrates to author samples instead of forcing a generic casual voice.
- Protects URLs, numbers, dates, code identifiers, quotations, and other fixed details.
- Runs deterministic local linting without sending prose to another service.
- Reviews upstream writing research every other day through a controlled, test-gated evolution workflow.

## Local use

Run the deterministic checks directly:

```bash
python3 skills/nuko-nova-unslop/scripts/unslop_lint.py --profile balanced draft.md
python3 skills/nuko-nova-unslop/scripts/preservation_guard.py source.md rewrite.md
python3 tests/validate_bundle.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

The linter reports writing signals. It does not classify authorship and does not produce an “AI score.”

The scripts make no network or model calls. On ordinary text, their runtime is normally negligible compared with generating the response; invoking a tool through a client can still add orchestration time.

## Marketplace installation

After the first release is published through the existing `nuko-nova-tools` marketplace:

Codex:

```bash
codex plugin marketplace upgrade nuko-nova-tools
codex plugin add nuko-nova-unslop@nuko-nova-tools
```

Claude Code:

```bash
claude plugin marketplace update nuko-nova-tools
claude plugin install nuko-nova-unslop@nuko-nova-tools --scope user
```

Both clients use `skills/nuko-nova-unslop/SKILL.md`. Claude Code also loads the forced plugin output style so the baseline applies before a substantive writing task explicitly invokes the full skill.

## Controlled evolution

`upstreams.lock.json` records the reviewed commit for every research source. The scheduled workflow checks for new commits every other day and opens a review issue when monitored material changes. It never copies a new word list into the skill or rewrites the prompt automatically.

An evolution pass must inspect the relevant diff, decide whether behavior should change, add or update a regression case, run the package gates, and only then advance the source pin. A valid review can conclude that no plugin change is warranted.

## Source policy

The implementation is an original Nuko Nova synthesis. Permissively licensed projects informed its pattern taxonomy, safety contract, lint architecture, evaluation strategy, and cross-client packaging. Large phrase corpora and third-party tools are not bundled. See `PROVENANCE.md`, `NOTICE`, and the skill's `references/source-map.md` for the exact source roles and reviewed commits.

## Release boundary

The local bundle is not a marketplace release until its repository commit is pushed, tagged, pinned by full SHA in both marketplace manifests, validated there, and installed independently in each client.

After creating a release commit, render aligned immutable catalog entries with:

```bash
python3 scripts/render_marketplace_entries.py \
  --sha <40-character-release-commit> \
  --ref nuko-nova-unslop-marketplace-v0.2.0
```

## License

Apache-2.0
