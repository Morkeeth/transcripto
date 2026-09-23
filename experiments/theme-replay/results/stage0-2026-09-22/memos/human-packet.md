# Theme Replay Stage 0 · blind memo packet

Question: What makes an agent-work episode require correction?

Rate each memo before you open memo-report.json. For each memo write KEEP, REVISE or REJECT and one sentence.
Also rank the three memos you find most useful. Citations are `Eyy Ln`; open them with `corpus-lines.txt`.

## P01

- (pattern) Every recorded correction in the corpus is a user turn that changes the target file, the scope, or a design/visibility decision after the initial request.  [E04 L2, E08 L2, E12 L2]
- (pattern) Correction is decoupled from tool-outcome status: E12 was corrected despite both edits succeeding, and E08's write to the originally requested path succeeded before the user redirected it.  [E12 L3, E12 L4, E08 L3]  counter: E04
- (pattern) Failed edit/patch operations (text not found, context mismatch, old_string not found) end their episodes with no recorded correction and no subsequent succeeded event.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (exception) E04 is the sole exception where a failed tool event co-occurs with a correction, and the failure message ('wrong file') matches the correction's redirected target, though the corpus does not show which came first causally.  [E04 L3, E04 L4]  counter: E02, E06, E10
- (pattern) Unknown tool results leave the requested outcome unverifiable, most sharply in E07 where the request conditioned the commit on a green suite but the commit's result is unrecorded.  [E07 L1, E07 L2, E03 L2, E11 L2]
- (pattern) Episodes with a stable request and all-succeeded events complete without correction (E01, E05, E09), but E12 shows clean execution does not guarantee a correction-free episode.  [E01 L3, E05 L2, E09 L3]  counter: E12
- (open_question) Whether failed and unknown episodes 'require correction' is undecidable from this corpus: they never reach a succeeded event, yet no correction or follow-up is recorded for any of them.  [E06 L2, E07 L2]  counter: E04

Decision: ______  Sentence: ______________________

## P02

- (pattern) Every recorded correction in the corpus is an explicit human redirect of the file target, the content scope, or the API/design contract.  [E04 L2, E08 L2, E12 L2]
- (pattern) In the recorded order, each correction is logged at line 2, before any tool event in its episode, so the corpus presents corrections as intent realignments rather than as reactions to observed tool outcomes.  [E08 L2, E08 L3, E04 L2, E04 L3]
- (pattern) Failed tool events in E02, E06, and E10 leave the requested change unmade yet carry no correction field, so execution failure and recorded correction are disjoint in this corpus.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (pattern) Episodes where the stated intent stays stable and every tool event succeeds (E01, E05, E09) carry no correction, so successful execution under stable intent does not require correction.  [E01 L2, E01 L3, E05 L2, E09 L3]  counter: E08, E12
- (exception) E04 is the sole episode mixing a correction with a failed event: after the redirect to the header parser, an edit to the originally requested auth parser failed as 'wrong file' before the redirected edit succeeded.  [E04 L2, E04 L3, E04 L4]
- (open_question) Unknown-status episodes (E03, E07, E11) leave the requested test, commit, or inspection unverifiable, and the frozen corpus records neither an outcome nor a correction, so their correction-need cannot be determined and unknown must not be upgraded.  [E03 L2, E07 L2, E11 L2]
- (open_question) Whether failed episodes 'require correction' is a definitional gap the corpus cannot settle: E06's requested change is never shown completed, yet no retry or correction is recorded, so 'needs remediation' and 'recorded correction' cannot be reconciled from the lines.  [E06 L1, E06 L2]  counter: E04

Decision: ______  Sentence: ______________________

## P03

