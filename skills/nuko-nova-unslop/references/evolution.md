# Controlled evolution

Use this protocol when maintaining or updating Nuko Nova Unslop. The objective is better behavior, not a larger rule count.

## Cadence

Check upstream state every two days. A check is read-only until a reviewed change justifies a local edit. Do not update source pins merely to make the report clean.

The permanent reference worktrees normally live at:

`../_reference/nuko-nova-unslop-sources` relative to the plugin's parent directory.

Override that location with `--references-dir` when needed.

## Review sequence

1. Run:

   ```bash
   python3 scripts/check_upstreams.py --refresh --format markdown --output upstream-review.md
   ```

2. For each changed source, inspect only the monitored paths and their diff from the reviewed SHA. Read surrounding context before drawing a conclusion.
3. Classify the change:
   - new editorial failure pattern
   - false-positive or preservation safeguard
   - deterministic detection improvement
   - evaluation or fixture improvement
   - cross-client packaging or manifest change
   - optional tool integration change
   - irrelevant repository churn
4. Decide whether the plugin should change. “No change” is a valid result.
5. If behavior changes, update the smallest appropriate artifact: skill instruction, reference, lint rule, helper, fixture, validator, or packaging file.
6. Add a regression case for any non-obvious rule, exception, or safety fix.
7. Run the full validation suite and compare lint output on both slop-heavy and clean-human fixtures.
8. Review the diff for third-party copying, inflated claims, new blanket bans, and degraded context handling.
9. Advance only the accepted source pins:

   ```bash
   python3 scripts/check_upstreams.py --refresh --accept source-id
   ```

10. Record the behavioral reason in `CHANGELOG.md`. Do not list a source bump as a product improvement when behavior did not change.

## Admission tests for a new rule

A rule must answer all of these:

- What observable failure does it identify?
- How does the failure hurt clarity, specificity, trust, voice, or usefulness?
- In which genres or contexts is the same form valid?
- Can a deterministic check detect it reliably, or does it require editorial judgment?
- What is the smallest fix?
- What clean-human fixture prevents overreach?

Reject rules based only on folklore, a single disliked word, or “humans never write this.”

## Source handling

- Do not ingest upstream prompt files, regex engines, or phrase corpora wholesale.
- Prefer concepts and independently written implementations.
- Preserve applicable license and attribution notices.
- Treat generated or scraped word lists as research data, not an automatic blacklist.
- Treat README claims and model-generated summaries as leads. Verify against code, tests, results, or primary documentation.
- Separate upstream repository updates from changes in the large tool's writing-relevant surface. A desktop UI commit in a grammar checker normally requires no plugin change.

## Safety invariants

Every accepted evolution must preserve these guarantees:

- no invented facts, sources, stance, or personality
- personality stays with an owned voice: the author, the assistant as itself, an approved brand voice, or an authorized genre
- source facts and fixed strings outrank style rules
- author samples guide cadence and syntax but do not override the zero-em-dash house preference without an explicit request for the current piece
- removed em dashes are restructured into flowing sentences, never into staccato fragments
- context and genre outrank isolated surface patterns
- audit mode never rewrites
- a no-op remains valid
- deterministic helpers remain local and dependency-free
- Codex and Claude manifests stay synchronized

## Release boundary

Passing local checks does not publish an update. Repository push, release tag, marketplace pin, marketplace validation, client installation, and client reload are separate stages.

Require explicit authorization before changing public or live state. A recurring automation created by the repository owner satisfies this requirement only when its prompt explicitly authorizes the exact push, release, marketplace, and client-update actions for Nuko Nova Unslop. On every authorized run:

1. Verify the plugin repository, branch, marketplace repository, open pull request or target branch, installed marketplace identity, and both client scopes before mutation.
2. Refuse to publish when tests fail, the worktree contains unrelated changes, credentials are unavailable, or the target cannot be resolved exactly.
3. For a behavioral improvement, bump the version, validate, commit, push, create an immutable tag and release, update the marketplace pin, validate and publish the marketplace change, then update and verify Codex and Claude Code.
4. For a fully reviewed upstream change that requires only a source-pin advance, commit and push the reviewed pins without claiming a behavioral release or reinstalling unchanged clients.
5. If no upstream changed, or no accepted change is justified, report the no-op without manufacturing a commit or release.
