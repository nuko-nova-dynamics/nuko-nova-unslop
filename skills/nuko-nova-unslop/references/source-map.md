# Source map

Research cutoff: August 27, 2026. `upstreams.lock.json` is the machine-readable source of reviewed commit pins and monitored paths.

| Source | Reviewed commit | License | Reviewed value |
| --- | --- | --- | --- |
| Vale | `405a7dabd73651d8ba24c72767a70c065aa6716a` | MIT | Markup-aware deterministic linting and small inspectable rules. |
| Avoid AI Writing | `40328bd292bc682d46010a6f9ac2cdbf4fb4ceca` | MIT | Separation of deterministic signals from editorial judgment, protected Markdown-fence handling, corpus discipline, and explicit limits on authorship classification. |
| Cursor pstack Unslop | `799151d91b6e12ee7dbd09f708eec108d7de9b3b` | MIT for `pstack` | Compact pattern catalog, portability test, mechanism-first specificity, and rhythm audit. |
| Better Writing | `0f6ea786b644928b2c047cf0407ba6f2f3190c6e` | MIT | Preservation contract, context dials, genre exemptions, voice fixtures, and preflight checks. |
| Harper | `1b7669236cb5aaa1a8f680c73f2844bfef2e6dfb` | Apache-2.0 | Private, low-latency English mechanics and structured, markup-aware diagnostics. |
| No AI Slop | `d30eddb9e04562234f2070b5ee63ca4649d9a05e` | MIT | Audit-only mode, minimum-effective editing, named findings, and no authorship guesses. |
| Humanizer | `e2e92e7b4b8229253ed5c8e81dc65463fdeddda5` | MIT | Cross-client packaging, author-sample calibration, broad pattern coverage, and non-fabrication guidance. |
| AntiSlop Sampler | `0ae330e98fbe6f09351f2d1063a51956378a44b2` | Apache-2.0 | Phrase-level prevention research and the warning that generated slop lists require curation rather than blanket adoption. |
| LanguageTool | `eea6b35ac428a3d2230e1585444e70cff2ae5992` | LGPL-2.1-or-later | Multilingual grammar/style architecture; referenced as an optional external tool and not redistributed. |
| Promptfoo | `e3b36451f4a2e587e819b2c4a19313003d68cde5` | MIT | Deterministic assertions, model-graded evaluation boundaries, and repeatable regression configuration. |
| Stop Slop | `8da1f030185bdfe8471220585162991eaeb970e9` | MIT | Compact structural catalog and the lineage source for several later skills. Blanket bans on adverbs, passive voice, and individual punctuation remain outside the Nuko Nova standard. |
| Slopbeth | `b33718bb9283c11b09567dc714f92d90ffb7bd16` | MIT | Brief-versus-artifact separation, evidence-bound rewriting, sentence-load and topic-swap tests, preservation benchmarks, and dated detector-evidence hygiene. |
| Adam Boudjemaa Humanizer | `98d27388c85dcccb0f7cf58cc22f4ef879c3c78b` | MIT | Broad cross-harness catalog, voice profiles, cluster-based false-positive checks, and always-on instruction patterns. Self-scoring remains a review signal, never an authorship verdict. |
| Stephen Turner Deslop | `48287d806e61534bc14939b55b72c3f3f11a7db5` | MIT | Scientific-writing examples, register-aware exceptions, and a derivative Stop Slop and tropes catalog. It is tracked as derivative evidence, not an independent vote for shared rules. |
| Elithrar Anti-Slop | `36b4a7e8d41b55ff5dff568a22f62bb0214967df` | MIT | Surgical edits and the author-defendability test for separating intentional voice from disposable formula. |
| SoundsHuman | `a45cfbba9fde843d670e553a0aa98f6a23d7fb28` | MIT | Explicit lineage, thresholded vocabulary tiers, conservative mechanical fixes, and a local scanner split from editorial judgment. Its merged catalogs are treated as derivative evidence. |
| Anti-AI-Slop Writing | `63255f9bbb75a265dc5786a04535cd033f487756` | No detected license file; README states MIT | Always-on activation and destination-specific formatting reminders. Blanket vocabulary bans, detector claims, and invented human detail are not adopted. |

## Local knowledge

The user-owned No AI Copy corpus is private research material, not an upstream package. It contributes the Nuko Nova house profile and real editing lessons: via-negativa value propositions, fake triplets, contrastive countdowns, vague superlatives, generic collaborative calls to action, and the need to audit metadata and repeated copy surfaces.

## Deliberate departures

- Em dashes, en dashes, curly quotes, parentheses, passive voice, adverbs, formal vocabulary, three-item lists, headings, and bullets are not authorship signals. The zero-em-dash preference for newly drafted or rewritten mutable prose is an owner style choice: Avoid AI Writing's published corpus table measured em-dash frequency skewing human at 0.2x, and the pstack advice to swap dashes for periods is rejected because the owner's own editing history shows it manufactures staccato slop.
- Personality is never invented for neutral or high-stakes prose.
- A self-audit does not require showing users multiple ceremonial drafts.
- Deterministic findings are writing signals, not evidence of machine authorship.
- Large word and phrase lists remain outside the package unless a small rule has a documented purpose and false-positive boundary.
- Repositories that merge or adapt earlier skills remain useful comparison sources, but repeated guidance from a derivative does not count as independent corroboration.

## Optional tools

Vale, Harper, LanguageTool, and Promptfoo are not dependencies. When already installed and appropriate:

- use Vale for markup-aware house-style enforcement
- use Harper for private English mechanics
- use LanguageTool for multilingual grammar and style
- use Promptfoo for repeated model-backed writing pipelines

Do not install or call an external service without the user's authorization. The bundled Python checks remain the default.
