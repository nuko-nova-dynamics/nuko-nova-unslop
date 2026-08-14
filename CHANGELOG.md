# Changelog

## 0.4.0 - 2026-08-14

- Add one shared lifecycle-hook layer for Codex and Claude Code so the baseline no longer depends on optional Codex skill invocation or Claude's main-conversation-only output style.
- Inject the full standard at session boundaries, a compact contract when subagents start, and a small per-prompt reminder in Codex.
- Check main-agent final output locally for em dashes, spaced double hyphens, and clear assistant or artifact leaks, with one corrective pass and a loop guard.
- Exempt quoted Markdown blocks from punctuation and phrase checks in file audits and final output so protected source wording does not trigger the backstop.
- Document Codex's required hook-trust review and the exact clean-output versus corrective-pass latency trade-off.

## 0.3.0 - 2026-08-13

- Carry explicit writing corrections through a conversation without making the user repeat them.
- Keep task, file, project, audience, and genre constraints inside their demonstrated scope instead of silently promoting them to standing preferences.
- Reject typos, pasted text, tool output, quotations, and bare approvals as preference evidence.
- Resolve a contract contradiction so an author sample cannot silently override the standing zero-em-dash preference.
- Document the privacy boundary for interaction-derived improvements: generalized rules only, with synthetic public regressions.
- Rename the upstream cadence to every two days and recognize narrowly scoped, owner-authorized automations as valid release authorization.
- Require authorized automated releases to verify exact targets, pass every gate, publish immutable plugin and marketplace state, and update both clients. No-change reviews remain no-ops.

## 0.2.2 - 2026-08-13

- Add original light, dark, and compact marketplace artwork built from one Nuko Nova Unslop mark.
- Expose the artwork through the Codex plugin interface and preserve the same packaged assets for both client distributions.
- Validate PNG signatures, exact square dimensions, and manifest path alignment in the dependency-free bundle gate.
- Record the image-generation and deterministic compositing process in the provenance file.

## 0.2.1 - 2026-08-13

- Draft and rewrite mutable prose with zero em dashes or spaced double-hyphen substitutes, restructured into flowing sentences rather than staccato fragments. Preserve quotations, code, proper titles, contractual text, fixed strings, and en-dash ranges; a voice sample alone does not override the preference.
- Define voice ownership: judgment, warmth, humor, and point of view are allowed for the actual author, the assistant as itself, an approved brand voice, or an authorized genre, and are never invented for a represented person.
- Fix chatbot-artifact alternatives that could never match ("Certainly!", "Of course,") and scope "let me know if" to assistant offers so ordinary human email closers stop flagging as errors.
- Normalize curly apostrophes before phrase matching so typographic copy is checked like plain copy.
- Exempt typographic label separators from the balanced rhythm count and Markdown checklists from the staccato rule, while strict and house passes still flag em dashes in mutable prose.
- Exempt quoted spans from phrase and dash findings so exact source language remains untouched.
- Require parent agents to pass delegated prose through the skill before delivery because forced client styles do not necessarily propagate to subagents.
- Add cutoff-disclaimer and hedging-filler rules, extend interpretive-label to neutral connectors in strict and house profiles, add via-negativa nouns fees, fuss, prep, and guesswork, and add `to sum up` to the generic-conclusion rule.
- Track sentence-final numbers and hyphen or dash ranges in the preservation guard so en-dash corruption and trailing-number drift surface for review.
- Record the measured corpus evidence behind the confidence ordering and the em-dash stance in the pattern catalog and source map.

## 0.2.0 - 2026-08-13

- Make unslopped prose the default standard for every human-facing response and artifact.
- Enable implicit Codex invocation explicitly and broaden the skill trigger to all writing surfaces.
- Add a forced Claude Code output style that applies while the plugin is enabled and retains coding instructions.
- Define proportionate linting: internal checks for short chat, local linting for substantive prose, and preservation checks for fact-dense rewrites.
- Add regression gates for the always-on contract across both clients.

## 0.1.0 - 2026-08-13

- Add the shared Codex and Claude Code plugin manifests.
- Add draft, rewrite, audit, file, embedded, and evolution modes.
- Add balanced, strict, and Nuko Nova editing profiles.
- Add deterministic linting, protected-fact comparison, regression tests, and package validation.
- Add deliberate package-mutation tests for client drift, source pins, references, and cadence.
- Add a controlled every-other-day upstream review workflow.
