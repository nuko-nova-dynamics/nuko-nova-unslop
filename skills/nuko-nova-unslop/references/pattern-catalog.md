# Pattern catalog

Treat these as contextual editing signals. Diagnose clusters, purpose, and effect before changing text. Preserve quoted examples and valid genre conventions.

## Confidence levels

- **Leak:** Usually removable generation residue rather than intended prose.
- **Strong:** Often weakens writing, but confirm the span is not quoted, required, or genre-correct.
- **Contextual:** Edit only when it repeats, obscures meaning, or conflicts with the chosen voice.

The measured corpus among the sources supports this ordering: structure and cluster signals carry more editorial weight than isolated vocabulary or punctuation folklore.

## Generation leaks

| ID | Signal | Focused response |
| --- | --- | --- |
| `chatbot-artifact` | “Certainly,” “I hope this helps,” “let me know if,” or an assistant greeting pasted into content | Remove the conversation wrapper. |
| `reasoning-artifact` | “Let's think step by step,” tool narration, or hidden-process language | Keep the conclusion or action, not the model's process. |
| `citation-leak` | Raw `oaicite`, `contentReference`, turn IDs, or malformed citation markers | Repair from the real source or remove the broken marker. |
| `placeholder-leak` | `[Your Name]`, “insert statistic,” `TODO`, or template residue in final prose | Fill it from supplied facts or flag the gap. |
| `cutoff-disclaimer` | Training-cutoff language or prose about not finding information | Verify the fact, state what is unknown, or cut the sentence. |

## Inflated meaning and authority

| ID | Signal | Focused response |
| --- | --- | --- |
| `significance-inflation` | “pivotal moment,” “testament to,” “marks a shift,” “plays a vital role” | State what happened and why it matters using supported consequences. |
| `promotional-fog` | “groundbreaking,” “breathtaking,” “world-class,” “game-changing,” “vibrant” without proof | Replace the label with a feature, result, constraint, or remove it. |
| `vague-authority` | “experts say,” “studies show,” “industry reports suggest” without a named source | Name a verified source or remove the appeal. |
| `notability-list` | Media, customer, or award names stacked without relevant context | Keep the evidence that advances the point. Do not invent context. |
| `generic-future` | “the future looks bright,” “exciting times lie ahead,” or progress-as-destiny | End on the actual plan, evidence, risk, or next action. |
| `formulaic-challenges` | “Despite challenges, X continues to thrive” | Name the specific problem and response, if sourced. |
| `interpretive-label` | “This is crucial,” “the key point is,” “as you can see,” “this underscores,” “this signals that” | Let evidence carry emphasis, or state the author's actual judgment. Keep literal technical uses such as a process signaling a handler. |
| `hedging-filler` | “It's worth noting that,” “it's important to note that” | State the point and delete the announcement that it matters. |

## Formula and staged rhetoric

| ID | Signal | Focused response |
| --- | --- | --- |
| `negative-reframe` | “It's not X; it's Y,” “not only X but Y,” or “not X. Not Y. Just Z.” | State the positive claim unless the contrast is real and useful. |
| `via-negativa` | Value expressed mainly as “No fees. No fuss. No surprises.” | Describe what the reader gets. This is strict in the Nuko Nova profile. |
| `forced-three` | Three qualities, clauses, or fragments assembled for rhetorical completeness | Use the natural number of supported ideas. Keep real three-item sets. |
| `staccato-drama` | Runs of tiny declarative sentences or fragments built to sound quotable | Join related thoughts and let one short sentence earn emphasis. |
| `colon-reveal` | A setup noun phrase followed by a dramatic lowercase reveal | Write a normal sentence. Keep colons for lists, labels, quotations, and genuine explanations. |
| `fake-insider` | “Here's what nobody tells you,” “the uncomfortable truth,” “the part everyone misses” | Make the underlying claim stand on its evidence. |
| `rhetorical-qa` | A question immediately answered to manufacture momentum | State the answer directly unless the question serves the reader. |
| `false-range` | “From X to Y” where the endpoints do not form a meaningful range | Name the topics or sequence directly. |
| `false-concession` | A balanced-sounding “while X, Y” that does not express a real tension | State the actual finding and trade-off. |
| `generic-recap` | A final paragraph restating the piece with “in conclusion,” “overall,” or “ultimately” | End on the last concrete point or action. |
| `aphorism-formula` | “X is the currency of Y,” “the architecture of,” or a reusable mic-drop metaphor | Replace it with the concrete relationship. |

