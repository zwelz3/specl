# specl Explorer specification review: disposition record

Three rounds, 80 verdicts, 7 changes. This records what each round decided and what remains open, so the reasoning survives the review artifacts.

## State of the specification

| | Before review | After round 3b |
| --- | --- | --- |
| Parser warnings | 0 | 0 |
| SHACL violations | 0 | 0 |
| SHACL warnings | 69 | 9 |
| Maturity | 8% | 94% |
| Requirements clean | 0 of 47 | 74 of 74 |
| User stories clean | 0 of 5 | 5 of 5 |
| Personas | none declared | 5 of 5 |
| Decisions | none recorded | 7 of 7 |

The nine remaining warnings are all one thing: nine open questions with no `specl:owner`. Owners are an accountability decision and were not drafted.

## Round 1: personas, requirements, decisions, dispositions

124 items presented, 33 in the needs-review set, 33 answered. All keep. Four comments, three of which changed something.

**R3.3 (keep, with a question).** Asked whether the wording should allow future tab expansion. The recommendation given was to restate the invariant rather than the count, since the defect was a specification-scoped tab sitting beside item-scoped ones and the number two was never what fixed it. Not applied, because a question is not a change request. The acceptance criterion was written to test the invariant, so it holds under either wording and will not need revisiting when the question is answered.

**OQ7 and OQ8 (keep, hold open).** The attesting reader persona (P5) stays pending an implementation that would show whether it collapses into the reviewer. The authoring boundary stays open above D7 and R13.5, which are settled.

**PR2 (keep, with direction).** The embedded example is this specification's own emitted graph. Carried into R9.4, with a second criterion added: the build compares the embedded copy against the current graph and fails on divergence, because an embedded self-reference goes stale silently and this one goes stale on every specification change.

A consequence worth stating. With the explorer's own specification as the default load, the first thing a new reader sees is that specification's maturity figure. Keeping it current stopped being housekeeping.

## Round 2: acceptance criteria

78 criteria presented, 43 in the needs-review set, 43 answered. 41 keep, 2 change.

**R1.3 (change).** The requirement made the Python distribution the only route to the explorer, which is the inversion PR1 identifies: seeing the tool required installing the thing the tool exists to demonstrate. Restated as obtainability without a build or an installation from at least one published channel, with every channel serving an identical file for a release. The distribution is now one option rather than the obligation.

That surfaced a property the old wording had been meeting by accident. A command that composes the explorer with a graph needs a local copy in an air-gapped deployment, and a hosted artifact does not supply one. **R1.6** was minted to hold that explicitly, worded conditionally so it costs nothing if the compose command does not land.

**R4.5 (change).** Identifier, label and description. The requirement text had been the weaker half, naming only identifier and description while the criterion asserted three. Both now agree.

**R2.2 (keep, with a comment).** The observation that the parser will likely also back a language server or highlighter contradicts the design note calling a thirty-line parser sufficient. Recorded as **OQ9** rather than acted on.

## Round 3 and 3b: the material the filter had skipped

Round 3 presented 35 items and returned 4, because the 31 items the round existed for were not marked as needing review and the filter hid them. Rebuilt as round 3b with the flag corrected. 31 of 31 answered, 30 keep, 1 change.

**OQ9 (keep, agreed).** The recommendation stands: hold R2.2 and R7.4 as written for this artifact and treat a reusable parser as a specl-level component if one is wanted. Status stays open, since agreeing with a disposition does not answer the question it defers. A consumer beyond the explorer is the trigger to raise it.

**R5.8 (change).** "Open and/or report." The criterion prescribed filtering the item list, which is a mechanism, and DN6 says a criterion states what must be obtainable rather than what must be on screen. Restated as obtainability by either route. Two references in R8.1 and R8.3 were reworded to match.

**skos:altLabel on R4.5, answered outside the artifact.** The filter matches any SKOS label the item carries. One clause was added beyond the instruction: where an item matches on text its row does not display, the matching text is shown with it. Matching labels the reader cannot see produces a result set they cannot account for, which is the condition D3 excludes. This clause is the one piece of the round not derived from a verdict and is the first thing to strike if it is unwanted.

## What the review did not cover

Forty-six items of the current specification were carried unchanged and never had a verdict: the original requirements left untouched by the plan, and DN1 through DN5. They were in scope in round 1 and outside its needs filter throughout. Nothing in the review contradicts them; they simply were not read.

Nine open questions have no owner. Six are open (OQ1, OQ3, OQ5, OQ7, OQ8, OQ9) and three carry applied dispositions.

## An observation on the verdict distribution

Of 80 verdicts, 73 were keep and 7 were change. That is either a sound proposal or a review that was aimed at the items already reasoned hardest about. Round 3b is the better evidence on that question, since it covered the material written quickly rather than argued over, and it returned one change in 31. The distribution held.

Two of the seven changes were the substantive ones. R1.3 and R5.8 both corrected the same class of error: a requirement stating a mechanism where it should have stated a property. Both were mine, and both had passed a drafting pass that was supposed to catch exactly that.