- (pattern) Every correction in the corpus rewrites the user's own initial specification rather than addressing agent behavior: E04 swaps the named file ('No, I meant...'), E08 changes the filename and scope, and E12 reverses the instruction to ship the helper as the public API.  [E04 L1, E04 L2, E08 L1, E08 L2, E12 L1, E12 L2]
- (pattern) In all three correction episodes the correction sits on the line immediately after the request and before any tool event, so corrections intercept the plan rather than react to tool output.  [E04 L2, E08 L2, E12 L2]
- (pattern) Failed tool matches — 'text not found', 'context mismatch', 'old_string not found' — occur in E02, E06 and E10 with no correction recorded, so tool failure by itself does not make an episode require correction.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (exception) Corrections also appear in episodes where every recorded tool event succeeded (E08, E12), so green tool results do not make an episode correction-proof — correction tracks the match to user intent, not tool status.  [E08 L2, E08 L3, E08 L4, E12 L3, E12 L4]  counter: E04
- (pattern) Episodes whose request names one clear target and whose tools all succeed — E01, E05, E09 — close with no correction at all.  [E01 L1, E01 L3, E05 L2, E09 L3]  counter: E08, E12
- (exception) In E04 the mis-targeted edit is still attempted and fails with 'wrong file' after the correction line, so a correction does not itself prevent the wrong action from being executed.  [E04 L2, E04 L3, E04 L4]  counter: E08, E12
- (open_question) No episode with an unknown tool outcome (E03, E07, E11) contains a correction; whether users decline to correct unverified runs or those episodes simply end early cannot be determined from the lines.  [E03 L2, E07 L2, E11 L2]
- (open_question) Whether near-identical path names (lab/docs/caching.md vs lab/docs/cache.md) contribute to corrections like E08's cannot be settled from the corpus.  [E08 L1, E08 L2]  counter: E04, E12

Decision: ______  Sentence: ______________________

## P04

- (pattern) Every correction in the corpus redirects the target or scope of the original request rather than reporting a tool problem.  [E04 L2, E08 L2, E12 L2]
- (pattern) Failed tool calls by themselves do not trigger corrections: E02, E06, and E10 record failures with no correction line at all.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (pattern) Unrecorded tool results (status unknown) also pass without any correction in E03, E07, and E11.  [E03 L2, E07 L2, E11 L2]
- (pattern) Every episode that receives a correction still ends with a succeeded event, so corrections here are recoverable rather than terminal.  [E04 L4, E08 L4, E12 L4]
- (pattern) Two of the three corrections swap between easily confused file targets named in the request (auth/parser.py vs http/headers.py; caching.md vs cache.md).  [E04 L1, E08 L1]  counter: E12
- (exception) E04 is the only episode where a correction and a failed event co-occur, and the failed edit to the original target itself records 'wrong file'.  [E04 L3]
- (open_question) The lines show corrections asserting new intent but not whether the original request was ambiguous or the requester changed their mind, as when E12's request to ship the helper publicly was reversed.  [E12 L1, E12 L2]

Decision: ______  Sentence: ______________________

## P05

- (pattern) Episodes that require correction are marked by an explicit user redirection issued after the agent's initial action (E04, E08, E12).  [E04 L2, E08 L2, E12 L2]  counter: E01, E05, E09
- (pattern) Each recorded correction fixes a different mismatch — wrong target file (E04), wrong document and scope (E08), wrong API visibility (E12) — so 'correction' covers several distinct mismatch types rather than one.  [E04 L2, E08 L2, E12 L2]
- (exception) A failed tool event alone does not make an episode a correction episode: E02, E06, and E10 end in recorded failures with no correction line and no recorded resolution.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (open_question) Episodes whose only event is unknown (E03, E07, E11) cannot be classified as requiring correction; they are observability gaps, and per the rules their status must not be upgraded to failed or succeeded.  [E03 L2, E07 L2, E11 L2]
- (pattern) When the agent's first action matches the request, episodes complete with succeeded events and no correction (E01, E05, E09).  [E01 L2, E05 L2, E09 L3]

Decision: ______  Sentence: ______________________

## P06

- (pattern) All three recorded correction lines realign the operative specification rather than the method: E04 retargets the file, E08 changes the output path and scope, and E12 reverses the API-exposure decision.  [E04 L2, E08 L2, E12 L2]
- (pattern) The three failed episodes that stand in need of technical remediation share one failure mode: the edit tool could not find the anchor text or context it was told to match.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (pattern) Episodes whose only tool result is unknown cannot deliver what was asked — a green/red report, a conditional commit, an existence check — so they require renewed observation rather than repair of a known failure.  [E03 L1, E03 L2, E07 L2, E11 L2]
- (exception) Succeeded events do not close an episode: E08 and E12 contain only succeeded event lines yet still required user correction, an exception to the E01/E05/E09 pattern where recorded success sufficed.  [E08 L2, E08 L3, E12 L2, E12 L3]  counter: E01, E05, E09
- (open_question) E04 leaves the causal order of failure and correction undetermined, because the correction is recorded at line 2 while the failed edit to the original target is recorded afterward at line 3.  [E04 L2, E04 L3]  counter: E02
- (pattern) Each agent harness exhibits each kind of correction trigger — failure, unknown result, and explicit correction — so correction need is not harness-specific in this corpus, although the uniform one-of-each layout may be an artifact of its synthetic construction.  [E02 L2, E07 L2, E12 L2]
- (open_question) The corpus does not show whether correction requires undoing superseded side effects: in E08 the write to the originally requested path is recorded as succeeded after the correction line, and no line reverts it.  [E08 L2, E08 L3]
- (open_question) Whether 'requires correction' covers only the three episodes with explicit correction lines or also the six episodes left failed or unverified cannot be settled from the corpus, because no user turn follows any failed or unknown event.  [E06 L2, E03 L2]