## Vague or assembled prose

| ID | Signal | Focused response |
| --- | --- | --- |
| `superficial-ing` | Trailing “highlighting,” “underscoring,” “showcasing,” or “ensuring” clause that pretends to analyze | Delete it or state the supported mechanism. |
| `abstract-outcome` | “drive impact,” “unlock value,” “elevate experiences,” “transform workflows” | Name what changes for whom and how. |
| `portability-failure` | The sentence could move unchanged to another product, person, or sector | Add supported specifics or cut it. |
| `copula-avoidance` | “serves as,” “stands as,” “boasts,” or “features” used to avoid `is` or `has` | Prefer the plain construction when meaning stays intact. |
| `weak-verb-stack` | “has the ability to,” “make a decision,” or abstract nouns hiding the action | Use `can`, `decide`, or the specific verb. |
| `synonym-cycling` | Several labels for the same person or system in one passage | Repeat the clearest term. |
| `fake-specificity` | An exact-sounding number, quote, source, or anecdote unsupported by the brief | Remove it and restore honest uncertainty. |
| `corporate-therapist` | “lean into our strengths,” “foster alignment,” or soft managerial abstractions | Name the action, owner, decision, or behavior. |

## Human without cringe

Cringe is usually a mismatch, not a word. The language performs more intimacy, emotion, cleverness, importance, vulnerability, or cultural fluency than the facts, author, audience relationship, or genre can support. Do not flatten an owned voice because it is playful, intense, strange, sentimental, or informal. Check ownership, proportion, audience fit, and substance.

Use these questions in order:

1. **Ownership:** Does the feeling, opinion, joke, slang, or attitude belong to the actual or approved voice?
2. **Proportion:** Does its intensity fit the event, evidence, stakes, and relationship?
3. **Audience:** Would this author naturally speak this way to this reader in this channel?
4. **Substance:** Does the flourish carry meaning or connection, or is it performing humanity?

| ID | Signal | Focused response |
| --- | --- | --- |
| `fake-intimacy` | “We've all been there,” “you know the feeling,” “between you and me,” or “trust me on this” without an established relationship or shared experience | State the point without claiming closeness, consensus, or shared experience. Keep genuine familiarity when the relationship supports it. |
| `performative-personality` | Canned quirks such as “plot twist,” “chef's kiss,” “mic drop,” “I'm not crying, you're crying,” or “main character energy” added to make ordinary information feel human | Keep the humor or flourish only when it belongs to the voice, fits the audience, and earns its space. Otherwise state the actual reaction or fact. |
| `emotional-overreach` | Fake enthusiasm, delight, outrage, heartbreak, awe, urgency, or triumph whose intensity exceeds the supported event | Lower the emotional temperature or supply the evidence that earns it. Preserve strong emotion present in the source. |
| `faux-vulnerability` | A confession, self-deprecation, or intimate aside manufactured without source evidence | Remove it. Never donate an experience or feeling to a represented person. |
| `quirk-injection` | Slang, emojis, deliberate fragments, grammar errors, profanity, or unusual punctuation added without support from the voice or context | Restore the natural register. Keep quirks supported by the author, channel, or approved voice. |
| `motivational-uplift` | Unsolicited encouragement, life lessons, inspirational summaries, or reassurance attached to ordinary information | End on the useful fact, decision, consequence, or next action unless encouragement is the actual purpose. |

## Rhythm, structure, and formatting

