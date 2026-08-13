# Editorial contract

Use this reference for fact-dense, high-stakes, quoted, cited, technical, or heavily formatted work.

## Authority order

Apply instructions in this order:

1. The user's explicit constraints and fixed wording.
2. Source truth: facts, evidence, quotations, citations, numbers, uncertainty, and scope.
3. The user's applicable standing writing standards and current corrections.
4. A user-provided voice sample or named house style.
5. Genre, channel, and audience conventions.
6. The selected profile.
7. General anti-slop preferences.

A lower item never overrides a higher one. A voice sample informs cadence and syntax but does not repeal the zero-em-dash standing preference unless the user explicitly requests em dashes for the current piece. If a rule favors active voice but passive voice protects scientific or legal accuracy, keep the passive construction.

## Preservation ledger

Before a material rewrite, identify these protected classes:

- names, organizations, locations, product names, and proper nouns
- numbers, dates, prices, percentages, units, versions, and ranges
- quotations, citations, footnotes, URLs, email addresses, and link targets
- code identifiers, commands, flags, filenames, API names, and exact UI labels
- legal definitions, regulatory language, warnings, commitments, and disclaimers
- modality and uncertainty: `may`, `likely`, `estimated`, `alleged`, `subject to`, and similar limits
- scope: who or what a claim covers, and what it excludes
- user-marked fixed language and contractual text

Preserve meaning as well as tokens. Changing “may” to “will” can be worse than dropping a number.

For a file-to-file rewrite, run `scripts/preservation_guard.py`. Investigate every missing or added protected token. The helper cannot detect semantic drift, swapped ownership, changed negation, or altered causal claims, so perform a final manual comparison.

## Missing facts

Specificity must come from the source or the user.

When a useful sentence needs a missing detail:

- ask for it when the answer blocks the task
- use a visible marker such as `[Q2 churn figure needed]` when placeholders are appropriate
- state the limitation directly
- cut the unsupported claim

Never create a plausible percentage, customer, date, study, quotation, benchmark, or anecdote. Do not turn “experts say” into a named authority unless that authority appears in a verified source.

## Voice calibration

When the user supplies a sample, build an internal style fingerprint from evidence:

- sentence-length range and cadence
- paragraph length and openings
- plain versus formal vocabulary
- punctuation habits and contractions
- humor, bluntness, warmth, uncertainty, profanity, and first person
- asides, self-corrections, fragments, and repeated phrases
- typical density and amount of polish

Match stable habits without caricaturing them. Do not amplify every quirk or reuse distinctive phrases so often that the result becomes imitation. A sample controls style, not facts or opinions.

When no sample exists, infer only from the supplied draft and the channel. Use a clean, direct baseline without manufacturing personality. Personality must belong to an owned voice as defined in the skill's voice-ownership rules; an editor never donates opinions, feelings, or anecdotes to a represented author.

## Meaning preservation

Check these failure modes after rewriting:

- a qualified claim became certain
- correlation became causation
- an example became a general rule
- an attributed view became the author's view
- a future plan became a completed action
- a proposal became a commitment
- a group, geography, time period, or product scope widened
- a negative or exception disappeared
- a useful detail became a generic statement
- a list lost an item because three felt too formulaic

The “rule of three” is a warning about forced symmetry, not permission to delete a real three-item set.

## High-stakes registers

### Legal, policy, and compliance

Keep definitions, standards, citations, caveats, and approval boundaries exact. Do not make legal prose warmer or more opinionated for its own sake. If the task depends on current law or policy, verify it before editing the conclusion.

### Medical and financial

Preserve uncertainty, risk language, time horizons, units, eligibility, and source attribution. Do not replace technical terms with friendlier but less accurate language.

### Academic and scientific

Keep methodological passive voice, calibrated hedging, citations, equations, and disciplinary vocabulary when appropriate. Remove inflated significance only when it is unsupported.

### Technical documentation

Protect identifiers and present-tense behavior. Avoid narrating the diff unless the genre is a changelog, release note, or migration guide. Prefer the real system actor: compiler, server, client, parser, user, or team.

## Quotations and formatting

Do not rewrite quoted material because it contains a watched phrase. Do not alter code fences, inline code, YAML frontmatter, JSON, tables, citations, Markdown link targets, or HTML attributes during a prose-only pass. Punctuation inside quotations stays exactly as quoted, including em dashes, and en dashes in numeric and date ranges stay en dashes.

Formatting can be functional. Keep headings, lists, bold text, tables, emojis, and typography when the destination or author uses them deliberately. Remove them when they decorate weak prose or repeat information already conveyed by structure.

## Safe outcomes

The correct result may be:

- no change
- a few targeted edits
- an audit with no rewrite
- a request for missing facts
- a rewrite with an explicit unresolved gap

Do not perform an aggressive rewrite merely to demonstrate that the skill ran.
