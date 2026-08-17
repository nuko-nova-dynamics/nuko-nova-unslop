# Source map

Research cutoff: August 13, 2026. `upstreams.lock.json` is the machine-readable source of reviewed commit pins and monitored paths.

| Source | Reviewed commit | License | What it contributed |
| --- | --- | --- | --- |
| Vale | `e58732900ce0f94b85e46f3093cfd6facbb9e3cd` | MIT | Markup-aware deterministic linting and small inspectable rules. |
| Avoid AI Writing | `3c0fd8a2668962df97f0a6771dcd57c84a4be568` | MIT | Separation of regex-detectable signals from editorial judgment, corpus discipline, and explicit limits on authorship classification. |
| Cursor pstack Unslop | `2a8044425c7bddf429c3bdedf3ab61e791d34d65` | MIT for `pstack` | Compact pattern catalog, portability test, mechanism-first specificity, and rhythm audit. |
| Better Writing | `4023076319e5a7838dd7587ebf3d5e3588f9544f` | MIT | Preservation contract, context dials, genre exemptions, voice fixtures, and preflight checks. |
| Harper | `3bec2dbe7328c60a931161148cf861e32efff173` | Apache-2.0 | Private, low-latency English mechanics and structured, markup-aware diagnostics. |
| No AI Slop | `d30eddb9e04562234f2070b5ee63ca4649d9a05e` | MIT | Audit-only mode, minimum-effective editing, named findings, and no authorship guesses. |
| Humanizer | `43c97670b563cfa75e4f16ef00c32e933104d10a` | MIT | Cross-client packaging, author-sample calibration, broad pattern coverage, and non-fabrication guidance. |
| AntiSlop Sampler | `0ae330e98fbe6f09351f2d1063a51956378a44b2` | Apache-2.0 | Phrase-level prevention research and the warning that generated slop lists require curation rather than blanket adoption. |
| LanguageTool | `d20060d4257ddd7a561567719c10bd574e3f0e85` | LGPL-2.1-or-later | Multilingual grammar/style architecture; referenced as an optional external tool and not redistributed. |
| Promptfoo | `7d6b91a63cc7b20b589545ef505af71a82892a7b` | MIT | Deterministic assertions, model-graded evaluation boundaries, and repeatable regression configuration. |

## Local knowledge

`/Users/judiazm/Projects/no-ai-copy` is a user-owned local corpus, not an upstream package. It contributes the Nuko Nova house profile and real editing lessons: via-negativa value propositions, fake triplets, contrastive countdowns, vague superlatives, generic collaborative calls to action, and the need to audit metadata and repeated copy surfaces.

## Deliberate departures

- Em dashes, en dashes, curly quotes, parentheses, passive voice, adverbs, formal vocabulary, three-item lists, headings, and bullets are not authorship signals. The zero-em-dash preference for newly drafted or rewritten mutable prose is an owner style choice: Avoid AI Writing's published corpus table measured em-dash frequency skewing human at 0.2x, and the pstack advice to swap dashes for periods is rejected because the owner's own editing history shows it manufactures staccato slop.
- Personality is never invented for neutral or high-stakes prose.
- A self-audit does not require showing users multiple ceremonial drafts.
- Deterministic findings are writing signals, not evidence of machine authorship.
- Large word and phrase lists remain outside the package unless a small rule has a documented purpose and false-positive boundary.

## Optional tools

Vale, Harper, LanguageTool, and Promptfoo are not dependencies. When already installed and appropriate:

- use Vale for markup-aware house-style enforcement
- use Harper for private English mechanics
- use LanguageTool for multilingual grammar and style
- use Promptfoo for repeated model-backed writing pipelines

Do not install or call an external service without the user's authorization. The bundled Python checks remain the default.