| ID | Signal | Focused response |
| --- | --- | --- |
| `uniform-rhythm` | Sentences and paragraphs repeat the same length and shape | Vary structure where the ideas call for it. Do not add content for variety. |
| `tiny-sections` | A heading every few sentences or a heading followed by a restatement | Merge sections or begin with the substantive sentence. |
| `inline-label-list` | Repeated bold label, colon, and sentence that echoes the label | Use prose or a real list whose labels aid scanning. |
| `list-addiction` | Bullets substitute for an argument or narrative | Use prose when sequence and relationships matter. Keep reference lists and checklists. |
| `decorative-emphasis` | Mechanical bolding, emoji section markers, or excessive title case | Remove decoration that does not convey structure. |
| `dash-cluster` | Em dashes repeatedly supply rhythm or fake punch | Restructure mutable prose with commas, colons, parentheses, or separate sentences, never with staccato fragments. Preserve quoted, fixed, or explicitly requested dashes and valid en-dash ranges. Typographic label separators do not count toward the balanced rhythm threshold, but strict and house passes still surface them for the zero-em-dash preference. |
| `dash-substitute` | A spaced double hyphen substitutes for an em dash in prose | Restructure the sentence. Preserve command flags and fixed strings. |
| `transition-stack` | Paragraphs repeatedly open with “Moreover,” “Furthermore,” “Additionally,” or “That said” | Remove announcements and connect the ideas directly. |
| `diff-anchored` | Documentation explains what was added or replaced rather than current behavior | Describe the current system unless change history is the genre. |

## Tone and relationship

| ID | Signal | Focused response |
| --- | --- | --- |
| `sycophancy` | Unnecessary praise, agreement, or servile reassurance | Respond to the substance. Keep genuine warmth. |
| `permission-giving` | “Feel free to,” “don't hesitate,” or repeated offers that dilute a clear action | Give the action, deadline, or contact path once. |
| `caveat-displacement` | Unrequested risk framing, permissions narration, process warnings, or background displaces the answer | Answer directly. Keep a caveat only when it materially changes accuracy, safety, legality, or the reader's next action. |
| `reader-context-gap` | A term, label, acronym, cost model, or technical choice appears without the context a non-expert reader needs | State the plain-language meaning and practical consequence first, then add exact terminology and detail. Keep it concise for an expert audience. |
| `manufactured-soul` | Added opinion, first person, humor, or emotional reaction not present in the source or brief | Remove the invented stance. Personality must belong to an owned voice: the actual author, the assistant speaking as itself, an approved brand voice, or an authorized creative genre. |
| `sterile-polish` | Every paragraph is equally tidy, neutral, and resolved despite a distinctive source voice | Restore supported edge, uncertainty, asides, or unevenness. |

## Contextual word bank

Words such as `delve`, `landscape`, `robust`, `seamless`, `leverage`, `transform`, `foster`, `pivotal`, `nuanced`, `tapestry`, `testament`, `underscore`, `streamline`, `unlock`, `empower`, and `elevate` deserve attention when they cluster or replace a more exact word. They are not forbidden in quotations, precise technical usage, historical prose, or an author's established voice.

Likewise, passive voice, adverbs, parentheses, curly quotes, Oxford commas, hyphenated compounds, transitions, and three-item lists are normal language. Flag the observed failure, not the mere presence of a feature.

## Signs to preserve

- unusual and verifiable detail
- mixed feelings or unresolved tension
- era-bound references and subcultural language
- defendable first-person judgments
- clear long sentences mixed with short ones
- genuine asides and self-corrections
- technically necessary terms and caveats
- deliberate repetition
- punctuation habits supported by the author's sample

Good human writing may be polished, formal, complex, or grammatically perfect.

## Deterministic linter coverage

`scripts/unslop_lint.py` implements a subset of this catalog: the leak rules, the high-confidence phrase rules, the em-dash check, and the two rhythm checks. Its `watched-vocabulary` rule maps to the contextual word bank, `generic-conclusion` spans `generic-recap` and `generic-future`, `signposting` covers throat-clearing openers such as “let's dive in” and “without further ado,” and the profile-scoped `via-negativa` and `collaborative-cta` rules are defined with the house rules in [profiles-and-genres.md](profiles-and-genres.md). Strict and Nuko Nova passes also surface a small set of canned `fake-intimacy` and `performative-personality` phrases for review. Emotional proportion, relationship fit, caveat relevance, reader context, humor, slang, vulnerability, and genuine personality remain contextual judgments outside deterministic coverage.
