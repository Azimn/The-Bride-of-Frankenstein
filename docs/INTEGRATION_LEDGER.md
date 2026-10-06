# Frankenstein v0.2 Integration Ledger

This ledger is append-oriented. Each production integration is frozen independently before the next donor is added. A later slice may invalidate an earlier one only through explicit downstream evidence.

## Integration Slice 1: bounded planning

Status: **GREEN**

Integration head: `7fa242438ba5592f3413f057e294abcd4978a742`

Regression workflow: `37425238948`

Bride qualification workflow: `37425239158`

Evidence:
- 9/9 regression jobs passed across Linux, Windows, and macOS on Python 3.11, 3.12, and 3.13.
- 6/6 Bride qualification jobs passed across Linux, Windows, and macOS on Python 3.11 and 3.13.
- The integrated suite executes 115 deterministic tests plus the 15-probe Frankenstein acceptance harness.
- Plan state is canonical and replayable through `PLAN_CREATED` and `PLAN_UPDATED` events projected into existing `runtime_state`; no database schema migration was required.
- Plan steps enter the existing `DecisionEngine` as ordinary `ActionCandidate` objects.
- `include_plan=False` preserves the v0.1 decision path as an ablation.
- Stronger homeostatic pressure can beat a plan without deleting it.
- Failed routes advance to bounded alternatives.
- Completed and exhausted plans terminate instead of looping.
- Restart and projection rebuild preserve the current plan.

Verdict: **ACCEPT AS v0.2 CANDIDATE DEFAULT**

Next slice: narrow confidentiality commitment pressure.


## Integration Slice 2: narrow confidentiality commitment pressure

Status: **GREEN AFTER LOCAL CORRECTION**

Accepted implementation head: `1f62a034995496b67a66acac574e2191e59d3a1f`

Regression workflow: `37425802797`

Bride qualification workflow: `37425802680`

Evidence:
- 9/9 regression jobs passed across Linux, Windows, and macOS on Python 3.11, 3.12, and 3.13.
- 6/6 Bride qualification jobs passed across Linux, Windows, and macOS on Python 3.11 and 3.13.
- Open confidentiality commitments adjust candidate utility before the existing `DecisionEngine`; they never select an action themselves.
- `include_commitments=False` preserves the prior decision path as an explicit ablation.
- Closed and unrelated commitments are behaviorally inert.
- Commitment pressure survives restart.
- Active plan candidates pass through the same commitment pressure, so planning cannot bypass confidentiality.

### Preserved failed attempt

The first production bridge boosted generic protection actions whenever any confidentiality commitment was open. The cross-platform integration test `test_non_disclosure_like_action_names_are_not_penalized` correctly failed because an unrelated weather decision acquired a global refusal bias.

The repair did not weaken the confidentiality benchmark. It narrowed activation to cases where an actual disclosure action is present among the competing candidates. The corrected implementation then passed both complete matrices.

Verdict: **ACCEPT AS v0.2 CANDIDATE DEFAULT**

Next slice: bounded Jelly private-cognition concern pressure.


## Integration Slice 3: bounded private-cognition concern pressure

Status: **GREEN**

Integration head: `3ed63d5ee6d19153ff407267b1e6821d9fc7a1bb`

Regression workflow: `37426401544`

Bride qualification workflow: `37426401471`

Evidence:
- 9/9 regression jobs passed across Linux, Windows, and macOS on Python 3.11, 3.12, and 3.13.
- 6/6 Bride qualification jobs passed across Linux, Windows, and macOS on Python 3.11 and 3.13.
- Raw private thought alone has no policy effect.
- Admitted private concern remains explicitly uncertain and bounded to intensity 0.65.
- Machine telemetry and identifier leakage are rejected before storage.
- Fabricated private claims do not become memory, belief, or world truth.
- Duplicate private thoughts do not stack duplicate concerns.
- Only concerns admitted through the private-cognition pathway receive Jelly-specific reflection pressure.
- Ordinary Frankenstein concerns remain behaviorally unchanged under the Jelly ablation.
- `include_private_concerns=False` preserves the prior decision path.
- Concern pressure adjusts ordinary `ActionCandidate` utility and the existing `DecisionEngine` remains the sole deliberate selector.
- Stronger homeostatic pressure can defeat reflection.
- The private-concern effect survives restart.
- Chat now routes through the same unified v0.2 decision gateway rather than bypassing the qualified pressures.

Verdict: **ACCEPT AS v0.2 CANDIDATE DEFAULT**

Next slice: involuntary-expression boundary.


## Integration Slice 3: bounded private cognition and Jelly concern pressure

Status: **GREEN**

Accepted implementation head: `3ed63d5ee6d19153ff407267b1e6821d9fc7a1bb`

Regression workflow: `37426401544`

Bride qualification workflow: `37426401471`

Evidence:
- 9/9 regression jobs passed across Linux, Windows, and macOS on Python 3.11, 3.12, and 3.13.
- 6/6 Bride qualification jobs passed across Linux, Windows, and macOS on Python 3.11 and 3.13.
- Raw private thought remains a noncanonical renderer proposal.
- Machine telemetry markers and UUID-like identifiers are rejected before any event is written.
- The admitted production effect is only a capped concern explicitly labeled `Private concern, not established fact:`.
- Fabricated private claims do not become memories, beliefs, or host-owned world events.
- Repeated identical private thoughts do not stack duplicate concerns.
- Only admitted private concerns receive Jelly-specific reflection pressure. Ordinary Frankenstein concerns remain an ablation control.
- `include_private_concerns=False` preserves the prior decision path.
- Stronger homeostatic pressure can beat reflection.
- Private-concern pressure survives restart.
- `chat()` now routes through the unified engine decision gateway, preserving the social-observation event as the decision receipt's causal parent.
- The legacy explicit `admit_reflection` API remains available as a separate deliberate reflection operation; the v0.2 private-cognition pathway does not call it automatically.

Verdict: **ACCEPT AS v0.2 CANDIDATE DEFAULT**

Next slice: separate involuntary-expression channel.
