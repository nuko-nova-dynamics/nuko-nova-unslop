# Source map

Research cutoff: October 6, 2026. `upstreams.lock.json` is the machine-readable source of reviewed commit pins and monitored paths.

| Source | Reviewed commit | License | Reviewed value |
| --- | --- | --- | --- |
| Vale | `cfb21a4ce87238bcfb44b90e8e0db9e0e91d6c09` | MIT | Markup-aware deterministic linting, quote and source-boundary tests, and small inspectable rules. |
| Avoid AI Writing | `db82bc8a2631f75fa829e97dc811c16a091fe1d9` | MIT | Separation of deterministic signals from editorial judgment, protected Markdown source boundaries, and corpus discipline. |
| Cursor pstack Unslop | `df581122cde17e6e27686b5a448bde23e4ad4318` | MIT for `pstack` | Compact pattern catalog, portability test, mechanism-first specificity, and rhythm audit. |
| Better Writing | `d77d4c074f8a1a51045a2f089d763fb5b78c1875` | MIT | Preservation contract, context dials, genre exemptions, voice fixtures, and preflight checks. |
| Harper | `ed69387634647a4771fc902a8264f3f8720ad71a` | Apache-2.0 | Private, low-latency English mechanics and structured, markup-aware diagnostics. |
| No AI Slop | `000650b156983f5159695b441477f4e63b25dc85` | MIT | Audit-only mode, minimum-effective editing, and named findings. |
| Humanizer | `225a6f39ac85f76ee48dbad772ea4abe4ed6c9d8` | MIT | Cross-client packaging, author-sample calibration, broad pattern coverage, and non-fabrication guidance. |
| AntiSlop Sampler | `0ae330e98fbe6f09351f2d1063a51956378a44b2` | Apache-2.0 | Phrase-level prevention research and the warning that generated slop lists require curation rather than blanket adoption. |
| LanguageTool | `576225c1df8c572a90ec9250244fdb7912816a03` | LGPL-2.1-or-later | Multilingual grammar/style architecture; referenced as an optional external tool and not redistributed. |
| Promptfoo | `a65fe81a676e906a304421e7af7423b435f8b882` | MIT | Deterministic assertions, model-graded evaluation boundaries, and repeatable regression configuration. |
| Stop Slop | `8da1f030185bdfe8471220585162991eaeb970e9` | MIT | Compact structural catalog and the lineage source for several later skills. Blanket bans on adverbs, passive voice, and individual punctuation remain outside the Nuko Nova standard. |
| Slopbeth | `b33718bb9283c11b09567dc714f92d90ffb7bd16` | MIT | Brief-versus-artifact separation, evidence-bound rewriting, sentence-load and topic-swap tests, preservation benchmarks, and dated evaluation hygiene. |
| Adam Boudjemaa Humanizer | `a58df065367550b6ce40ff3f648335018d8e0589` | MIT | Broad cross-harness catalog, voice profiles, cluster-based false-positive checks, and always-on instruction patterns. |
| Stephen Turner Deslop | `48287d806e61534bc14939b55b72c3f3f11a7db5` | MIT | Scientific-writing examples, register-aware exceptions, and a derivative Stop Slop and tropes catalog. It is tracked as derivative evidence, not an independent vote for shared rules. |
| Elithrar Anti-Slop | `4b38887ec969bbc1c97c1434732fac97ea7ff0dd` | MIT | Surgical edits and the author-defendability test for separating intentional voice from disposable formula. |
| SoundsHuman | `a45cfbba9fde843d670e553a0aa98f6a23d7fb28` | MIT | Explicit lineage, thresholded vocabulary tiers, conservative mechanical fixes, and a local scanner split from editorial judgment. Its merged catalogs are treated as derivative evidence. |
| Anti-AI-Slop Writing | `63255f9bbb75a265dc5786a04535cd033f487756` | No detected license file; README states MIT | Always-on activation and destination-specific formatting reminders. Blanket vocabulary bans and invented human detail are not adopted. |

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
