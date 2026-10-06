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


## Integration Slice 4: involuntary-expression boundary

Status: **GREEN**

Integration head: `f61e5a0bc65b6cc7651fba2b666214c6f40edd1b`

Regression workflow: `37426924967`

Bride qualification workflow: `37426924976`

Evidence:
- 9/9 regression jobs passed across Linux, Windows, and macOS on Python 3.11, 3.12, and 3.13.
- 6/6 Bride qualification jobs passed across Linux, Windows, and macOS on Python 3.11 and 3.13.
- The integrated suite now executes 144 deterministic tests plus the 15-probe Frankenstein acceptance harness.
- Neutral pain/surprise state emits no reflex.
- High pain produces a qualitative non-intentional pain-vocalization emission.
- Held-out extreme surprise produces a qualitative non-intentional startle emission.
- Raw numeric pain and surprise values are not exposed in the emission object.
- Reflex evaluation appends no canonical or noncanonical event.
- Reflex evaluation does not create subject actions, memories, beliefs, commitments, goals, or concerns.
- Reflex evaluation does not change deliberate `DecisionReceipt` selection.
- Simultaneous extreme triggers resolve deterministically without creating a second policy selector.

Verdict: **ACCEPT AS v0.2 CANDIDATE DEFAULT**

## Qualified-core integration freeze

Status: **COMPLETE**

The v0.2 candidate core now contains exactly four behaviorally qualified additions over Frankenstein v0.1:
1. bounded replayable planning,
2. narrow confidentiality commitment pressure,
3. bounded private-cognition concern pressure,
4. a separate involuntary-expression channel.

TinyPersona perception remains an external adapter rather than core world authority. Donors held, rejected, blocked, or infrastructure-only in the Bride promotion ledger remain outside the production core.

The next phase is integrated longitudinal qualification, not additional donor accumulation.


## Integrated Longitudinal Gate 1

Status: **GREEN**

Candidate evidence SHA: `d481153628cad95ca4348e5f6a799b0472c808cb`

Regression workflow: `37427624732`

Bride qualification workflow: `37427624706`

Frozen evidence: `evidence/INTEGRATED_LONGITUDINAL_SNAPSHOT_d481153.md`

Evidence:
- 9/9 regression jobs passed.
- 6/6 qualification jobs passed.
- Six machine-readable longitudinal artifacts decode to identical JSON.
- Normalized full-result SHA-256: `d2541d20fcb2d4460d2372986e4f41441f0b07dc84a73315aa9ff5a96fc7758f`.
- Nine integrated trials passed everywhere: planning persistence, confidentiality policy, private-cognition policy, involuntary expression, combined pressure competition, renderer-swap semantic invariance, diagnostic-fork isolation, remember-versus-intrude memory behavior, and developmental path divergence.

Verdict: **ADVANCE TO LONGER STRESS QUALIFICATION**

This gate is stronger than isolated feature tests because the qualified mechanisms coexist in the same candidate and compete through the same action authority. It is still deterministic and bounded. Live-model renderer invariance and much longer histories remain separate gates.


## Repeated-Interaction Stress Gate

Status: **GREEN**

Candidate evidence SHA: `e66d7e9ffe9312f82a0d5a95b0ce7b0506f6c551`

Regression workflow: `37428534048`

Bride qualification workflow: `37428534259`

Frozen evidence: `evidence/REPEATED_INTERACTION_STRESS_SNAPSHOT_e66d7e9.md`

Evidence:
- 9/9 regression jobs passed.
- 6/6 qualification jobs passed.
- Six stress artifacts normalize to identical JSON.
- Normalized full stress-result SHA-256: `54534a007a118178ca7262c7c31ffae3c570856bf488456a2d3c0a984afa1271`.
- Normalized stress trial-payload SHA-256: `65831d7d9b6bb4b381c81da24558eb5c86de42d631d75b8206ad9e20d3eef967`.
- Eight repeated-interaction trials passed everywhere: long-history replay/restart, multi-restart plans, commitment retention, private-thought loop suppression, renderer long-run drift, diagnostic-fork isolation, 130-memory cue specificity, and developmental long-run divergence.

Verdict: **ADVANCE TO RELEASE HARDENING**

The next graph phase is compatibility and release acceptance, not additional donor accumulation.


## Release Hardening Gate

Status: **GREEN**

Candidate hardening head: `31f727afe6918e05b1deb508d09fd99cb042e36d`

Regression workflow: `37516915821`

Bride qualification workflow: `37516915930`

Evidence:
- 9/9 regression jobs passed across Linux, Windows, and macOS on Python 3.11, 3.12, and 3.13.
- 6/6 Bride qualification jobs passed across Linux, Windows, and macOS on Python 3.11 and 3.13.
- v0.1-shaped homes open under v0.2 with schema version 1 and unchanged semantic state.
- v0.1-shaped backups restore under the v0.2 runtime.
- legacy v0.1-style backup manifests without the new semantic digest remain accepted.
- v0.2 backups record and verify a portable semantic projection digest independent of SQLite row insertion order.
- the legacy `projection_digest()` contract remains unchanged for backward compatibility.
- qualified plan and private-cognition state survive backup/restore.
- involuntary expression remains transient across backup/restore.

Verdict: **ADVANCE TO v0.2.0rc1**


## v0.2.0rc1 Release-Branch Acceptance

Status: **GREEN**

Release head: `9ad66a5943518cece4ebb27e207871fce8e4fbfa`

Regression workflow: `37518089330`

Bride qualification workflow: `37518089557`

Evidence:
- 9/9 release-branch regression jobs passed.
- 6/6 release-branch Bride qualification jobs passed.
- RC package and runtime versions agree at `0.2.0rc1`.
- integrated longitudinal, repeated-interaction stress, v0.1 compatibility, legacy restore, and semantic backup verification all execute on the release branch.

Verdict: **ACCEPT RC1 FOR MERGE TO MAIN**
