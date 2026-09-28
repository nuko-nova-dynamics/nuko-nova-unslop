# Synthetic editorial regression cases

These cases require editorial review of the supplied context, not a standalone phrase detector.

## Visible thread: remove repeated setup

Context: The reader reports that archive job J42 failed because its access token expired and asks when to retry. The operator has confirmed that the token is renewed and the retry is scheduled for 15:00 UTC.

Draft: You reported that archive job J42 failed because its access token expired. An expired token prevents access to the archive. The token is renewed, and J42 will retry at 15:00 UTC.

Expected: The token is renewed, and J42 will retry at 15:00 UTC.

Reject: J42 succeeded. This invents a completed result.

## Necessary reminder: keep the condition

Context: The reader asks whether a planned retry can start. Approval is still pending.

Draft and expected no-op: J42 can retry after approval; it has not restarted yet.

Reject: J42 can retry. This removes the approval condition and incomplete status.

## Missing thread: preserve useful explanation

Context: Only the following message is available. The reader's prior knowledge is unknown.

Draft and expected no-op: J42 stopped because its access token expired. The token is renewed, and the retry is scheduled for 15:00 UTC.

Reject: Cut the cause solely because this is a reply. Shared knowledge has not been established.

## Requested handoff: repeat established facts

Context: The user requests a standalone handoff for a new operator. The cause and schedule appeared earlier in the thread.

Draft and expected no-op: J42 stopped because its access token expired. The token is renewed, and the retry is scheduled for 15:00 UTC. Completion is not confirmed.

Reject: Remove the cause, schedule, or incomplete status because they were already mentioned.