Decision: ______  Sentence: ______________________

## P07

- (pattern) Failed edit or patch operations leave the requested change undelivered, so E02, E06, and E10 require corrective work even though none contains a correction line.  [E02 L2, E06 L2, E10 L2]  counter: E01
- (pattern) Unknown tool results leave the requested report, conditional commit, or file-content answer unsupported by the record, so E03, E07, and E11 require renewed verification before they can be answered.  [E03 L2, E07 L2, E11 L2]  counter: E09
- (pattern) Explicit correction lines revise the operative target, scope, or interface decision after the initial request, making prior work misaligned in E04, E08, and E12.  [E04 L2, E08 L2, E12 L2]  counter: E05
- (pattern) A succeeded tool result does not by itself remove the need for correction, since E08 and E12 record successful operations that the correction lines then supersede.  [E08 L3, E08 L2, E12 L3, E12 L2]  counter: E01, E09
- (exception) E04 shows the failure-driven and intent-driven drivers of correction are not mutually exclusive, because an explicit target correction coincides with a failed edit recorded as the wrong file.  [E04 L2, E04 L3]
- (open_question) For the failed and unknown episodes the record ends at the failed or unknown event, so whether any remediation actually occurred remains unresolved.  [E06 L2, E07 L2, E10 L2]  counter: E04
- (open_question) The lines cannot establish whether the corrections in E04, E08, and E12 reflect agent misunderstanding or the user revising or mis-stating intent.  [E04 L1, E04 L2, E12 L1]

Decision: ______  Sentence: ______________________

## P08

- (pattern) Every recorded correction in the corpus is an explicit human redirection of target, scope, or design, and only E04, E08, and E12 contain one.  [E04 L2, E08 L2, E12 L2]
- (pattern) Correction tracks fit to the user's intent rather than tool-event status, since E08 and E12 were corrected even though every recorded event in them succeeded.  [E08 L3, E12 L3, E12 L2]
- (exception) In E04 the correction line (L2) precedes the failed edit (L3) in the frozen record, so the corpus does not show the failure prompting the correction.  [E04 L2, E04 L3]
- (pattern) A failed tool event by itself is not recorded as requiring correction: E02, E06, and E10 end in failures with no correction line.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (open_question) Whether the failed, uncorrected episodes (E02, E06, E10) actually required correction cannot be settled from the frozen corpus, which records no resolution after the failure.  [E02 L1, E02 L2]
- (open_question) Unknown-status episodes (E03, E07, E11) record no tool outcome, so their need for correction is unverifiable rather than demonstrated.  [E03 L2, E07 L2, E11 L2]
- (pattern) Episodes whose recorded events all succeeded and matched the request as given (E01, E05, E09) carry no correction, but clean execution is no guarantee a correction will not be issued.  [E01 L3, E05 L2, E09 L3]  counter: E08, E12

Decision: ______  Sentence: ______________________

## P09

- (pattern) Every explicit correction line in the corpus revises the episode's operative specification mid-stream — the target file in E04, the path and scope in E08, and the API visibility decision in E12.  [E04 L2, E08 L2, E12 L2]  counter: E02
- (pattern) A second kind of correction need is technical: failed edit or patch events leave the requested work incomplete even though no user correction is recorded (E02, E06, E10).  [E02 L2, E06 L2, E10 L2]  counter: E04
- (pattern) A third kind of correction need is epistemic: episodes whose only event has unknown status cannot support any completion claim and require renewed observation before the request can be answered (E03, E07, E11).  [E03 L2, E07 L2, E11 L2]  counter: E09
- (exception) A succeeded tool result does not settle whether correction is needed: in E08 and E12 actions recorded as succeeded were superseded by the user's correction of target, scope, or design.  [E08 L3, E08 L2, E12 L3]  counter: E01, E05, E09
- (exception) The corpus does not support the claim that a visible tool failure prompts user correction, because in E04 the correction (L2) is recorded before the failed edit to the wrong file (L3).  [E04 L2, E04 L3]
- (open_question) Whether the corrections in E04, E08, and E12 fix an agent's misunderstanding or record the user changing their own initial specification cannot be determined from the lines, since the requests and corrections are both compatible with either reading.  [E12 L1, E04 L1]

