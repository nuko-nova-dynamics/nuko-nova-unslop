# Source map

Research cutoff: August 21, 2026. `upstreams.lock.json` is the machine-readable source of reviewed commit pins and monitored paths.

| Source | Reviewed commit | License | What it contributed |
| --- | --- | --- | --- |
| Vale | `d0e65f4187c304b174f9bcb2854f02ebb455708f` | MIT | Markup-aware deterministic linting and small inspectable rules. |
| Avoid AI Writing | `b504e2086bd3e544615afba7e5c7f31c8eade1d0` | MIT | Separation of deterministic signals from editorial judgment, protected Markdown-fence handling, corpus discipline, and explicit limits on authorship classification. |
| Cursor pstack Unslop | `46125561306434d8a1d7745d540d8932ab0cd2a2` | MIT for `pstack` | Compact pattern catalog, portability test, mechanism-first specificity, and rhythm audit. |
| Better Writing | `0f6ea786b644928b2c047cf0407ba6f2f3190c6e` | MIT | Preservation contract, context dials, genre exemptions, voice fixtures, and preflight checks. |
| Harper | `3486414b5756f579c4fdf268173dcbb6cbf00ec6` | Apache-2.0 | Private, low-latency English mechanics and structured, markup-aware diagnostics. |
| No AI Slop | `d30eddb9e04562234f2070b5ee63ca4649d9a05e` | MIT | Audit-only mode, minimum-effective editing, named findings, and no authorship guesses. |
| Humanizer | `e2e92e7b4b8229253ed5c8e81dc65463fdeddda5` | MIT | Cross-client packaging, author-sample calibration, broad pattern coverage, and non-fabrication guidance. |
| AntiSlop Sampler | `0ae330e98fbe6f09351f2d1063a51956378a44b2` | Apache-2.0 | Phrase-level prevention research and the warning that generated slop lists require curation rather than blanket adoption. |
| LanguageTool | `86c5f3a966621dcacdf910e5a9a7e0d69d949842` | LGPL-2.1-or-later | Multilingual grammar/style architecture; referenced as an optional external tool and not redistributed. |
| Promptfoo | `127d90534b9c1b1ba4554f007dd4b5fd2c8bf1b4` | MIT | Deterministic assertions, model-graded evaluation boundaries, and repeatable regression configuration. |

## Local knowledge

The user-owned No AI Copy corpus is private research material, not an upstream package. It contributes the Nuko Nova house profile and real editing lessons: via-negativa value propositions, fake triplets, contrastive countdowns, vague superlatives, generic collaborative calls to action, and the need to audit metadata and repeated copy surfaces.

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
