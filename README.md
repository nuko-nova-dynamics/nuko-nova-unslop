# Nuko Nova Unslop

Nuko Nova Unslop provides the human-writing standard for Codex, Claude Code, and ChatGPT. It helps make responses and prose artifacts direct, specific, natural, and appropriate to their writer and reader, without treating human style as a blacklist or sacrificing facts to sound less artificial.

The plugin combines a default writing standard, a context-aware editing skill, a forced Claude Code output style, and dependency-free checks for surface patterns and protected facts. It supports a balanced default, an explicit strict pass, and a Nuko Nova house profile for product and marketing copy.

Original marketplace artwork is packaged in `assets/icon.png`, `assets/logo.png`, and `assets/logo-dark.png`. The light and dark versions use the same writing-page and nova mark so the plugin remains recognizable across client surfaces.

## Runtime behavior

- Codex exposes the skill for implicit invocation on human-facing writing tasks.
- Claude Code keeps the forced plugin output style for its main conversation.
- The full skill loads for substantive drafting, rewriting, auditing, file editing, linting, and preservation work.
- Delegated prose returns to the parent as reviewable source material under the skill contract.
- The plugin ships no lifecycle hooks and never intercepts, blocks, rewrites, or delays a final answer.
- ChatGPT can load the same skill package from a public, read-only MCP server. ChatGPT still writes the answer itself.

## Short invocation

Use the same word on every client:

- ChatGPT: `@Unslop`
- Codex: type `$unslop` and select Unslop
- Claude Code: `/unslop`

The clients use different prefix characters, but `unslop` is the shared trigger. Automatic writing guidance remains active; the short command is available when you want to invoke it explicitly.

The standard and the linter are separate. The standard shapes prose when the skill or output style is active. The linter runs only when invoked for a writing task or file. It does not scan final conversational output automatically. Use it for prose files, multi-paragraph deliverables, and text that will be sent, submitted, published, or reused.

## What it does

- Drafts and rewrites mutable prose from supplied facts, audience, channel, and voice, with zero em dashes or spaced double-hyphen substitutes and flowing constructions instead of staccato fragments.
- Applies an explicit no-cringe test based on voice ownership, emotional proportion, audience relationship, and substance.
- Rejects fake intimacy, forced cleverness, canned vulnerability, motivational uplift, theatrical reveals, borrowed slang, and unsupported quirks while preserving personality the voice has earned.
- Audits observable writing patterns and explains their effects.
- Allows real judgment, warmth, humor, and point of view only in an owned voice: the actual author, the assistant as itself, an approved brand voice, or an authorized genre.
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

The linter reports writing signals for editorial review.

The scripts make no network or model calls. They run only when invoked and never block a client response.

## ChatGPT web plugin

The Cloudflare Worker in `apps/mcp` gives ChatGPT a small read-only doorway to the existing skill package. It does not run a model, rewrite text, or accept prose to process.

When the user invokes `@Unslop`, ChatGPT calls `load_nuko_nova_unslop` with an empty object. The tool returns `SKILL.md`, its version, its source commit, and the names of its supporting references. ChatGPT reads those instructions and writes the response itself. If the skill routes to a supporting file, ChatGPT can request that file by its fixed package name.

The server also implements OpenAI's MCP skill-import extension:

- `skills/list` returns the complete catalog entry and SHA-256 digest for every packaged file.
- `skills/get` returns the exact catalog entry for Nuko Nova Unslop.
- `resources/read` returns each declared package file by its `skill://` URI.

Only files inside `skills/nuko-nova-unslop` are embedded. Transcripts, interaction-learning evidence, local paths, credentials, and private automation data are outside the package boundary. The loader has no prose argument. The reference reader accepts one package filename and has no rewrite field.

Run the MCP checks locally:

```bash
pnpm install --frozen-lockfile
pnpm mcp:check
pnpm mcp:dev
```

The public ChatGPT connection uses the Worker's `/mcp` URL with no authentication because it serves the same public package already present in this repository. A formal Plugin Directory submission imports a reviewed snapshot. After the skill changes, scan the MCP server again and submit a new plugin version so ChatGPT imports the new snapshot.

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

Both clients use `skills/nuko-nova-unslop/SKILL.md`. Claude Code also loads the forced plugin output style. Neither client receives lifecycle hooks or a final-output blocker from this plugin.

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
  --ref nuko-nova-unslop-marketplace-v0.6.7
```

## License

Apache-2.0
