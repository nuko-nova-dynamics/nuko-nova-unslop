# Provenance

Nuko Nova Unslop is an original, human-directed synthesis published by Nuko Nova Dynamics. Julio Diaz selected the source set, supplied house-style evidence, directed the product decisions, and required support for Codex and Claude Code. AI systems assisted with source inspection, drafting, implementation, and testing.

## Local source

The local `/Users/judiazm/Projects/no-ai-copy` corpus supplied Nuko Nova and Miami Web AI preferences derived from real editing sessions. Those preferences include reader-outcome framing, resistance to via-negativa value propositions, avoidance of manufactured triplets and contrastive countdowns, direct calls to action, and specific language over vague promotion.

## Public research sources

The source set includes the ten repositories in the August 13, 2026 research report: Vale, Avoid AI Writing, Cursor pstack Unslop, Better Writing, Harper, No AI Slop, Humanizer, AntiSlop Sampler, LanguageTool, and Promptfoo. The exact reviewed commits and monitored paths live in `upstreams.lock.json`.

The projects were used according to their strengths:

- writing skills informed pattern names, workflow ideas, voice safeguards, and false-positive boundaries
- deterministic scanners informed the separation between machine-checkable signals and editorial judgment
- prose linters and grammar tools informed optional final-pass architecture
- evaluation frameworks informed fixture design and preservation assertions
- cross-client packages informed manifest synchronization and validation

## Reuse policy

The plugin's prose, rule organization, Python helpers, tests, and workflows were written for this project. Third-party phrase corpora, detector engines, language models, grammar engines, and source code are not copied into the distribution.

Short conventional phrases such as pattern names and examples may overlap with public editorial guidance because they describe common writing structures. The package preserves the applicable license notices and identifies upstream influence even where the implementation was independently written.

LanguageTool is research-only in this package because its LGPL implementation and language data are not needed by the dependency-free core. Optional references to installed Vale, Harper, LanguageTool, or Promptfoo tools do not redistribute them.

## Claims boundary

The linter detects explicit phrases and document-shape signals. It cannot determine who wrote a text, and its output must not be described as an authorship score. A clean scan does not prove good writing; a flagged sentence does not prove AI involvement.

## License scope

The distribution is offered under Apache-2.0. Nuko Nova Dynamics licenses all rights it owns or is authorized to license. No rights to third-party names, marks, repositories, or independently owned materials are granted.
