# Source map

`upstreams.lock.json` is the only record of reviewed commits, review dates, and monitored paths. `scripts/check_upstreams.py --accept` updates it, so this table does not repeat pins. Each row links the repository named in the lock, and the bundle validator requires one row per locked source.

| Source | License | Reviewed value |
| --- | --- | --- |
| [Vale](https://github.com/vale-cli/vale) | MIT | Markup-aware deterministic linting, quote and source-boundary tests, and small inspectable rules. |
| [Avoid AI Writing](https://github.com/conorbronsdon/avoid-ai-writing) | MIT | Separation of deterministic signals from editorial judgment, protected Markdown source boundaries, and corpus discipline. |
| [Cursor pstack Unslop](https://github.com/cursor/plugins) | MIT for `pstack` | Compact pattern catalog, portability test, mechanism-first specificity, and rhythm audit. |
| [Better Writing](https://github.com/forjd/better-writing) | MIT | Preservation contract, context dials, genre exemptions, voice fixtures, and preflight checks. |
| [Harper](https://github.com/Automattic/harper) | Apache-2.0 | Private, low-latency English mechanics and structured, markup-aware diagnostics. |
| [No AI Slop](https://github.com/petergyang/no-ai-slop) | MIT | Audit-only mode, minimum-effective editing, and named findings. |
| [Humanizer](https://github.com/blader/humanizer) | MIT | Cross-client packaging, author-sample calibration, broad pattern coverage, and non-fabrication guidance. |
| [AntiSlop Sampler](https://github.com/sam-paech/antislop-sampler) | Apache-2.0 | Phrase-level prevention research and the warning that generated slop lists require curation rather than blanket adoption. |
| [LanguageTool](https://github.com/languagetool-org/languagetool) | LGPL-2.1-or-later | Multilingual grammar/style architecture; referenced as an optional external tool and not redistributed. |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | MIT | Deterministic assertions, model-graded evaluation boundaries, and repeatable regression configuration. |
| [Stop Slop](https://github.com/hardikpandya/stop-slop) | MIT | Compact structural catalog and the lineage source for several later skills. Blanket bans on adverbs, passive voice, and individual punctuation remain outside the Nuko Nova standard. |
| [Slopbeth](https://github.com/ehmo/slopkit) | MIT | Brief-versus-artifact separation, evidence-bound rewriting, sentence-load and topic-swap tests, preservation benchmarks, and dated evaluation hygiene. |
| [Adam Boudjemaa Humanizer](https://github.com/Aboudjem/humanizer-skill) | MIT | Broad cross-harness catalog, voice profiles, cluster-based false-positive checks, and always-on instruction patterns. |
| [Elithrar Anti-Slop](https://github.com/elithrar/dotfiles) | MIT | Surgical edits and the author-defendability test for separating intentional voice from disposable formula. |
| [Anti-AI-Slop Writing](https://github.com/jalaalrd/anti-ai-slop-writing) | No detected license file; README states MIT | Always-on activation and destination-specific formatting reminders. Blanket vocabulary bans and invented human detail are not adopted. |

## Local knowledge

The user-owned No AI Copy corpus is private research material, not an upstream package. It contributes the Nuko Nova house profile and real editing lessons: via-negativa value propositions, fake triplets, contrastive countdowns, vague superlatives, generic collaborative calls to action, and the need to audit metadata and repeated copy surfaces.

## Deliberate departures

- The zero-em-dash preference for newly drafted or rewritten mutable prose is an owner style choice. The pstack advice to swap dashes for periods is rejected because the owner's own editing history shows it manufactures staccato slop.
- Personality is never invented for neutral or high-stakes prose.
- A self-audit does not require showing users multiple ceremonial drafts.
- Large word and phrase lists remain outside the package unless a small rule has a documented purpose and false-positive boundary.
- Repositories that merge or adapt earlier skills remain useful comparison sources, but repeated guidance from a derivative does not count as independent corroboration.

## Optional tools

Vale, Harper, LanguageTool, and Promptfoo are not dependencies. When already installed and appropriate:

- use Vale for markup-aware house-style enforcement
- use Harper for private English mechanics
- use LanguageTool for multilingual grammar and style
- use Promptfoo for repeated model-backed writing pipelines

Do not install or call an external service without the user's authorization. The bundled Python checks remain the default.