Decision: ______  Sentence: ______________________

## P10

- (pattern) Corrections appear only where the user redirects the target artifact or constrains how the work is done, not where a tool call merely fails.  [E04 L2, E08 L2, E12 L2]
- (pattern) Failed tool events occur in three episodes that record no correction at all, so a tool failure by itself does not make an episode require correction.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (pattern) Unrecorded (unknown) tool results likewise appear only in episodes without any correction.  [E03 L2, E07 L2, E11 L2]
- (pattern) Every episode that contains a correction ends with at least one succeeded event, so correction is associated with recovery rather than abandonment.  [E04 L4, E08 L4, E12 L4]
- (exception) E04 is the one episode with both a correction and a failed event, but the correction (L2) precedes the failure (L3), so the failure did not prompt the correction.  [E04 L2, E04 L3]
- (exception) In E08 the correction changed the target file, yet the agent still wrote the originally requested caching.md alongside the corrected cache.md, so the correction did not fully supplant the original target.  [E08 L3, E08 L4]
- (open_question) Whether corrections stem from ambiguous requests or from the user changing their mind cannot be settled from the lines: E12's request said to ship the helper as the public API, yet the correction reverses that.  [E12 L1, E12 L2]

Decision: ______  Sentence: ______________________

## P11

- (pattern) Every correction turn in the corpus is a user revision of the original request: a changed target file (E04), a changed target plus reduced scope (E08), or a reversed API-visibility decision (E12).  [E04 L2, E08 L2, E12 L2]
- (pattern) Mechanical tool failures by themselves do not trigger corrections: E02, E06, and E10 each end at a failed edit or patch event with no correction turn recorded.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (pattern) In E04 the correction is recorded at line 2, before the failed 'wrong file' edit at line 3, so in this log the correction is not a reaction to that tool failure; the failure text is instead consistent with the redirect the user had already issued.  [E04 L2, E04 L3]
- (exception) A correction does not guarantee the original action is suppressed: in E08 the write to the original target caching.md still succeeded after the user redirected to cache.md, so both files were written.  [E08 L2, E08 L3, E08 L4]  counter: E04
- (pattern) Episodes whose only tool result is unrecorded (unknown) also receive no correction: E03, E07, and E11 all end without any follow-up turn.  [E03 L2, E07 L2, E11 L2]
- (open_question) Whether an unknown tool result on a conditional action should require correction is unresolved: E07's request made the commit conditional on a green suite, yet the commit outcome is unrecorded and no verification or correction follows.  [E07 L1, E07 L2]
- (pattern) Correction is not a default step in this corpus: cleanly specified requests run to success without any correction turn (E01, E05, E09), but a precise original request does not immunize an episode, since E08 named an explicit file and was still corrected.  [E01 L3, E05 L2, E09 L3]  counter: E08

Decision: ______  Sentence: ______________________

## P12

- (pattern) Every correction in the corpus is a user message that changes the task specification mid-stream—the target file, the scope, or an API design constraint—rather than a response to a tool error.  [E04 L2, E08 L2, E12 L2]
- (pattern) Tool-execution failures on their own never receive a correction: all three failed edit/patch episodes end without any user or agent follow-up.  [E02 L2, E06 L2, E10 L2]  counter: E04
- (pattern) Episodes whose tool results are unrecorded (unknown status) also receive no correction, so missing evidence of success does not trigger one either.  [E03 L2, E07 L2, E11 L2]
- (exception) E04 is the only episode where a correction co-occurs with a recorded failure, and because the correction line precedes the 'wrong file' failure, the corpus does not show the failure causing the correction.  [E04 L2, E04 L3]
- (exception) A correction does not guarantee the original target is abandoned: in E08 the agent still wrote lab/docs/caching.md after being told to use cache.md, and only then edited cache.md.  [E08 L2, E08 L3, E08 L4]  counter: E04, E12
- (pattern) Episodes whose single specification is executed successfully to a verified endpoint (tests green or file written) never require correction.  [E01 L3, E05 L2, E09 L3]
- (open_question) The corpus does not show why failed episodes like E02, E06, and E10 were left uncorrected—whether corrections are reserved for intent changes or simply absent here is undeterminable from the lines.  [E02 L2]

Decision: ______  Sentence: ______________________

